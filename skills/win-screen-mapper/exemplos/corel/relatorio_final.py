"""Etapa 7a: relatorio de cobertura final (cruza o inventario com todos os logs).

Para cada item do inventario lido do Corel (menus da barra e seus itens):
  - em que print de menu ele aparece (o menu pai aberto);
  - se tem submenu: o print do submenu (em algum contexto);
  - se abre uma tela: o print da tela (doc vazio ou o 1o contexto que a ativou) e quantos prints por dentro;
  - situacao final e motivo quando nao ha print.
Os itens que so existem no DrawUI.xml (definicoes internas: dialogos, dockers, barras, menus) vao
para outro CSV, com a indicacao de quando o mesmo nome foi fotografado por outro caminho.

Saida: 90-relatorios/cobertura_final.csv, cobertura_definicoes_internas.csv, resumo_final.json
"""
import csv
import glob
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
R = ROOT / "90-relatorios"


def load(name):
    return json.loads((R / name).read_text(encoding="utf-8"))


inv = load("../01-inventario/inventory.json")
live = [x for x in inv if x.get("source") == "live" and x["kind"] in ("menu_root", "menu_item")]
xml = [x for x in inv if x.get("source") == "xml"]

# menus fotografados (por caminho), doc-vazio primeiro
menus = {}
ctxs = ["doc-vazio"] + sorted(Path(f).stem[6:] for f in glob.glob(str(R / "menus_*.json"))
                              if Path(f).stem[6:] not in ("doc-vazio", "contexto", "contextos"))
for c in ctxs:
    for r in load(f"menus_{c}.json"):
        if r["status"] == "ok" and r["path"] not in menus:
            menus[r["path"]] = (c, r["image"])
menu_fail = {}
for c in ctxs:
    for r in load(f"menus_{c}.json"):
        if r["status"] != "ok":
            menu_fail.setdefault(r["path"], (r["status"], r.get("note", "")))

# telas
telas_dv = {r["path"]: r for r in load("telas_doc-vazio.json")}
telas_cx = {r["path"]: r for r in load("telas_contextos.json")}
dentro = Counter()
for f in ("dentro_doc-vazio.json", "dentro_contextos.json"):
    for e in load(f)["estados"]:
        dentro[e["tela"]] += 1

# motivos do relatorio de menus da etapa 2 (ex.: "oculto")
with open(R / "cobertura_menus_doc-vazio.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["status"] not in ("ok",):
            menu_fail.setdefault(r["caminho"], (r["status"], r["motivo"]))

FORA = {"Purchase", "Debug", "<67cfe9c0>"}
rows = []
for x in live:
    p = x["path"]
    root = p.split(" > ")[0]
    parent = " > ".join(p.split(" > ")[:-1]) or p
    no_menu = menus.get(parent if x["kind"] == "menu_item" else p)
    row = {"caminho": p, "tipo": "", "menu_print": no_menu[1] if no_menu else "",
           "contexto": "", "imagem": "", "prints_dentro": "", "situacao": "", "motivo": ""}
    if root in FORA:
        row.update(tipo="fora do escopo", situacao="fora do escopo",
                   motivo="menu Purchase (pedido do usuario)" if root == "Purchase"
                   else "menu Debug oculto (so aparece com depuracao interna ligada)")
    elif x["kind"] == "menu_root" or x["has_submenu"]:
        row["tipo"] = "menu" if x["kind"] == "menu_root" else "submenu"
        if p in menus:
            row.update(situacao="ok", contexto=menus[p][0], imagem=menus[p][1])
        else:
            st, note = menu_fail.get(p, ("sem print", "nao apareceu em nenhum contexto"))
            row.update(situacao="oculto" if st == "oculto" else "sem print do submenu",
                       motivo=f"{st}: {note}".strip(": "))
    elif p in telas_dv:
        row["tipo"] = "abre tela"
        t = telas_dv[p]
        if t["status"] != "ok" and p in telas_cx:
            t = telas_cx[p]
        st = t["status"]
        row.update(contexto=t.get("contexto") or "doc-vazio", imagem=t.get("image", ""),
                   prints_dentro=dentro.get(p, 0) or "")
        if st == "ok":
            row["situacao"] = "ok"
        elif st == "docker":
            row.update(situacao="ok (abre no docker)", motivo=t.get("note", ""))
        elif st == "sem_janela":
            row.update(situacao="ok (sem janela)" if row["imagem"] else "sem janela",
                       motivo=t.get("note", "") or "o comando nao abre janela")
        elif st == "nao_aberto":
            note = t.get("note", "")
            if p.startswith("Help >") and note.startswith("pendente"):
                note = "decisao do usuario: no Help so os menus (o item abre o navegador)"
            row.update(situacao="nao aberto de proposito", motivo=note)
        else:
            row.update(situacao="sem print da tela", motivo=t.get("note", "") or st)
    else:
        row["tipo"] = "comando"
        row["situacao"] = "ok (aparece no print do menu)" if no_menu else "sem print"
        if not no_menu and menu_fail.get(parent, ("",))[0] == "oculto":
            row["situacao"] = "oculto"
        if not no_menu:
            row["motivo"] = "menu pai nao fotografado"
    if x["kind"] == "menu_item" and not no_menu and row["situacao"] not in ("fora do escopo",):
        st, note = menu_fail.get(parent, ("", ""))
        row["motivo"] = (row["motivo"] + "; " if row["motivo"] else "") + \
            f"menu pai sem print ({st or 'oculto'}{': ' + note if note else ''})"
    rows.append(row)

with open(R / "cobertura_final.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";")
    w.writeheader()
    w.writerows(rows)

# definicoes internas (DrawUI.xml): procura o mesmo nome entre o que foi fotografado
titulos = {(r.get("window_title") or "").lower() for r in list(telas_dv.values()) + list(telas_cx.values())}
dock_names = {r["docker"].split(" > ")[-1].lower() for r in load("dockers_retangulo.json")}
barras = {r["barra"].lower() for r in load("barras.json")}
caps = {x["caption"].lower().rstrip(".") for x in live}
xrows = []
for x in xml:
    c = x["caption"].lower()
    onde = ""
    if x["kind"] == "docker" and c in dock_names:
        onde = "docker fotografado (04-dockers)"
    elif x["kind"] == "toolbar" and (c in barras or c in ("property bar", "toolbox", "menu bar")):
        onde = "barra fotografada (05-ferramentas / 06-barras / 02-menus)"
    elif c and c in titulos:
        onde = "tela com o mesmo titulo fotografada (03-telas)"
    elif c and c in caps:
        onde = "item de menu com o mesmo nome no mapeamento"
    xrows.append({"tipo": x["kind"], "nome": x["caption"], "guid": x["guid"],
                  "fotografado_por_outro_caminho": onde,
                  "observacao": "" if onde else "definicao interna sem menu proprio; nao e aberta diretamente"})
with open(R / "cobertura_definicoes_internas.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(xrows[0]), delimiter=";")
    w.writeheader()
    w.writerows(xrows)

# totais por pasta
pastas = {}
for d in sorted(ROOT.glob("0[2-7]-*")):
    allp = list(d.rglob("*.png"))
    pastas[d.name] = {"prints": len([p for p in allp if "tela-inteira" not in p.parts]),
                      "tela_inteira": len([p for p in allp if "tela-inteira" in p.parts])}
resumo = {
    "itens_de_menu": len(rows),
    "situacao": Counter(r["situacao"] for r in rows).most_common(),
    "tipo": Counter(r["tipo"] for r in rows).most_common(),
    "definicoes_internas": len(xrows),
    "definicoes_por_tipo": Counter(r["tipo"] for r in xrows).most_common(),
    "definicoes_achadas": sum(1 for r in xrows if r["fotografado_por_outro_caminho"]),
    "pastas": pastas,
}
(R / "resumo_final.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(resumo, ensure_ascii=False, indent=1))
for r in rows:
    if not r["situacao"].startswith("ok") and r["situacao"] != "fora do escopo":
        print(f"  {r['situacao']:28} {r['caminho']}  | {r['motivo'][:90]}")
