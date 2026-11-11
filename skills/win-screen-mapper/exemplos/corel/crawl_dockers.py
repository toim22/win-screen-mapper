"""Etapa 6a: abre cada docker do menu Window > Dockers, fotografa e fecha.

Contexto: retangulo selecionado (dockers como Properties/Transform mostram mais campos com
objeto selecionado). O painel do docker e uma janela filha "ViewHost" da janela principal:
o recorte usa o retangulo dela. Fecha clicando o mesmo item do menu de novo (alterna).

Saida: 04-dockers/<contexto>/NNN Nome.png (recorte) + tela-inteira/   Log: 90-relatorios/dockers_<contexto>.json
Uso: python crawl_dockers.py [--context retangulo] [--only Properties Transform]
"""
import argparse
import json
import subprocess
import sys
import time

import win32gui

import crawl_telas as ct
from contextos import build, reset_doc
from corelui import force_foreground, grab, key, safe_name, win32con

ROOT, HERE = ct.ROOT, ct.HERE


def kids():
    out = {}

    def cb(h, _):
        if win32gui.IsWindowVisible(h):
            out[h] = (win32gui.GetClassName(h), win32gui.GetWindowRect(h))
        return True

    win32gui.EnumChildWindows(ct.mw, cb, None)
    return out


def invoke(guid):
    p = subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "invoke_one.py"), guid],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(10)
    except subprocess.TimeoutExpired:
        pass


def scroll_parts(r, img, out, stem, max_parts=8):
    """Rola o conteudo do docker com a roda do mouse; um print por parte nova."""
    import win32api
    from corelui import move
    from PIL import ImageChops
    move((r[0] + r[2]) // 2, (r[1] + r[3]) // 2)
    prev, k = img, 1
    for _ in range(max_parts):
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -120 * 15, 0)
        time.sleep(0.8)
        cur = grab(r, ROOT / "_tmp.png")
        if not ImageChops.difference(prev.convert("RGB"), cur.convert("RGB")).getbbox():
            break
        k += 1
        cur.save(out / f"{stem} ▸ rolagem parte {k}.png")
        prev = cur
    return k


def area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", default="retangulo")
    ap.add_argument("--only", nargs="*", default=[])
    a = ap.parse_args()
    inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
    pre = "Window > Dockers > "
    items = [x for x in inv if x["kind"] == "menu_item" and x["path"].startswith(pre) and not x["has_submenu"]]
    num = {x["guid"]: i for i, x in enumerate(items, 1)}  # numero fixo, mesmo com --only
    if a.only:
        items = [x for x in items if any(x["path"][len(pre):].strip().startswith(o) for o in a.only)]
    out = ROOT / "04-dockers" / a.context
    (out / "tela-inteira").mkdir(parents=True, exist_ok=True)
    logf = ROOT / "90-relatorios" / f"dockers_{a.context}.json"
    old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() else []
    log = []
    for x in items:
        n = num[x["guid"]]
        nome = x["path"][len(pre):].strip()
        ct.com(lambda app, au: build(app, a.context))
        force_foreground(ct.mw)
        k0, w0 = kids(), {t[0] for t in ct.top_windows(ct.pid)}
        invoke(x["guid"])
        time.sleep(2.5)
        new = {h: v for h, v in kids().items() if h not in k0}
        tops = [t for t in ct.new_windows(w0) if t[1] not in ('SysShadow', 'tooltips_class32')]
        rec = {"docker": nome, "guid": x["guid"], "image": "", "status": "", "note": ""}
        fname = f"{n:03d} " + safe_name(nome.replace(" > ", " ▸ ")) + ".png"
        full = win32gui.GetWindowRect(ct.mw)
        hosts = [v[1] for v in new.values() if v[0] == "ViewHost"] or \
                sorted((v[1] for v in new.values()), key=area, reverse=True)[:1]
        if tops:  # docker flutuante ou janela
            big = max(tops, key=lambda t: area(t[3]))
            grab(win32gui.GetWindowRect(big[0]), out / fname)
            rec.update(status="janela", note=f"abriu janela/flutuante: {big[2] or big[1]}")
        elif hosts:
            r = max(hosts, key=area)
            img = grab(r, out / fname)
            rec["status"] = "ok"
            rec["partes"] = scroll_parts(r, img, out, fname[:-4])
        else:
            rec.update(status="sem_mudanca", note="nenhum painel novo apareceu")
        grab(full, out / "tela-inteira" / fname)
        rec["image"] = str((out / fname).relative_to(ROOT)) if rec["status"] != "sem_mudanca" else \
            str((out / "tela-inteira" / fname).relative_to(ROOT))
        # fecha: o item do menu alterna o docker
        if new or tops:
            invoke(x["guid"])
            time.sleep(1.5)
        for t in ct.new_windows(w0):
            ct.close_window(t[0])
        sobrou = [h for h in kids() if h not in k0 and kids()[h][0] == "ViewHost"]
        if sobrou:
            rec["note"] += " | painel nao fechou pelo menu"
        print(f"  [{rec['status']}] {nome} {rec['note']}", flush=True)
        log.append(rec)
        logf.write_text(json.dumps([r for r in old if r["docker"] not in {l['docker'] for l in log}] + log,
                                   ensure_ascii=False, indent=1), encoding="utf-8")
        if ct.new_windows(w0):
            raise SystemExit(f"!! janela sobrou depois de {nome}")
        key(win32con.VK_ESCAPE)
    ct.com(lambda app, au: reset_doc(app))
    print(f"{len(log)} dockers -> {logf}")


if __name__ == "__main__":
    main()
