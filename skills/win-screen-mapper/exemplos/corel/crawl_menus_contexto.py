"""Etapa 6d: menus de contexto (clique direito) e seus submenus.

Para cada "onde" (objeto de cada contexto, pagina vazia, area de trabalho, regua, paletas,
abas, barras...), monta o contexto, da um clique direito no ponto e percorre os submenus so
passando o mouse (mesmo metodo dos menus da barra, crawl_menus.Crawler). Nada e clicado
dentro do menu; fecha com Esc.

Saida: 07-menus-de-contexto/NN onde/...   Log: 90-relatorios/menus_contexto.json
Uso: python crawl_menus_contexto.py [--only retangulo pagina]
"""
import argparse
import json
import time

import win32api
import win32con
import win32gui

import contextos
import crawl_menus as cm
from contextos import CONTEXTOS, build, reset_doc

contextos.SOFT = True
from corelui import force_foreground, key, move

ROOT = cm.ROOT
OUT = ROOT / "07-menus-de-contexto"


def doc_pt(x, y):
    return cm.app.ActiveWindow.DocumentToScreen(x, y)


def sel_center():
    s = cm.app.ActiveDocument.SelectionRange
    return doc_pt(s.CenterX, s.CenterY)


def win_pt(fx, fy):
    """Ponto relativo a janela principal (fx, fy em pixels; negativos contam da direita/baixo)."""
    L, T, R, B = win32gui.GetWindowRect(cm.mw)
    return (R + fx if fx < 0 else L + fx, B + fy if fy < 0 else T + fy)


def text_editing():
    build(cm.app, "texto-artistico")
    cm.app.ActiveTool = 7  # ferramenta Text
    time.sleep(0.5)
    p = sel_center()
    from corelui import click
    click(*p)
    time.sleep(0.8)
    return p


def node_editing():
    build(cm.app, "curva")
    cm.app.ActiveTool = 2  # ferramenta Shape
    time.sleep(0.5)
    return doc_pt(2, 6)  # meio do lado esquerdo da curva


# (nome da pasta, descricao, preparo -> ponto do clique direito)
ONDE = [(c, f"objeto: {d}", (lambda c=c: (build(cm.app, c), sel_center())[1]))
        for c, d in CONTEXTOS.items() if c not in ("varias-paginas", "com-efeitos", "tabela-celulas")]
ONDE += [
    ("tabela-celulas", "celulas selecionadas com a ferramenta Table",
     lambda: (build(cm.app, "tabela-celulas"), doc_pt(3.2, 6.0))[1]),
    ("texto-em-edicao", "dentro do texto artistico com a ferramenta Text", text_editing),
    ("nos-da-curva", "curva com a ferramenta Shape (edicao de nos)", node_editing),
    ("pagina", "area vazia da pagina, nada selecionado", lambda: (reset_doc(cm.app), doc_pt(4.25, 2))[1]),
    ("area-de-trabalho", "fora da pagina (desktop), nada selecionado", lambda: (reset_doc(cm.app), doc_pt(-2.5, 5))[1]),
    ("regua", "regua horizontal", lambda: (reset_doc(cm.app), win_pt(900, 170))[1]),
    ("paleta-de-cores", "amostra da paleta de cores lateral", lambda: (reset_doc(cm.app), win_pt(-18, 420))[1]),
    ("paleta-do-documento", "paleta do documento (barra inferior)", lambda: (reset_doc(cm.app), win_pt(700, -54))[1]),
    ("aba-da-pagina", "aba 'Page 1' no rodape", lambda: (reset_doc(cm.app), win_pt(280, -80))[1]),
    ("aba-do-documento", "aba do documento (Untitled-1)", lambda: (reset_doc(cm.app), win_pt(230, 150))[1]),
    ("barra-de-ferramentas", "area vazia da barra Standard", lambda: (reset_doc(cm.app), win_pt(-300, 73))[1]),
    ("barra-de-status", "barra de status", lambda: (reset_doc(cm.app), win_pt(1100, -20))[1]),
    ("caixa-de-ferramentas", "caixa de ferramentas", lambda: (reset_doc(cm.app), win_pt(24, 360))[1]),
]


def right_click(x, y):
    move(x, y)
    time.sleep(0.15)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    c = cm.Crawler(OUT)
    todo = [(n, o) for n, o in enumerate(ONDE, 1) if not a.only or o[0] in a.only]
    for n, (nome, desc, prep) in todo:
        print(f"== {nome}: {desc}", flush=True)
        try:
            x, y = prep()
        except Exception as e:
            c.record([nome], "", "erro", note=f"preparo falhou: {e}")
            continue
        force_foreground(cm.mw)
        time.sleep(0.5)
        baseline = {t[0] for t in cm.top_windows(cm.pid)}
        c.start_root(n, nome, (int(x) - 12, int(y) - 12, int(x) + 12, int(y) + 12))
        right_click(x, y)
        p = cm.wait_popups(baseline, 1, 2.5)
        p = [w for w in p if w[1].startswith("Afx:")]
        if not p:
            c.record([nome], "", "sem_menu", note=f"nenhum menu de contexto abriu ({desc})")
            key(win32con.VK_ESCAPE, 2)
            continue
        time.sleep(0.4)
        r = win32gui.GetWindowRect(p[0][0])
        move(x, y)  # cursor fora das linhas: sem destaque
        f = c.shot([nome], [r])
        c.record([nome], "", "ok", f, [list(r)], desc)
        c.explore(baseline, [(p[0][0], r)], [nome], "")
        key(win32con.VK_ESCAPE, 4)
        time.sleep(1.5)
        if cm.popups(baseline):
            key(win32con.VK_ESCAPE, 3)
        left = [t for t in cm.top_windows(cm.pid) if t[0] not in baseline and t[0] != cm.mw
                and t[1] not in ("SysShadow", "tooltips_class32")]
        if left:
            raise SystemExit(f"!! sobrou janela depois de {nome}: {left}")
    cm.app.ActiveTool = 1
    reset_doc(cm.app)
    (OUT / "_tmp.png").unlink(missing_ok=True)
    logf = ROOT / "90-relatorios" / "menus_contexto.json"
    old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() and a.only else []
    feitos = {o[0] for _, o in todo}
    keep = [r for r in old if r["path"].split(" > ")[0] not in feitos]
    logf.write_text(json.dumps(keep + c.log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(c.log)} registros -> {logf}")


if __name__ == "__main__":
    main()
