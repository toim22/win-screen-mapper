"""Etapa 2/3 (menus): abre cada menu da barra e percorre submenus so passando o mouse.

Nada e clicado alem do item da barra de menus; os submenus abrem por hover. Cada menu
e submenu aberto vira um PNG (janela principal + menus abertos) e uma linha no log.

Uso:
  python crawl_menus.py                 # todos os menus da barra
  python crawl_menus.py Tools Window    # so esses menus (pelo caption sem &)
  --context nome   subpasta de saida (padrao: doc_vazio)
"""
import argparse
import json
import time
from pathlib import Path

from PIL import Image

from corelui import (MENUBAR, SEPARATOR, click, connect, corel_pid, force_foreground, grab, key, main_window, move,
                     safe_name, top_windows, union, win32con, win32gui)

ROW_H, SEP_H, PAD = 22, 7, 3
HOVER_WAIT = 0.55
CROP_MARGIN = 16
ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
# Menus da barra que nao entram: Purchase (pedido do usuario) e o menu Debug oculto.
SKIP_ROOTS = {"ac291790-gf51-d4s1-f23x-dsf9dfb6fgf5", "67cfe9c0-890c-07b2-4de2-cc788654e6ef"}

app, au = connect()
pid = corel_pid()
mw = main_window(pid)


def clean(c):
    return c.replace("&&", "\0").replace("&", "").replace("\0", "&").replace("…", "...").strip()


def bar_items(bar):
    out = []
    for i in range(au.GetNumItemsOnBar(bar)):
        g, has = au.GetItem(bar, i)
        out.append({"guid": g, "caption": clean(au.GetCaptionText(g) or "") if g else "",
                    "has_sub": bool(has), "sep": g.lower() == SEPARATOR})
    return out


def popup_rows(img):
    """Devolve lista de (y_centro, indice_segmento) das linhas de item de um popup."""
    W, H = img.size
    rgb = img.convert("RGB")
    px = rgb.load()
    bg = max(rgb.getcolors(W * H), key=lambda t: t[0])[1]  # cor predominante = fundo
    seps = []
    for y in range(PAD, H - PAD):
        row = {px[x, y] for x in range(36, W - 12, 3)}
        if len(row) == 1:
            c = next(iter(row))
            if c != bg and abs(sum(c) - sum(bg)) > 60:
                seps.append(y)
    # agrupa linhas de separador consecutivas
    lines = []
    for y in seps:
        if not lines or y - lines[-1][-1] > 1:
            lines.append([y])
        else:
            lines[-1].append(y)
    rows, seg, start = [], 0, PAD
    bounds = [(l[0] - SEP_H // 2, l[-1] + SEP_H - SEP_H // 2) for l in lines] + [(H - PAD, H)]
    for s0, s1 in bounds:
        n = round((s0 - start) / ROW_H)
        for i in range(max(n, 0)):
            rows.append((start + i * ROW_H + ROW_H // 2, seg))
        seg += 1
        start = s1
    return rows


def map_names(items, rows):
    """Cruza segmentos do inventario com os da tela. Devolve nome/guid por linha (ou None)."""
    segs, cur = [], []
    for it in items:
        if it["sep"]:
            if cur:
                segs.append(cur)
            cur = []
        elif it["guid"]:
            cur.append(it)
    if cur:
        segs.append(cur)
    screen = {}
    for y, s in rows:
        screen.setdefault(s, []).append(y)
    screen = [screen[k] for k in sorted(screen)]
    # descarta segmentos so de placeholders que sumiram, se a contagem nao bater
    if len(segs) != len(screen):
        segs = [s for s in segs if any(i["caption"] for i in s)] if len(segs) > len(screen) else segs
    names = [None] * len(rows)
    if len(segs) != len(screen):
        return names, False
    k, exact = 0, True
    for inv, scr in zip(segs, screen):
        if len(inv) == len(scr):
            for it in inv:
                names[k] = it
                k += 1
            continue
        ph = [i for i, it in enumerate(inv) if not it["caption"]]
        extra = len(scr) - len(inv)
        if len(ph) == 1 and extra >= -1:
            for i, it in enumerate(inv):
                span = extra + 1 if i == ph[0] else 1
                for j in range(span):
                    names[k] = dict(it, caption=f"{it['caption'] or 'dynamic'} #{j + 1}") if i == ph[0] else it
                    k += 1
        else:
            exact = False
            k += len(scr)
    return names, exact


def popups(baseline):
    return [t for t in top_windows(pid) if t[0] not in baseline and t[0] != mw]


def wait_popups(baseline, expect, timeout=2.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        p = popups(baseline)
        if len(p) == expect:
            return p
        time.sleep(0.05)
    return popups(baseline)


class Crawler:
    def __init__(self, outdir):
        self.base = outdir
        self.out = outdir
        self.log = []
        self.seq = 0
        self.title_rect = None
        self.hidden = 0

    def start_root(self, n, caption, title_rect):
        self.out = self.base / f"{n:02d} {safe_name(caption)}"
        (self.out / "tela-inteira").mkdir(parents=True, exist_ok=True)
        self.seq = 0
        self.title_rect = title_rect

    def shot(self, path, chain_rects):
        """Salva o recorte (barra do menu + cascata aberta) e a janela inteira."""
        self.seq += 1
        name = f"{self.seq:03d} " + safe_name(" ▸ ".join(path)) + ".png"
        main = win32gui.GetWindowRect(mw)
        full = union([main] + chain_rects)
        img = grab(full, self.out / "tela-inteira" / name)
        c = union([self.title_rect] + chain_rects)
        c = (max(c[0] - CROP_MARGIN, full[0]), max(c[1] - CROP_MARGIN, full[1]),
             min(c[2] + CROP_MARGIN, full[2]), min(c[3] + CROP_MARGIN, full[3]))
        img.crop((c[0] - full[0], c[1] - full[1], c[2] - full[0], c[3] - full[1])).save(self.out / name)
        return self.out / name

    def record(self, path, guid, status, img=None, rects=None, note=""):
        self.log.append({"path": " > ".join(path), "guid": guid, "status": status,
                         "image": str(img.relative_to(ROOT)) if img else "", "rects": rects or [], "note": note})
        print(f"  [{status}] {' > '.join(path)} {note}", flush=True)

    def targets(self, rect, bar_guid):
        """Linhas do popup aberto a explorar. Posicao exata pela API do Corel
        (GetItemScreenRect com o menu aberto); itens ocultos voltam sem retangulo.
        Linhas sem GUID (listas dinamicas) sao achadas pela imagem do popup."""
        out, covered = [], []
        for it in (bar_items(bar_guid) if bar_guid else []):
            if it["sep"] or not it["guid"]:
                continue
            ok, x, y, w, h = au.GetItemScreenRect(bar_guid, it["guid"])
            inside = ok and rect[0] - 4 <= x and rect[1] - 4 <= y and y + h <= rect[3] + 4
            if not inside:
                self.hidden += 1
                continue
            covered.append((y, y + h))
            if it["has_sub"]:
                out.append({"x": x + 30, "y": y + h // 2, "top": y, "item": it, "label": it["caption"]})
        img = grab(rect, self.base / "_tmp.png")
        n = 0
        for yy, _ in popup_rows(img):
            ay = rect[1] + yy
            if not any(a <= ay < b for a, b in covered):
                n += 1
                out.append({"x": rect[0] + 40, "y": ay, "top": ay - ROW_H // 2, "item": None,
                            "label": f"item dinamico {n}"})
        return sorted(out, key=lambda t: t["y"])

    def hover_open(self, baseline, x, y, known, stale, timeout):
        """Passa o mouse e espera um submenu NOVO. Ignora o submenu anterior enquanto
        ele ainda esta fechando (stale = {hwnd: rect})."""
        move(x - 6, y)
        time.sleep(0.05)
        move(x, y)
        t0 = time.time()
        jig = 0
        while time.time() - t0 < timeout:
            jig += 1
            if jig % 6 == 0:  # micro-movimento: o Corel so arma o hover com WM_MOUSEMOVE
                move(x + (2 if (jig // 6) % 2 else -2), y)
            cur = popups(baseline)
            new, stale_open = [], False
            for w in cur:
                if w[0] in known:
                    continue
                if w[0] in stale and tuple(w[3]) == tuple(stale[w[0]]):
                    stale_open = True
                    continue
                new.append(w)
            if new and not stale_open:
                time.sleep(0.25)  # deixa o submenu terminar de desenhar
                return new
            time.sleep(0.05)
        return []

    def explore(self, baseline, chain, path, bar_guid):
        """chain = lista de popups (hwnd, rect) abertos; o ultimo e o que exploramos."""
        hwnd, rect = chain[-1]
        stale = {}
        for t in self.targets(rect, bar_guid):
            it, label = t["item"], t["label"] or "sem nome"
            known = {h for h, _ in chain}
            new = self.hover_open(baseline, t["x"], t["y"], known, stale, 2.0 if it else 0.9)
            if not new:
                if it:
                    self.record(path + [label], it["guid"], "sem_submenu",
                                note="tem submenu mas nao abriu (desativado neste contexto)")
                continue
            sub = max(new, key=lambda w: (w[3][2] - w[3][0]) * (w[3][3] - w[3][1]))
            sub_rect = win32gui.GetWindowRect(sub[0])
            note = ""
            if abs(sub_rect[1] - t["top"]) > 40 and abs(sub_rect[3] - t["top"] - ROW_H) > 40:
                note = "conferir: submenu longe da linha do item"
            p2 = path + [label]
            f = self.shot(p2, [r for _, r in chain] + [sub_rect])
            self.record(p2, it["guid"] if it else "", "ok", f,
                        [list(r) for _, r in chain] + [list(sub_rect)], note)
            sub_bar = ""
            if it:
                ok, sb = au.GetSubBar(it["guid"])
                sub_bar = sb if ok else ""
            self.explore(baseline, chain + [(sub[0], sub_rect)], p2, sub_bar)
            # o submenu deste item (e filhos) agora esta "velho": ignorado ate fechar
            stale = {w[0]: w[3] for w in popups(baseline) if w[0] not in known}

    def crawl_root(self, n, guid, caption):
        baseline = {t[0] for t in top_windows(pid)}
        if not force_foreground(mw):
            self.record([caption], guid, "erro", note="nao consegui trazer o Corel para frente")
            return
        ok, x, y, w, h = au.GetItemScreenRect(MENUBAR, guid)
        if not ok:
            self.record([caption], guid, "erro", note="sem retangulo na barra")
            return
        self.start_root(n, caption, (x, y, x + w, y + h))
        click(x + w / 2, y + h / 2)
        p = wait_popups(baseline, 1)
        if not p:
            self.record([caption], guid, "erro", note="menu nao abriu")
            return
        time.sleep(0.3)
        move(x + w / 2, y + h / 2)  # cursor fica no titulo do menu: sem destaque nos itens
        time.sleep(0.2)
        r = win32gui.GetWindowRect(p[0][0])
        f = self.shot([caption], [r])
        self.record([caption], guid, "ok", f, [list(r)])
        ok, sb = au.GetSubBar(guid)
        self.explore(baseline, [(p[0][0], r)], [caption], sb if ok else "")
        key(win32con.VK_ESCAPE, 4)
        time.sleep(0.3)
        if popups(baseline):
            key(win32con.VK_ESCAPE, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("menus", nargs="*")
    ap.add_argument("--context", default="doc-vazio")
    a = ap.parse_args()
    out = ROOT / "02-menus" / a.context
    out.mkdir(parents=True, exist_ok=True)
    c = Crawler(out)
    mb = app.CommandBars.Item("Menu Bar")
    want = {m.lower() for m in a.menus}
    t0 = time.time()
    for i in range(1, mb.Controls.Count + 1):
        ctl = mb.Controls.Item(i)
        cap = clean(ctl.Caption)
        if not cap or ctl.ID.lower() in SKIP_ROOTS or (want and cap.lower() not in want):
            continue
        print(f"== {cap}", flush=True)
        c.crawl_root(i, ctl.ID, cap)
    (out / "_tmp.png").unlink(missing_ok=True)
    (ROOT / "90-relatorios").mkdir(exist_ok=True)
    logf = ROOT / "90-relatorios" / f"menus_{a.context}.json"
    old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() and want else []
    keep = [r for r in old if r["path"].split(" > ")[0].lower() not in want]
    logf.write_text(json.dumps(keep + c.log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(c.log)} registros em {time.time() - t0:.0f}s -> {logf}")


if __name__ == "__main__":
    main()
