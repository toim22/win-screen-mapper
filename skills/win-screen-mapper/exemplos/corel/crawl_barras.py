"""Etapa 6c: barras de ferramentas.

- Barras ocultas (CommandBars com Visible=False): mostra, fotografa, oculta de novo (estado
  original do workspace restaurado no fim).
- Barras sempre visiveis: recortes da janela principal (Standard, barra de status, paletas).

Saida: 06-barras/   Log: 90-relatorios/barras.json
"""
import json
import time

import win32gui

import crawl_telas as ct
from contextos import build, reset_doc
from corelui import force_foreground, grab, safe_name

ROOT = ct.ROOT
OUT = ROOT / "06-barras"
SKIP = {"Menu Bar"}  # ja fotografada nos menus


def kids():
    out = {}

    def cb(h, _):
        if win32gui.IsWindowVisible(h):
            out[h] = (win32gui.GetClassName(h), win32gui.GetWindowRect(h))
        return True

    win32gui.EnumChildWindows(ct.mw, cb, None)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ct.com(lambda app, au: build(app, "retangulo"))
    force_foreground(ct.mw)
    time.sleep(1)
    log = []
    full = win32gui.GetWindowRect(ct.mw)
    L, T, R, B = full
    fixos = {
        "Standard (barra padrao)": (L, T + 56, R, T + 92),
        "Barra de status": (L, B - 40, R, B),
        "Paleta do documento": (L + 40, B - 68, R, B - 40),
        "Paleta de cores (lateral)": (R - 36, T + 135, R, B - 40),
    }
    for nome, r in fixos.items():
        grab(r, OUT / f"00 {nome}.png")
        log.append({"barra": nome, "status": "ok", "como": "recorte da janela principal"})
    grab(full, OUT / "00 tela inteira (referencia).png")

    def bars(app, au):
        return [(i, app.CommandBars.Item(i).Name, app.CommandBars.Item(i).Visible)
                for i in range(1, app.CommandBars.Count + 1)]

    for i, name, vis in ct.com(bars):
        if name in SKIP or vis:
            continue
        k0, w0 = kids(), {t[0] for t in ct.top_windows(ct.pid)}
        ct.com(lambda app, au: setattr(app.CommandBars.Item(i), "Visible", True))
        time.sleep(1.5)
        tops = [t for t in ct.new_windows(w0) if t[1] not in ("SysShadow", "tooltips_class32")]
        new = [v[1] for h, v in kids().items() if h not in k0]
        fname = f"{i:02d} {safe_name(name)}.png"
        rec = {"barra": name, "status": "ok", "image": str((OUT / fname).relative_to(ROOT))}
        if tops:
            grab(win32gui.GetWindowRect(tops[0][0]), OUT / fname)
            rec["como"] = "flutuante"
        elif new:
            r = max(new, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
            grab((r[0] - 2, r[1] - 2, r[2] + 2, r[3] + 2), OUT / fname)
            rec["como"] = "encaixada"
        else:
            grab(win32gui.GetWindowRect(ct.mw), OUT / fname)
            rec.update(como="tela inteira", status="sem_janela_detectada")
        ct.com(lambda app, au: setattr(app.CommandBars.Item(i), "Visible", False))
        time.sleep(0.8)
        print(f"  [{rec['status']}] {name} ({rec['como']})", flush=True)
        log.append(rec)
    (ROOT / "90-relatorios" / "barras.json").write_text(json.dumps(log, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    print("visiveis agora:", [n for _, n, v in ct.com(bars) if v])
    ct.com(lambda app, au: reset_doc(app))


if __name__ == "__main__":
    main()
