"""relatorio_cobertura.py: etapa 7a de qualquer app. Cruza o inventario com todos os logs.

Le (em 90-relatorios): menus_<ctx>.json, telas_<ctx>.json, dentro_<ctx>.json e quaisquer logs extras
passados em --extra (ex.: paineis_dentro.json do alvos_visao, com campo "painel").
Para cada item de menu do inventario: em que print de menu ele aparece, print do submenu/tela,
quantos prints por dentro, situacao e motivo. Itens do inventario que nao sao de menu (dialog, docker,
toolbar... vindos do adaptador) vao para cobertura_definicoes_internas.csv, com a indicacao de quando o
mesmo nome foi fotografado por outro caminho.

Situacoes: ok | ok (sem janela) | ok (aparece no print do menu) | nao aberto de proposito | desativado |
           oculto | sem print do submenu | sem print da tela | fora do escopo
Saida: cobertura_final.csv (;  UTF-8 com BOM, abre no Excel), cobertura_definicoes_internas.csv,
       resumo_final.json. Depois: gera_indice.py.
Uso: python relatorio_cobertura.py [--extra paineis_dentro] [--config app.json]
"""
import argparse
import csv
import json
from collections import Counter

import lista_negra as ln
import projeto


def ler(P, nome):
    f = P.R / nome
    d = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    if isinstance(d, dict):  # log em outro formato (ex.: {"estados": [...]}): usa a 1a lista de registros
        d = next((v for v in d.values() if isinstance(v, list) and v and isinstance(v[0], dict)), [])
    return [r for r in d if isinstance(r, dict) and "path" in r or isinstance(r, dict) and "tela" in r]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--config")
    a = ap.parse_args()
    P = projeto.carregar(a.config, precisa_app=False)
    inv = projeto.inventario(P)
    menu_inv = [x for x in inv if x["kind"] in ("menu_root", "menu_item")]
    outros = [x for x in inv if x["kind"] not in ("menu_root", "menu_item")]
    ctxs = (P.cfg.get("contextos") or ["doc-vazio"]) + sorted(
        f.stem[6:] for f in P.R.glob("menus_*.json") if f.stem[6:] not in P.cfg.get("contextos", []) + ["contexto"])

    menus, falha_menu = {}, {}
    for c in ctxs:
        for r in ler(P, f"menus_{c}.json"):
            if r["status"] == "ok":
                menus.setdefault(r["path"], (c, r["image"]))
            else:
                falha_menu.setdefault(r["path"], (r["status"], r.get("note", "")))
    # o mesmo item pode aparecer em varios contextos: fica o melhor resultado
    ordem = {"ok": 0, "docker": 1, "painel": 1, "sem_janela": 2, "nao_aberto": 3, "nao_abriu": 4,
             "desativado": 4, "erro": 5}
    telas = {}
    for c in ctxs:
        for r in ler(P, f"telas_{c}.json"):
            atual = telas.get(r["path"])
            if not atual or ordem.get(r["status"], 9) < ordem.get(atual["status"], 9):
                telas[r["path"]] = dict(r, contexto=r.get("contexto") or c)
    dentro = Counter()
    for c in ctxs:
        for r in ler(P, f"dentro_{c}.json"):
            dentro[r["tela"]] += 1
    fora = set(P.cfg.get("menus_fora", [])) | ln.MENUS_FORA

    rows = []
    for x in menu_inv:
        p = x["path"]
        raiz = p.split(" > ")[0]
        pai = " > ".join(p.split(" > ")[:-1]) or p
        no_menu = menus.get(pai if x["kind"] == "menu_item" else p)
        row = {"caminho": p, "tipo": "", "menu_print": no_menu[1] if no_menu else "", "contexto": "",
               "imagem": "", "prints_dentro": "", "situacao": "", "motivo": ""}
        if raiz in fora:
            row.update(tipo="fora do escopo", situacao="fora do escopo", motivo=f"menu {raiz} (decisao do usuario)")
        elif x["kind"] == "menu_root" or x["has_submenu"]:
            row["tipo"] = "menu" if x["kind"] == "menu_root" else "submenu"
            if p in menus:
                row.update(situacao="ok", contexto=menus[p][0], imagem=menus[p][1])
            else:
                st, note = falha_menu.get(p, ("", "nao apareceu em nenhum contexto"))
                row.update(situacao="desativado" if st == "sem_submenu" else "sem print do submenu",
                           motivo=f"{st}: {note}".strip(": "))
        elif p in telas:
            t = telas[p]
            row.update(tipo="abre tela", contexto=t.get("contexto", ""), imagem=t.get("image", ""),
                       prints_dentro=dentro.get(p, 0) or "")
            st = t["status"]
            if st == "ok":
                row["situacao"] = "ok"
            elif st in ("docker", "painel"):  # o comando abre um painel em vez de janela
                row.update(situacao="ok (abre no painel)", motivo=t.get("note", ""))
            elif st == "sem_janela":
                row.update(situacao="ok (sem janela)" if row["imagem"] else "sem janela", motivo=t.get("note", ""))
            elif st == "nao_aberto":
                row.update(situacao="nao aberto de proposito", motivo=t.get("note", ""))
            elif st == "desativado" or (st == "nao_abriu" and "desativado" in t.get("note", "")):
                row.update(situacao="desativado", motivo=t.get("note", ""))
            elif "oculto" in t.get("note", ""):
                row.update(situacao="oculto", motivo=t.get("note", ""))
            else:
                row.update(situacao="sem print da tela", motivo=t.get("note", "") or st)
        else:
            row["tipo"] = "comando"
            row["situacao"] = "ok (aparece no print do menu)" if no_menu else "sem print"
            if not no_menu:
                st, note = falha_menu.get(pai, ("", ""))
                row["motivo"] = f"menu pai sem print ({st or 'nao fotografado'}{': ' + note if note else ''})"
        rows.append(row)
    with open(P.R / "cobertura_final.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
        wr.writeheader()
        wr.writerows(rows)

    # definicoes fora dos menus: procura o mesmo nome no que foi fotografado
    titulos = {(t.get("window_title") or "").lower() for t in telas.values()}
    extras = {}
    for nome in a.extra:
        for r in ler(P, f"{nome}.json"):
            extras[(r.get("painel") or r.get("path") or "").split(" > ")[-1].lower()] = nome
    caps = {projeto.norm(x["caption"]) for x in menu_inv}
    xrows = []
    for x in outros:
        c = (x.get("caption") or x["path"]).lower()
        onde = ("tela com o mesmo titulo fotografada" if c in titulos else
                f"fotografado em {extras[c]}" if c in extras else
                "item de menu com o mesmo nome no mapeamento" if projeto.norm(c) in caps else "")
        xrows.append({"tipo": x["kind"], "nome": x.get("caption") or x["path"], "id": x.get("id", ""),
                      "fotografado_por_outro_caminho": onde,
                      "observacao": "" if onde else "definicao sem menu proprio; nao aberta diretamente"})
    with open(P.R / "cobertura_definicoes_internas.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=["tipo", "nome", "id", "fotografado_por_outro_caminho", "observacao"],
                            delimiter=";")
        wr.writeheader()
        wr.writerows(xrows)

    pastas = {}
    for d in sorted(P.ROOT.glob("0[2-9]-*")):
        allp = list(d.rglob("*.png"))
        pastas[d.name] = {"prints": len([p for p in allp if "tela-inteira" not in p.parts]),
                          "tela_inteira": len([p for p in allp if "tela-inteira" in p.parts])}
    resumo = {"itens_de_menu": len(rows), "situacao": Counter(r["situacao"] for r in rows).most_common(),
              "tipo": Counter(r["tipo"] for r in rows).most_common(), "definicoes_internas": len(xrows),
              "definicoes_por_tipo": Counter(r["tipo"] for r in xrows).most_common(),
              "definicoes_achadas": sum(1 for r in xrows if r["fotografado_por_outro_caminho"]), "pastas": pastas}
    (P.R / "resumo_final.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    for r in rows:
        if not r["situacao"].startswith("ok") and r["situacao"] != "fora do escopo":
            print(f"  {r['situacao']:28} {r['caminho']}  | {r['motivo'][:90]}")


if __name__ == "__main__":
    main()
