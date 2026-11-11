"""alvos_visao.py: motor do "passe por visao" (cliques por coordenada onde a UI Automation nao enxerga).

Serve para qualquer app: paineis, abas, listas e menus desenhados pelo proprio app, barras,
telas sem UIA. O que e especifico do app (abrir/fechar o painel ou a janela de cada alvo) fica num
ADAPTADOR (copie adaptador_modelo.py), indicado no app.json ("adaptador") ou com --adaptador.
Origem: crawl_dockers_dentro.py do mapeamento do CorelDRAW (223 alvos, 239 prints).

Alvos (JSON, lista). x, y relativos ao canto superior esquerdo do retangulo que adaptador.abrir() devolve:
  {"painel": "Transform", "nome": "aba Rotate", "tipo": "aba", "x": 45, "y": 40,
   "antes": [{"x": 10, "y": 40}, {"rolar": 2}, {"x": 90, "y": 60, "manter": true}],
   "voltar": [{"x": 10, "y": 40}], "rolar": 0, "submenus": true, "reiniciar_depois": false,
   "desfazer": false}

  tipo aba      -> clica, fotografa o painel (com partes de rolagem) e deixa como esta
       expandir -> clica, fotografa (com rolagem), clica de novo para recolher
       lista    -> clica, fotografa painel + lista aberta, fecha (Esc em menus/listas; janela pelo X)
       menu     -> igual a lista; com "submenus" (padrao) passa o mouse em cada linha e fotografa
                   os submenus (linhas achadas pela imagem: winui.linhas_do_popup)
  antes  -> cliques que preparam o estado. Sem "manter", qualquer popup aberto e fechado depois do
            clique; com "manter": true a lista fica aberta para o alvo escolher um item dela.
  voltar -> cliques que devolvem a opcao padrao (OBRIGATORIO quando o alvo troca uma opcao).
  reiniciar_depois -> reinicio preventivo (alvo que deixa o app instavel).
  desfazer -> numa lista que "abriu dentro do painel", clica de novo no alvo para desfazer.

So clique o que foi escolhido a dedo olhando os prints (folhas_regua.py). NUNCA marque alvos em
OK/Apply/Delete/Reset/Save/Export/Create/Generate/I agree/conta/compra/links.

Uso:
  python alvos_visao.py --alvos alvos.json --pasta "04-paineis/dentro" --log paineis_dentro
      [--adaptador adaptador_meuapp] [--only Transform Fill] [--skip Objects] [--max-rolagem 8]
  --pasta e relativa ao MAPEAMENTO do app.json; o log vai para 90-relatorios/<log>.json.
"""
import argparse
import importlib
import json
import time
import traceback
from pathlib import Path

import projeto
import winui as w

AD = None
P = None
MAX_ROLAGEM = 8


def pops(base):
    return w.popups_novos(P.pid, base, P.mw)


def fechar_pops(base, manter=()):
    """Menus/listas: Esc (WM_CLOSE num menu desenhado pelo app ja derrubou o app). Janelas: Cancel/X."""
    for _ in range(3):
        abertos = [p for p in pops(base) if p[0] not in manter]
        if not abertos:
            return
        if not [p for p in abertos if w.eh_menu(p)]:
            break
        w.esc()
        time.sleep(0.5)
    for p in [p for p in pops(base) if p[0] not in manter]:
        if hasattr(AD, "fechar_janela"):
            AD.fechar_janela(p[0])
        else:
            w.fechar_dialogo(p[0])
    time.sleep(0.3)


def partes_rolagem(r, img, pasta, stem):
    """Rola o painel ate o conteudo parar de mudar; um print por parte. Devolve o total de partes."""
    k, prev = 1, img
    for _ in range(MAX_ROLAGEM):
        w.wheel(r, 1)
        w.away(r)
        cur = w.grab(r)
        if not w.mudou(prev, cur):
            break
        k += 1
        cur.save(pasta / f"{stem} ▸ rolagem parte {k}.png")
        prev = cur
    if k > 1:
        w.wheel(r, 10, para_baixo=False)
    return k


def submenus(r_painel, pasta, stem, menu, base, nome):
    """Explora o menu aberto passando o mouse em cada linha (nada e clicado)."""
    mr = w.win32gui.GetWindowRect(menu[0])
    if mr[2] - mr[0] > 600 or mr[3] - mr[1] > 900:  # grande demais: nao e menu suspenso
        return 0
    out = pasta / f"{stem} ▸ submenus"
    n = 0
    kw = P.cfg.get("linhas_menu", {})

    def explorar(cadeia, caminho):
        nonlocal n
        hwnd, rect = cadeia[-1]
        velhos = {}
        for i, (yy, _) in enumerate(w.linhas_do_popup(w.grab(rect), **kw), 1):
            conhecidos = {h for h, _ in cadeia}
            novos = w.hover_abre(P.pid, base, P.mw, rect[0] + 40, rect[1] + yy, conhecidos, velhos, 0.9)
            if not novos:
                continue
            sub = max(novos, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
            sr = w.win32gui.GetWindowRect(sub[0])
            n += 1
            p2 = caminho + [f"linha {i}"]
            w.grab(w.union([r_painel] + [c[1] for c in cadeia] + [sr]),
                   out / f"{n:03d} {w.safe_name(' > '.join(p2))}.png")
            explorar(cadeia + [(sub[0], sr)], p2)
            velhos = {t[0]: t[3] for t in pops(base) if t[0] not in conhecidos}

    explorar([(menu[0], mr)], [nome])
    return n


def executar(r, base, pasta, t, seq, rec):
    for a in t.get("antes", []):
        if "rolar" in a:
            w.wheel(r, a["rolar"])
        else:
            w.click(r[0] + a["x"], r[1] + a["y"])
            time.sleep(1.0)
            if not a.get("manter"):
                fechar_pops(base)
    if t.get("rolar"):
        w.wheel(r, t["rolar"])
    w.away(r)
    antes = w.grab(r)
    base_pop = {p[0] for p in pops(base)}
    w.click(r[0] + t["x"], r[1] + t["y"])
    time.sleep(1.2)
    novos = [p for p in pops(base) if p[0] not in base_pop]
    stem = f"{seq:03d} {w.safe_name(t['nome'])}"
    if t["tipo"] in ("lista", "menu"):
        if novos:
            w.grab(w.union([r] + [w.win32gui.GetWindowRect(p[0]) for p in novos]), pasta / f"{stem}.png")
            rec.update(status="ok", prints=1)
            if t["tipo"] == "menu" and t.get("submenus", True):
                menus = [p for p in novos if w.eh_menu(p)] or novos
                menu = max(menus, key=lambda p: (p[3][2] - p[3][0]) * (p[3][3] - p[3][1]))
                rec["submenus"] = submenus(r, pasta, stem, menu, base | base_pop, t["nome"])
                rec["prints"] += rec["submenus"]
            fechar_pops(base, base_pop)
        else:
            w.away(r)
            cur = w.grab(r)
            if w.mudou(antes, cur):
                cur.save(pasta / f"{stem}.png")
                rec.update(status="ok (abriu dentro do painel)", prints=1)
                if t.get("desfazer"):
                    w.click(r[0] + t["x"], r[1] + t["y"])
            else:
                rec.update(status="nada abriu", prints=0)
    else:  # aba / expandir
        if novos:
            w.grab(w.win32gui.GetWindowRect(novos[0][0]), pasta / f"{stem} ▸ janela.png")
            rec["nota"] = f"abriu janela {novos[0][2] or novos[0][1]!r}"
            fechar_pops(base, base_pop)
        w.away(r)
        cur = w.grab(r)
        if w.mudou(antes, cur):
            cur.save(pasta / f"{stem}.png")
            rec.update(status="ok", prints=partes_rolagem(r, cur, pasta, stem))
        else:
            rec.update(status="nada mudou", prints=0)
        if (t["tipo"] == "expandir" and rec["prints"]) or t.get("voltar"):
            w.wheel(r, 10, para_baixo=False)
            vs = t.get("voltar") or [{"x": t["x"], "y": t["y"]}]
            if t.get("rolar"):
                w.wheel(r, t["rolar"])
            for v in (vs if isinstance(vs, list) else [vs]):
                w.click(r[0] + v["x"], r[1] + v["y"])
                time.sleep(0.8)
            fechar_pops(base)


def rodar_alvo(t, seq, pasta, log):
    rec = {"painel": t["painel"], "alvo": t["nome"], "tipo": t["tipo"], "status": "", "prints": 0}
    r = AD.abrir(t)
    if not r:
        rec["status"] = "painel nao abriu"
        log.append(rec)
        AD.fechar(t)
        return
    base = {x[0] for x in w.top_windows(P.pid)}
    try:
        executar(r, base, pasta, t, seq, rec)
    except Exception as e:
        traceback.print_exc()
        rec["status"] = f"erro: {e}"
        w.esc()
    log.append(rec)
    print(f"  [{rec['status']}] {t['painel']} > {t['nome']} ({rec['prints']})", flush=True)
    AD.fechar(t)


def main():
    global AD, P, MAX_ROLAGEM
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--adaptador", help="modulo python (sem .py); padrao: o do app.json")
    ap.add_argument("--alvos", required=True)
    ap.add_argument("--pasta", required=True, help="saida, relativa ao MAPEAMENTO")
    ap.add_argument("--log", required=True, help="nome do log em 90-relatorios")
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("--max-rolagem", type=int, default=8)
    a = ap.parse_args()
    MAX_ROLAGEM = a.max_rolagem
    P = projeto.carregar(a.config)
    AD = importlib.import_module(a.adaptador) if a.adaptador else P.AD
    if not AD or not hasattr(AD, "abrir"):
        raise SystemExit("precisa de um adaptador com abrir(alvo)/fechar(alvo): copie adaptador_modelo.py")
    if hasattr(AD, "iniciar"):
        AD.iniciar(P)
    alvos = json.loads(Path(a.alvos).read_text(encoding="utf-8"))
    paineis = list(dict.fromkeys(t["painel"] for t in alvos))
    if a.only:
        paineis = [p for p in paineis if any(p.startswith(o) for o in a.only)]
    if a.skip:
        paineis = [p for p in paineis if not any(p.startswith(o) for o in a.skip)]
    log = []
    try:
        for n, painel in enumerate(paineis, 1):
            ts = [t for t in alvos if t["painel"] == painel]
            pasta = P.ROOT / a.pasta / f"{n:03d} {w.safe_name(painel)}"
            pasta.mkdir(parents=True, exist_ok=True)
            print(f"== {painel}: {len(ts)} alvos", flush=True)
            for seq, t in enumerate(ts, 1):
                if not w.vivo(P.pid, P.mw):
                    projeto.recuperar(P, "app nao esta rodando ou nao responde")
                try:
                    rodar_alvo(t, seq, pasta, log)
                except (Exception, SystemExit) as e:
                    if w.vivo(P.pid, P.mw) and not isinstance(e, SystemExit):
                        raise
                    log.append({"painel": painel, "alvo": t["nome"], "tipo": t["tipo"], "prints": 0,
                                "status": f"app caiu/instavel: {str(e)[:120]}"})
                    projeto.recuperar(P, str(e)[:120])
                    continue
                if t.get("reiniciar_depois"):
                    projeto.recuperar(P, "alvo marcado como instavel (reinicio preventivo)")
    finally:
        feitos = {r["painel"] for r in log}
        f = projeto.salvar_log(P, a.log, log, lambda r: r.get("painel") in feitos)
        print(f"{len(log)} alvos; {sum(r['prints'] for r in log)} prints -> {f}")


if __name__ == "__main__":
    main()
