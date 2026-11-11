"""Etapa 6f: dockers por dentro (passe por visao).

A automacao do Windows quase nao enxerga o conteudo dos dockers (o Corel desenha os controles).
Os alvos (abas, listas, menus "...", secoes recolhidas) foram marcados olhando os prints e
ficam em docker_alvos.json, com x, y relativos ao canto superior esquerdo do painel:

  {"docker": "Transform", "nome": "aba Rotate", "tipo": "aba", "x": 45, "y": 40,
   "antes": [{"x": 10, "y": 40}] ou [{"rolar": 2}]}

tipo: aba     -> clica, fotografa o painel (com rolagem) e deixa como esta
      lista   -> clica, fotografa painel + lista aberta, fecha a lista (Esc; dialogo pelo X)
      menu    -> igual a lista (menus de "..." e setas)
      expandir-> clica, fotografa (com rolagem), clica de novo para recolher

Nunca clica em botoes de acao (Apply, Generate, Export, Delete, Reset, Create, New, Add...):
so os alvos listados, que foram escolhidos a dedo.

Cada alvo parte do zero: contexto remontado, docker aberto, cliques "antes", alvo.

Saida: 04-dockers/dentro/NNN Docker/...   Log: 90-relatorios/dockers_dentro.json
Uso: python crawl_dockers_dentro.py iniciais [--only Transform]
     python crawl_dockers_dentro.py alvos [--only Transform]
"""
import argparse
import json
import time

import win32api
import win32con
import win32gui
from PIL import Image, ImageChops, ImageDraw

import contextos
import crawl_telas as ct
from contextos import build, reset_doc
from corelui import click, force_foreground, grab, key, move, safe_name
from crawl_dockers import invoke, kids, scroll_parts

contextos.SOFT = True  # limpa o documento em vez de fechar (fechar depois de menus derrubou o Corel)
ROOT, HERE = ct.ROOT, ct.HERE
OUT = ROOT / "04-dockers" / "dentro"
PRE = "Window > Dockers > "
CTX = {"Pages": "varias-paginas", "Symbols": "simbolo", "Find and Replace": "texto-artistico",
       "Align and Distribute": "selecao-multipla", "Fit Objects to Path": "selecao-multipla",
       "Shape": "selecao-multipla", "Corners": "curva", "Join Curves": "curva", "Text": "texto-artistico",
       "Font Sampler": "texto-artistico", "Glyphs": "texto-artistico", "Effects > Artistic Media": "curva",
       "Effects > Bitmap Mask": "bitmap", "Effects > Blend": "selecao-multipla", "Effects > PhotoCocktail": "bitmap",
       "Effects > Pointillizer": "bitmap", "Links and Rollovers": "rollover"}
SKIP_POP = ("SysShadow", "tooltips_class32")


def dockers():
    inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
    items = [x for x in inv if x["kind"] == "menu_item" and x["path"].startswith(PRE) and not x["has_submenu"]]
    return [(i, x["path"][len(PRE):].strip(), x["guid"]) for i, x in enumerate(items, 1)]


def folder(n, nome):
    return OUT / f"{n:03d} {safe_name(nome.replace(' > ', ' ▸ '))}"


def vivo():
    from corelui import corel_pid
    try:
        return bool(win32gui.IsWindow(ct.mw)) and corel_pid() == ct.pid
    except Exception:
        return False


def recuperar(motivo):
    """Corel caiu (ou ficou instavel): encerra o processo, reabre com File > New > OK e reconecta.
    O Crash Report que aparece ao reabrir e fechado pelo X (nada e enviado)."""
    import subprocess
    import sys
    from corelui import connect, corel_pid, main_window
    print(f"  !! reiniciando o Corel: {motivo}", flush=True)
    ct.app = ct.au = None
    cm = sys.modules.get("crawl_menus")
    if cm:
        cm.app = cm.au = None
    subprocess.run(["taskkill", "/IM", "CorelDRW.exe", "/F"], capture_output=True)
    time.sleep(5)
    out = subprocess.run([sys.executable, "-W", "ignore", str(HERE / "restart_corel.py")],
                         capture_output=True, text=True, encoding="utf-8")
    if "pronto" not in out.stdout:
        raise SystemExit("!! nao consegui reabrir o Corel: " + out.stdout[-800:] + out.stderr[-800:])
    ct.app, ct.au = connect()
    ct.pid = corel_pid()
    ct.mw = main_window(ct.pid)
    if cm:
        cm.app, cm.au, cm.pid, cm.mw = ct.app, ct.au, ct.pid, ct.mw
    time.sleep(2)


def paineis():
    """Paineis de docker abertos (ViewHost estreito; a area de desenho e o ViewHost largo)."""
    return [v[1] for h, v in kids().items() if v[0] == "ViewHost"
            and 150 < v[1][2] - v[1][0] < 900 and v[1][3] - v[1][1] > 300]


def fechar_todos():
    """Fecha qualquer docker aberto pelo X do painel (o Corel reabre o workspace salvo)."""
    for _ in range(8):
        ps = paineis()
        if not ps:
            return
        r = ps[0]
        click(r[2] - 17, r[1] + 13)
        time.sleep(1.2)
    raise SystemExit(f"!! nao consegui fechar os dockers abertos: {paineis()}")


def open_docker(nome, guid):
    ctx = CTX.get(nome, "retangulo")
    force_foreground(ct.mw)
    fechar_todos()
    ct.com(lambda app, au: build(app, ctx))
    force_foreground(ct.mw)
    k0 = kids()
    w0 = {t[0] for t in ct.top_windows(ct.pid)}
    invoke(guid)
    time.sleep(2.5)
    hosts = [(h, v[1]) for h, v in kids().items() if h not in k0 and v[0] == "ViewHost"]
    if not hosts:  # o docker ja estava aberto (o 1o comando fechou): abre de novo
        k0 = kids()
        invoke(guid)
        time.sleep(2.5)
        hosts = [(h, v[1]) for h, v in kids().items() if h not in k0 and v[0] == "ViewHost"]
    if not hosts:
        return None, w0, ctx
    return max(hosts, key=lambda t: (t[1][2] - t[1][0]) * (t[1][3] - t[1][1]))[1], w0, ctx


def close_docker(guid, w0):
    fechar_pops(w0)
    invoke(guid)
    time.sleep(1.2)
    left = [t for t in ct.new_windows(w0) if t[1] not in SKIP_POP]
    for t in left:
        ct.close_window(t[0])
    if [t for t in ct.new_windows(w0) if t[1] not in SKIP_POP]:
        raise SystemExit("!! sobrou janela depois de fechar o docker")
    fechar_todos()


def fechar_pops(w0, keep=()):
    """Menus/listas do Corel (Afx) fecham com Esc (WM_CLOSE neles derrubou o Corel); dialogos pelo X."""
    for _ in range(3):
        if not [p for p in popups(w0) if p[0] not in keep]:
            return
        if not [p for p in popups(w0) if p[0] not in keep and p[1].startswith("Afx:")]:
            break
        key(win32con.VK_ESCAPE)
        time.sleep(0.5)
    for p in [p for p in popups(w0) if p[0] not in keep]:
        ct.close_window(p[0])
    time.sleep(0.3)


def popups(w0):
    L, T, R, B = win32gui.GetWindowRect(ct.mw)

    def ok(t):
        try:
            a, b, c, d = win32gui.GetWindowRect(t[0])
            # so janelas visiveis, com tamanho e dentro da janela do Corel (nada do outro monitor)
            return (win32gui.IsWindowVisible(t[0]) and c - a > 4 and d - b > 4
                    and a >= L - 40 and c <= R + 40 and b >= T - 40 and d <= B + 40)
        except Exception:
            return False
    return [t for t in ct.top_windows(ct.pid) if t[0] not in w0 and t[0] != ct.mw and t[1] not in SKIP_POP and ok(t)]


def wheel(r, n):
    move((r[0] + r[2]) // 2, (r[1] + r[3]) // 2)
    for _ in range(n):
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -120 * 15, 0)
        time.sleep(0.5)


def wheel_up(r, n=10):
    move((r[0] + r[2]) // 2, (r[1] + r[3]) // 2)
    for _ in range(n):
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, 120 * 15, 0)
        time.sleep(0.2)
    time.sleep(0.4)


def away(r):
    move(r[0] - 150, r[1] + 300)  # tira o mouse do painel (tooltip)
    time.sleep(0.9)


def gridded(img, path):
    """Copia com grade (10/50 px) para marcar alvos olhando o print."""
    im = img.convert("RGB")
    d = ImageDraw.Draw(im)
    for x in range(0, im.width, 10):
        d.line([(x, 0), (x, im.height)], fill=(90, 90, 0) if x % 50 else (200, 200, 0), width=1)
    for y in range(0, im.height, 10):
        d.line([(0, y), (im.width, y)], fill=(90, 90, 0) if y % 50 else (200, 200, 0), width=1)
    for x in range(0, im.width, 50):
        for y in range(0, im.height, 100):
            d.text((x + 1, y + 1), f"{x},{y}", fill=(255, 80, 80))
    im.save(path)


def iniciais(lst, gdir):
    gdir.mkdir(parents=True, exist_ok=True)
    for n, nome, guid in lst:
        f = folder(n, nome)
        f.mkdir(parents=True, exist_ok=True)
        for old in f.glob("*.png"):
            old.unlink()
        r, w0, ctx = open_docker(nome, guid)
        if not r:
            print(f"!! {nome}: painel nao abriu", flush=True)
            close_docker(guid, w0)
            continue
        away(r)
        img = grab(r, f / "000 inicial.png")
        gridded(img, gdir / f"{n:03d} {safe_name(nome.replace(' > ', ' - '))} (0).png")
        k = scroll_parts(r, img, f, "000 inicial")
        for j in range(2, k + 1):
            gridded(Image.open(f / f"000 inicial ▸ rolagem parte {j}.png"),
                    gdir / f"{n:03d} {safe_name(nome.replace(' > ', ' - '))} ({j - 1}).png")
        print(f"  {nome} ({ctx}): {k} parte(s)", flush=True)
        close_docker(guid, w0)


def run_target(n, nome, guid, t, seq, log):
    f = folder(n, nome)
    f.mkdir(parents=True, exist_ok=True)
    r, w0, ctx = open_docker(nome, guid)
    rec = {"docker": nome, "alvo": t["nome"], "tipo": t["tipo"], "contexto": ctx, "status": "", "prints": 0}
    if not r:
        rec["status"] = "painel nao abriu"
        log.append(rec)
        close_docker(guid, w0)
        raise SystemExit(f"!! {nome}: painel nao abriu (docker ja aberto ou Corel inconsistente)")
    try:
        _target(r, w0, f, nome, t, seq, rec)
    except Exception as e:
        import traceback
        traceback.print_exc()
        rec.update(status=f"erro: {e}")
        print(f"  [erro] {nome} ▸ {t['nome']}: {e}", flush=True)
        key(win32con.VK_ESCAPE)
    log.append(rec)
    close_docker(guid, w0)


def submenus(r, f, stem, nome, afx, base):
    import crawl_menus as cm
    c = cm.Crawler(f)
    c.out = f / f"{stem} ▸ submenus"
    (c.out / "tela-inteira").mkdir(parents=True, exist_ok=True)
    c.title_rect = r
    menu = max(afx, key=lambda p: (p[3][2] - p[3][0]) * (p[3][3] - p[3][1]))
    mr = win32gui.GetWindowRect(menu[0])
    if mr[2] - mr[0] > 600 or mr[3] - mr[1] > 900:  # nao e um menu suspenso
        return 0
    baseline = set(base) | {t[0] for t in ct.top_windows(ct.pid) if t[1] in SKIP_POP}
    c.explore(baseline, [(menu[0], win32gui.GetWindowRect(menu[0]))], [nome], "")
    (f / "_tmp.png").unlink(missing_ok=True)
    k = len([x for x in c.log if x["status"] == "ok"])
    if not k:
        import shutil
        shutil.rmtree(c.out, ignore_errors=True)
    return k


def _target(r, w0, f, nome, t, seq, rec):
    for a in t.get("antes", []):
        if "rolar" in a:
            wheel(r, a["rolar"])
        else:
            click(r[0] + a["x"], r[1] + a["y"])
            time.sleep(1.0)
            if not a.get("manter"):  # "manter": a lista aberta e o alvo (escolher um item dela)
                fechar_pops(w0)  # o clique "antes" nao deve deixar nada aberto
    if t.get("rolar"):
        wheel(r, t["rolar"])
    before = away(r) or grab(r, ROOT / "_tmp.png")
    base_pop = {p[0] for p in popups(w0)}
    click(r[0] + t["x"], r[1] + t["y"])
    time.sleep(1.2)
    pops = [p for p in popups(w0) if p[0] not in base_pop]
    stem = f"{seq:03d} {safe_name(t['nome'])}"
    if t["tipo"] in ("lista", "menu"):
        if pops:
            rects = [r] + [win32gui.GetWindowRect(p[0]) for p in pops]
            box = (min(x[0] for x in rects), min(x[1] for x in rects), max(x[2] for x in rects),
                   max(x[3] for x in rects))
            grab(box, f / f"{stem}.png")
            rec.update(status="ok", prints=1)
            afx = [p for p in pops if p[1].startswith("Afx:")]
            if t["tipo"] == "menu" and afx:  # submenus: so passando o mouse (mesmo metodo dos menus)
                rec["submenus"] = submenus(r, f, stem, t["nome"], afx, w0 | base_pop)
                rec["prints"] += rec["submenus"]
            fechar_pops(w0, base_pop)
        else:
            away(r)
            cur = grab(r, f / f"{stem}.png")
            mudou = ImageChops.difference(before.convert("RGB"), cur.convert("RGB")).getbbox()
            rec.update(status="ok (abriu dentro do painel)" if mudou else "nada abriu", prints=1 if mudou else 0)
            if not mudou:
                (f / f"{stem}.png").unlink()
            elif t.get("desfazer"):
                click(r[0] + t["x"], r[1] + t["y"])
    else:  # aba / expandir
        if pops:  # abriu algo (janela/menu): fotografa e fecha
            grab(win32gui.GetWindowRect(pops[0][0]), f / f"{stem} ▸ janela.png")
            fechar_pops(w0, base_pop)
            rec["nota"] = f"abriu janela {pops[0][2] or pops[0][1]!r}"
        away(r)
        cur = grab(r, f / f"{stem}.png")
        mudou = ImageChops.difference(before.convert("RGB"), cur.convert("RGB")).getbbox()
        if mudou:
            k = scroll_parts(r, cur, f, stem)
            rec.update(status="ok", prints=k)
        else:
            (f / f"{stem}.png").unlink()
            rec.update(status="nada mudou", prints=0)
        # devolve o docker ao estado original: recolhe a secao / volta a opcao padrao
        if (t["tipo"] == "expandir" and mudou) or t.get("voltar"):
            wheel_up(r)
            vs = t.get("voltar") or {"x": t["x"], "y": t["y"]}
            if t.get("rolar"):
                wheel(r, t["rolar"])
            for v in (vs if isinstance(vs, list) else [vs]):
                click(r[0] + v["x"], r[1] + v["y"])
                time.sleep(0.8)
            fechar_pops(w0)
    print(f"  [{rec['status']}] {nome} ▸ {t['nome']} ({rec['prints']})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["iniciais", "alvos"])
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--skip", nargs="*", default=[])
    a = ap.parse_args()
    lst = dockers()
    if a.only:
        lst = [d for d in lst if any(d[1].startswith(o) for o in a.only)]
    if a.skip:
        lst = [d for d in lst if not any(d[1].startswith(o) for o in a.skip)]
    if a.modo == "iniciais":
        iniciais(lst, ROOT.parent / "scripts" / "_grade_dockers")
    else:
        alvos = json.loads((HERE / "docker_alvos.json").read_text(encoding="utf-8"))
        logf = ROOT / "90-relatorios" / "dockers_dentro.json"
        old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() else []
        log, feitos = [], set()
        try:
            for n, nome, guid in lst:
                ts = [t for t in alvos if t["docker"] == nome]
                if not ts:
                    continue
                f = folder(n, nome)
                for oldp in f.glob("[0-9][0-9][0-9] *"):
                    if oldp.name.startswith("000 inicial"):
                        continue
                    if oldp.is_dir():
                        import shutil
                        shutil.rmtree(oldp)
                    else:
                        oldp.unlink()
                print(f"== {nome}: {len(ts)} alvos", flush=True)
                for seq, t in enumerate(ts, 1):
                    if not vivo():
                        recuperar("Corel nao esta rodando")
                    try:
                        run_target(n, nome, guid, t, seq, log)
                    except (Exception, SystemExit) as e:
                        if vivo() and not isinstance(e, SystemExit):
                            raise
                        log.append({"docker": nome, "alvo": t["nome"], "tipo": t["tipo"], "status":
                                    f"Corel caiu/instavel: {str(e)[:120]}", "prints": 0})
                        recuperar(str(e)[:120])
                        continue
                    if t.get("reiniciar_depois"):
                        recuperar("alvo marcado como instavel (reinicio preventivo)")
                feitos.add(nome)
                logf.write_text(json.dumps([x for x in old if x["docker"] not in feitos] + log,
                                           ensure_ascii=False, indent=1), encoding="utf-8")
        finally:
            logf.write_text(json.dumps([x for x in old if x["docker"] not in feitos | {l['docker'] for l in log}]
                                       + log, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "_tmp.png").unlink(missing_ok=True)
    ct.com(lambda app, au: reset_doc(app))


if __name__ == "__main__":
    main()
