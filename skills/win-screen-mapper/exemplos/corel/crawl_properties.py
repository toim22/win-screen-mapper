"""Etapa 6e: abas do docker Properties em alguns contextos.

As abas sao icones desenhados pelo Corel (invisiveis para a automacao do Windows). O script
acha os icones pela imagem na faixa das abas (topo do painel, grupo da esquerda; os 2 botoes
da direita nao sao abas e nao sao clicados), clica em cada um e fotografa a aba, com as partes
de rolagem. So clica nas abas e rola: nao altera nada no objeto.

Saida: 04-dockers/properties-abas/<contexto>/NN aba K.png   Log: 90-relatorios/properties_abas.json
Uso: python crawl_properties.py [retangulo texto-artistico ...]
"""
import json
import sys
import time

from PIL import Image

import crawl_telas as ct
from contextos import build, reset_doc
from corelui import click, force_foreground, grab, key, win32con
from crawl_dockers import invoke, kids, scroll_parts

ROOT = ct.ROOT
PROPS = "Window > Dockers > Properties"
TAB_Y = 44          # centro da faixa das abas, relativo ao topo do painel
TAB_MAX_X = 228     # abas ficam a esquerda disto; a direita ficam 2 botoes de exibicao
CONTEXTOS = ["retangulo", "texto-artistico", "texto-paragrafo", "bitmap", "tabela"]


def tab_centers(img):
    """Centros x dos icones na faixa das abas (agrupa colunas que diferem do fundo)."""
    im = img.convert("RGB")
    px = im.load()
    bg = px[TAB_MAX_X - 4, TAB_Y - 14]
    cols = []
    for x in range(2, min(TAB_MAX_X, im.width)):
        hit = any(sum(abs(a - b) for a, b in zip(px[x, y], bg)) > 90 for y in range(TAB_Y - 9, TAB_Y + 9))
        cols.append(hit)
    centers, start = [], None
    for i, h in enumerate(cols + [False]):
        if h and start is None:
            start = i
        elif not h and start is not None:
            if i - start >= 6:
                centers.append(2 + (start + i - 1) // 2)
            start = None
    return centers


def main():
    ctxs = sys.argv[1:] or CONTEXTOS
    inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
    guid = next(x["guid"] for x in inv if x["kind"] == "menu_item" and x["path"] == PROPS)
    log = []
    for ctx in ctxs:
        out = ROOT / "04-dockers" / "properties-abas" / ctx
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.png"):
            old.unlink()
        ct.com(lambda app, au: build(app, ctx))
        force_foreground(ct.mw)
        k0, w0 = kids(), {t[0] for t in ct.top_windows(ct.pid)}
        invoke(guid)
        time.sleep(2.5)
        hosts = [v[1] for h, v in kids().items() if h not in k0 and v[0] == "ViewHost"]
        if not hosts:
            print(f"!! {ctx}: painel do Properties nao apareceu", flush=True)
            log.append({"contexto": ctx, "status": "sem_painel"})
            continue
        r = max(hosts, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
        first = grab(r, out / "00 aberto.png")
        tabs = tab_centers(first)
        print(f"== {ctx}: {len(tabs)} abas em x={tabs}", flush=True)
        for k, tx in enumerate(tabs, 1):
            click(r[0] + tx, r[1] + TAB_Y)
            time.sleep(0.4)
            from corelui import move
            move(r[0] - 150, r[1] + 300)  # tira o mouse: a dica (tooltip) da aba cobria o titulo
            time.sleep(1.2)
            img = grab(r, out / f"{k:02d} aba {k}.png")
            partes = scroll_parts(r, img, out, f"{k:02d} aba {k}")
            log.append({"contexto": ctx, "aba": k, "x": tx, "partes": partes, "status": "ok",
                        "image": str((out / f"{k:02d} aba {k}.png").relative_to(ROOT))})
            print(f"  [ok] aba {k} (x={tx}) partes={partes}", flush=True)
            extra = [t for t in ct.new_windows(w0) if t[1] not in ("SysShadow", "tooltips_class32")]
            if extra:
                raise SystemExit(f"!! clicar a aba {k} em {ctx} abriu janela: {[t[2] for t in extra]}")
        invoke(guid)  # fecha o docker
        time.sleep(1.5)
        key(win32con.VK_ESCAPE)
    (ROOT / "_tmp.png").unlink(missing_ok=True)
    f = ROOT / "90-relatorios" / "properties_abas.json"
    old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    f.write_text(json.dumps([r for r in old if r["contexto"] not in ctxs] + log, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    ct.com(lambda app, au: reset_doc(app))


if __name__ == "__main__":
    main()
