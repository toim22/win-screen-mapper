"""Etapa 4: explora o interior de cada tela capturada na etapa 3.

Para cada tela: abre pelo GUID, fotografa o estado inicial e entao
  - seleciona cada pagina da lista lateral de navegacao (ou cada aba) e fotografa;
  - dentro de cada pagina: abre cada caixa de combinacao (sem escolher nada) e
    rola cada lista/area com rolagem do topo ao fim, um print por "tela";
  - descarta prints repetidos (hash da imagem).
Nao clica em botoes (decisao pendente com o usuario). Fecha pelo Cancel.

Uso:
  python crawl_dentro.py                                  # todas as telas 'ok' da etapa 3
  python crawl_dentro.py --only "Tools > Options > CorelDRAW..." "File > New..."
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageChops

from crawl_telas import (HERE, ROOT, close_window, com, guard_prompts, new_windows, pid, mw,
                         wait_stable)
from corelui import click, force_foreground, grab, key, safe_name, top_windows, union, win32con, win32gui

SKIP = {
    "Tools > Scripts > Script Editor...": "editor VBA: fechar pede para fechar o documento",
    "Help > What's New?...": "nao e janela (aba Welcome Screen)",
    "Object > Rollover > Edit Rollover...": "abre a barra de ferramentas flutuante Internet (etapa 6)",
}
MAX_NAV = 60        # mais itens que isso numa lista = lista de conteudo, nao de paginas
MAX_SCROLL = 25     # paginas de rolagem por lista
MAX_COMBOS = 25     # caixas de combinacao por pagina


class UIA:
    """Cliente do uia_tool.py em modo servidor; reinicia se o processo cair."""

    def __init__(self):
        self.p = None
        self.start()

    def start(self):
        if self.p:
            try:
                self.p.kill()
            except Exception:
                pass
        self.p = subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "uia_tool.py"), "serve"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, encoding="utf-8")

    def call(self, **c):
        for attempt in range(2):
            try:
                self.p.stdin.write(json.dumps(c) + "\n")
                self.p.stdin.flush()
                line = self.p.stdout.readline()
                if line:
                    return json.loads(line)
            except Exception:
                pass
            self.start()
        return {"ok": False, "erro": "servidor UIA caiu"}

    def dump(self, hwnd):
        r = self.call(cmd="dump", hwnd=hwnd)
        return r if isinstance(r, list) else []

    def do(self, hwnd, action, key):
        return self.call(cmd="do", hwnd=hwnd, action=action, key=key)


def label_for(el, els):
    """Rotulo de uma caixa sem nome: texto mais proximo a esquerda na mesma linha, ou logo acima."""
    x0, y0, x1, y1 = el["rect"]
    cy = (y0 + y1) / 2
    best, bd = "", 1e9
    for t in els:
        if t["type"] != "Text" or not t["name"]:
            continue
        if t["parent"].split("|")[0] in ("ListItem", "TreeItem", "TabItem", "List", "Tree", "ComboBox"):
            continue  # texto de item de lista (ex.: nome de pagina), nao rotulo
        a0, b0, a1, b1 = t["rect"]
        if a1 <= x0 + 4 and b0 - 6 <= cy <= b1 + 6:
            d = x0 - a1
        elif b1 <= y0 + 4 and abs(a0 - x0) < 120:
            d = (y0 - b1) * 3 + 50
        else:
            continue
        if d < bd:
            best, bd = t["name"], d
    return best.rstrip(":").strip()


class Explorer:
    def __init__(self, uia, ctx):
        self.uia, self.ctx = uia, ctx
        self.log = []

    # ---------- captura ----------
    def shot(self, label, extra_rects=(), force=False):
        r = win32gui.GetWindowRect(self.hwnd)
        rect = union([r] + list(extra_rects))
        img = grab(rect, ROOT / "_tmp.png")
        h = hashlib.md5(img.tobytes()).hexdigest()
        if h in self.hashes and not force:
            return None
        self.hashes.add(h)
        self.n += 1
        f = self.folder / (f"{self.n:03d} " + safe_name(label, 140) + ".png")
        img.save(f)
        self.log.append({"tela": self.path, "estado": label, "imagem": str(f.relative_to(ROOT))})
        print(f"     + {label}", flush=True)
        return f

    def popups(self):
        return [t for t in new_windows(self.base) if t[0] != self.hwnd]

    def popups_all(self):
        """Inclui os popups Afx:...:808 (listas suspensas e menus do Corel)."""
        return [t for t in top_windows(pid) if t[0] not in self.base and t[0] not in (self.hwnd, mw)]

    def settle(self, t=0.5):
        time.sleep(t)
        wait_stable(self.hwnd, 3.0)

    # ---------- partes ----------
    def nav_items(self, els):
        """Itens de navegacao primaria: abas, ou lista/arvore lateral com nomes (<= MAX_NAV)."""
        tabs = [e for e in els if e["type"] == "TabItem" and e["name"] and e["enabled"]]
        groups = {}
        for e in els:
            if e["type"] in ("ListItem", "TreeItem") and e["name"] and "select" in e["patterns"]:
                groups.setdefault(e["parent"] + "|" + e["type"], []).append(e)
        lists = [g for g in groups.values() if 2 <= len(g) <= MAX_NAV and all(x["enabled"] for x in g)]
        # lista lateral de paginas: a que fica mais a esquerda
        lists.sort(key=lambda g: min(x["rect"][0] for x in g))
        return lists[0] if lists else tabs

    def explore_combos(self, prefix, els):
        """Abre cada caixa de combinacao visivel ainda nao tratada nesta pagina."""
        combos = [e for e in els if e["type"] == "ComboBox" and e["enabled"] and "expand" in e["patterns"]
                  and e["rect"][2] > e["rect"][0]][:MAX_COMBOS]
        # O Corel ignora o Expand da UIA (e fica num estado "aberto" invisivel). Entao:
        # foco (traz a caixa a vista) -> clique na seta abre -> print -> clique na seta fecha.
        for i, c in enumerate(combos, 1):
            if c["key"] in self.done_combos:
                continue
            base_name = label_for(c, els) or f"lista {i}"
            name = f"{base_name} ({c['value'][:30]})" if c.get("value") else base_name
            before = {t[0] for t in self.popups_all()}
            self.uia.do(self.hwnd, "focus", c["key"])
            time.sleep(0.4)
            r = self.uia.do(self.hwnd, "rect", c["key"])
            if not r.get("ok"):
                continue
            x0, y0, x1, y1 = r["rect"]
            dl, dt, dr, db = win32gui.GetWindowRect(self.hwnd)
            if not (dl <= x0 and x1 <= dr and dt + 30 <= y0 and y1 <= db - 50):
                self.offscreen[c["key"]] = f"{prefix}{name}: caixa fora da area visivel"
                continue
            self.done_combos.add(c["key"])
            self.offscreen.pop(c["key"], None)
            px, py = x1 - 8, (y0 + y1) / 2
            force_foreground(self.hwnd)
            click(px, py)
            pops, t0 = [], time.time()
            while time.time() - t0 < 1.5 and not pops:
                time.sleep(0.15)
                pops = [t for t in self.popups_all() if t[0] not in before]
            if not pops:
                self.skipped.append(f"{prefix}{name}: lista nao abriu")
                continue
            time.sleep(0.3)
            self.shot(f"{prefix}lista aberta ▸ {name}", [t[3] for t in pops])
            click(px, py)  # fecha sem escolher nada
            t0 = time.time()
            while time.time() - t0 < 1.5 and [t for t in self.popups_all() if t[0] not in before]:
                time.sleep(0.15)
            still = [t for t in self.popups_all() if t[0] not in before]
            if still:
                # Paleta de cor do Corel nao fecha com o 2o clique, e o Esc fecha a tela inteira:
                # fecha so o popup.
                for t in still:
                    win32gui.PostMessage(t[0], win32con.WM_CLOSE, 0, 0)
                time.sleep(0.6)
                if [t for t in self.popups_all() if t[0] not in before]:
                    key(win32con.VK_ESCAPE)  # ultimo recurso
                    time.sleep(0.4)
            if not win32gui.IsWindow(self.hwnd) or not win32gui.IsWindowVisible(self.hwnd):
                raise RuntimeError("a tela fechou ao fechar uma lista")

    def explore_scroll(self, prefix, els):
        scrollers = [e for e in els if "scroll" in e["patterns"] and e["enabled"]
                     and e["rect"][2] > e["rect"][0] and e["type"] != "ComboBox"]
        for i, s in enumerate(scrollers, 1):
            if not self.uia.do(self.hwnd, "scroll_top", s["key"]).get("ok"):
                continue
            nome = s["name"] or (f"area {i}" if len(scrollers) > 1 else "conteudo")
            for k in range(1, MAX_SCROLL + 1):
                r = self.uia.do(self.hwnd, "scroll_down", s["key"])
                if not r.get("ok"):
                    break
                time.sleep(0.4)
                if self.shot(f"{prefix}rolagem ▸ {nome} ▸ parte {k + 1}") is None:
                    break
                if self.offscreen:  # caixas que so aparecem depois de rolar
                    self.explore_combos(f"{prefix}parte {k + 1} ▸ ", self.uia.dump(self.hwnd))
            self.uia.do(self.hwnd, "scroll_top", s["key"])
            time.sleep(0.3)

    def explore_page(self, prefix, scroll=True):
        self.done_combos, self.offscreen = set(), {}
        els = self.uia.dump(self.hwnd)
        self.explore_combos(prefix, els)
        if scroll:
            self.explore_scroll(prefix, els)
        self.skipped.extend(self.offscreen.values())

    # ---------- tela ----------
    def run(self, entry):
        self.path, self.hashes, self.n, self.skipped = entry["path"], set(), 0, []
        img = Path(entry["image"])
        self.folder = ROOT / img.parent / img.stem
        self.folder.mkdir(parents=True, exist_ok=True)
        for old in self.folder.glob("*.png"):  # recomeco desta tela: substitui a rodada anterior
            old.unlink()
        if not self.open_screen(entry):
            print("   sem janela", flush=True)
            return "sem_janela"
        try:
            self.shot("inicial")
            status = self.explore_window("")
        except Exception as e:
            status = f"erro: {e}"
            print("   !!", e, flush=True)
        return self.finish(status)

    def open_screen(self, entry):
        """Abre a tela pelo GUID; define self.base e self.hwnd. False se nenhuma janela abriu.
        Telas da etapa 5 (entry["contexto"]) remontam o contexto de objeto antes de abrir."""
        if entry.get("contexto"):
            from contextos import build
            com(lambda app, au: build(app, entry["contexto"]))
        force_foreground(mw)
        self.base = {t[0] for t in top_windows(pid)}
        subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "invoke_one.py"), entry["guid"]],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wins, t0 = [], time.time()
        while time.time() - t0 < 15 and not wins:
            wins = new_windows(self.base)
            time.sleep(0.15)
        if not wins:
            return False
        w = max(wins, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
        self.hwnd = w[0]
        wait_stable(self.hwnd)
        return True

    @staticmethod
    def is_file_dialog(els):
        return bool({"Items View", "Navigation Pane"} & {e["name"] for e in els})

    def pages(self, els):
        """Itens de navegacao validados (pagina de verdade), ou []."""
        nav = self.nav_items(els)
        if nav and not self.is_real_nav(nav):
            self.skipped.append("lista com itens tratada como conteudo (selecionar nao troca de pagina)")
            nav = []
        return nav

    def explore_window(self, prefix):
        """Explora a janela self.hwnd (ja fotografada no estado inicial)."""
        els = self.uia.dump(self.hwnd)
        if self.is_file_dialog(els):
            # Seletor de arquivos do Windows: nao navega por pastas nem rola conteudo
            # (arquivos do usuario nao interessam). So as listas suspensas (tipos de arquivo).
            self.explore_page(prefix, scroll=False)
            return "ok (seletor de arquivos do Windows: so estado inicial e listas)"
        nav = self.pages(els)
        if nav:
            for it in nav:
                tipo = "aba" if it["type"] == "TabItem" else "pagina"
                if not self.uia.do(self.hwnd, "select", it["key"]).get("ok"):
                    continue
                self.settle()
                self.shot(f"{prefix}{tipo} ▸ {it['name']}", force=True)
                self.explore_page(f"{prefix}{it['name']} ▸ ")
        else:
            self.explore_page(prefix)
        return "ok"

    def is_real_nav(self, nav):
        """Pagina de verdade troca boa parte da tela; linha de lista so muda o destaque."""
        if len(nav) < 2:
            return True
        r = win32gui.GetWindowRect(self.hwnd)
        self.uia.do(self.hwnd, "select", nav[0]["key"])
        self.settle(0.3)
        a = grab(r, ROOT / "_tmp.png").convert("L")
        self.uia.do(self.hwnd, "select", nav[1]["key"])
        self.settle(0.3)
        b = grab(r, ROOT / "_tmp.png").convert("L")
        if a.size != b.size:
            return True
        diff = ImageChops.difference(a, b).point(lambda v: 255 if v > 24 else 0)
        frac = diff.histogram()[255] / (a.size[0] * a.size[1])
        return frac >= 0.04

    def finish(self, status):
        for t in self.popups():
            close_window(t[0])
        how = close_window(self.hwnd) if win32gui.IsWindow(self.hwnd) else "ja fechada"
        prompts = guard_prompts(self.base)
        left = new_windows(self.base)
        t0 = time.time()
        while left and not prompts and time.time() - t0 < 5:  # janelas sem titulo que ainda estao sumindo
            time.sleep(0.5)
            left = new_windows(self.base)
        if prompts or left or not how:
            raise SystemExit(f"!! parando: pergunta={prompts} sobrou={[t[2] for t in left]} fechou={how!r}")
        return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--context", default="doc-vazio")
    a = ap.parse_args()
    telas = json.loads((ROOT / "90-relatorios" / f"telas_{a.context}.json").read_text(encoding="utf-8"))
    todo = [t for t in telas if t["status"] == "ok" and t["path"] not in SKIP]
    if a.only:
        todo = [t for t in todo if any(t["path"].startswith(o) for o in a.only)]
    ex = Explorer(UIA(), a.context)
    resumo = []
    t0 = time.time()
    parou = None
    try:
        for entry in todo:
            print(f"== {entry['path']}", flush=True)
            n0 = len(ex.log)
            st = ex.run(entry)
            resumo.append({"tela": entry["path"], "status": st, "prints": len(ex.log) - n0,
                           "nao_capturado": ex.skipped})
            for sk in ex.skipped:
                print(f"     - {sk}", flush=True)
            com(lambda app, au: app.Documents.Count)  # mantem a conexao viva
    except SystemExit as e:  # parada de seguranca: grava o log do que ja foi feito
        parou = str(e)
        print(parou, flush=True)
    except Exception as e:  # erro inesperado: tambem grava o log antes de parar
        import traceback
        traceback.print_exc()
        parou = f"!! erro: {e}"
    (ROOT / "_tmp.png").unlink(missing_ok=True)
    logf = ROOT / "90-relatorios" / f"dentro_{a.context}.json"
    old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() else {"estados": [], "resumo": []}
    feitas = {r["tela"] for r in resumo}
    old["estados"] = [s for s in old["estados"] if s["tela"] not in feitas] + ex.log
    old["resumo"] = [s for s in old["resumo"] if s["tela"] not in feitas] + resumo
    logf.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ex.log)} prints em {time.time() - t0:.0f}s -> {logf}")
    if parou:
        raise SystemExit(parou)


if __name__ == "__main__":
    main()
