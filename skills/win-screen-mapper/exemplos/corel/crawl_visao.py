"""Etapa 4c: controles desenhados pelo Corel que a automacao do Windows nao enxerga.

Os alvos foram marcados olhando os prints (visao) e ficam em visao_alvos.json:
  {"tela": "File > New...", "pagina": null, "nome": "aba Templates", "x": 170, "y": 52,
   "desfazer": false}
x, y = posicao relativa ao canto superior esquerdo da janela (igual ao print "inicial").
pagina = nome do item da lista lateral/aba a selecionar antes (ou null).
desfazer = clicar de novo depois (ex.: caixa de selecao, ou fechar paleta de cor sem usar Esc).
explorar = false: so fotografa o que abriu (paletas de cor: Esc nelas fecha a tela inteira).

Para cada alvo: clica; se abrir janela, explora a janela filha; se abrir menu/lista, fotografa e
fecha com Esc; se so mudar a tela (aba, caixa marcada), fotografa e explora as listas/rolagem do
novo estado. Fecha a tela pelo Cancel no fim (o Cancel desfaz qualquer mudanca).

Saida: <pasta da tela>/visao/NNN ...png     Log: 90-relatorios/visao_<ctx>.json
Uso: python crawl_visao.py [--only "File > New..."]
"""
import argparse
import json
import time
from pathlib import Path

from crawl_botoes import ButtonExplorer
from crawl_dentro import UIA
from crawl_telas import HERE, ROOT, com
from corelui import win32gui


def run_targets(ex, entry, targets):
    ex.path, ex.hashes, ex.n, ex.skipped = entry["path"], set(), 0, []
    img = Path(entry["image"])
    ex.folder = ROOT / img.parent / img.stem / "visao"
    ex.folder.mkdir(parents=True, exist_ok=True)
    for old in ex.folder.glob("*.png"):
        old.unlink()
    if not ex.open_screen(entry):
        return "sem_janela"
    ex.docs = com(lambda a, u: a.Documents.Count)
    status = "ok"
    try:
        for t in targets:
            it = None
            if t.get("pagina"):
                els = ex.uia.dump(ex.hwnd)
                it = next((e for e in els if e["type"] in ("ListItem", "TreeItem", "TabItem")
                           and e["name"] == t["pagina"]), None)
                if not it or not ex.uia.do(ex.hwnd, "select", it["key"]).get("ok"):
                    ex.skipped.append(f"{t['nome']}: pagina {t['pagina']!r} nao encontrada")
                    continue
                ex.settle()
            l, tp, _, _ = win32gui.GetWindowRect(ex.hwnd)
            x, y = l + t["x"], tp + t["y"]
            rect = [x - 1, y - 1, x + 1, y + 1]
            prefix = f"{t['pagina']} ▸ " if t.get("pagina") else ""
            ex.press(prefix, {"name": t["nome"], "type": "Visao", "patterns": []}, it, rect=rect,
                     label=f"{prefix}{t['nome']}", explore_change=t.get("explorar", True))
            if t.get("desfazer"):
                from corelui import click
                click(x, y)
                ex.settle(0.3)
    except Exception as e:
        status = f"erro: {e}"
        print("   !!", e, flush=True)
    return ex.finish(status)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--context", default="doc-vazio")
    a = ap.parse_args()
    alvos = json.loads((HERE / "visao_alvos.json").read_text(encoding="utf-8"))
    telas = {t["path"]: t for t in json.loads(
        (ROOT / "90-relatorios" / f"telas_{a.context}.json").read_text(encoding="utf-8"))}
    por_tela = {}
    for t in alvos:
        por_tela.setdefault(t["tela"], []).append(t)
    if a.only:
        por_tela = {k: v for k, v in por_tela.items() if any(k.startswith(o) for o in a.only)}
    ex = ButtonExplorer(UIA(), a.context)
    resumo, t0 = [], time.time()
    parou = None
    try:
        for path, targets in por_tela.items():
            print(f"== {path}", flush=True)
            n0 = len(ex.log)
            st = run_targets(ex, telas[path], targets)
            for sk in ex.skipped:
                print(f"     - {sk}", flush=True)
            resumo.append({"tela": path, "status": st, "prints": len(ex.log) - n0, "observacoes": ex.skipped})
    except SystemExit as e:  # parada de seguranca: grava o log do que ja foi feito
        parou = str(e)
        print(parou, flush=True)
    (ROOT / "_tmp.png").unlink(missing_ok=True)
    logf = ROOT / "90-relatorios" / f"visao_{a.context}.json"
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
