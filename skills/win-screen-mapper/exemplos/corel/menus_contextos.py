"""Etapa 5 (menus): fotografa os menus em cada contexto, so quando o estado do menu muda.

Para cada contexto e cada menu da barra, a "assinatura" e o conjunto de itens ativos daquele
menu (matriz_contextos.json). Se a assinatura ja foi fotografada em outro contexto (ou no doc
vazio), o menu nao e repetido e o resumo registra "igual a <contexto>".

Contexto extra "sem-documento": todos os documentos fechados (barra de menus reduzida).

Saida: 02-menus/<contexto>/...   Resumo: 90-relatorios/menus_contextos.json
Uso: python menus_contextos.py [--only retangulo bitmap] [--list]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from contextos import CONTEXTOS, build, finish_editing, reset_doc
from corelui import connect

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "MAPEAMENTO"


def plano(mat):
    roots = sorted({k.split(" > ")[0] for k in mat["doc-vazio"]})
    seen = {r: {} for r in roots}
    out = {}
    for c in mat:
        out[c] = {"fotografar": [], "igual": {}}
        for r in roots:
            sig = tuple(sorted(k for k, v in mat[c].items() if v and k.startswith(r + " > ")))
            if sig in seen[r]:
                if c != "doc-vazio":
                    out[c]["igual"][r] = seen[r][sig]
                continue
            seen[r][sig] = c
            if c != "doc-vazio":
                out[c]["fotografar"].append(r)
    return out


def crawl(ctx, menus):
    r = subprocess.run([sys.executable, "-W", "ignore", "-u", str(HERE / "crawl_menus.py"), "--context", ctx, *menus],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout[-1500:], r.stderr[-800:], flush=True)
    return r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    mat = json.loads((ROOT / "90-relatorios" / "matriz_contextos.json").read_text(encoding="utf-8"))
    p = plano(mat)
    resumo_f = ROOT / "90-relatorios" / "menus_contextos.json"
    resumo = json.loads(resumo_f.read_text(encoding="utf-8")) if resumo_f.exists() else {}
    ctxs = ["sem-documento"] + list(CONTEXTOS)
    if a.only:
        ctxs = [c for c in ctxs if c in a.only]
    for c in ctxs:
        menus = "TODOS" if c == "sem-documento" else p[c]["fotografar"]
        print(f"== {c}: {menus}  iguais={p.get(c, {}).get('igual', {})}", flush=True)
    if a.list:
        return
    app, _ = connect()
    for c in ctxs:
        t0 = time.time()
        if c == "sem-documento":
            finish_editing(app)
            while app.Documents.Count:
                d = app.Documents.Item(1)
                d.Dirty = False
                d.Close()
                time.sleep(0.5)
            time.sleep(2)
            rc = crawl(c, [])
            resumo[c] = {"fotografados": "todos", "iguais": {}, "rc": rc}
        else:
            if not p[c]["fotografar"]:
                resumo[c] = {"fotografados": [], "iguais": p[c]["igual"], "rc": 0}
                continue
            # o Esc que fecha cada menu tambem tira a selecao: remonta o contexto antes de cada menu
            rc = 0
            for r in p[c]["fotografar"]:
                build(app, c)
                rc = rc or crawl(c, [r])
            resumo[c] = {"fotografados": p[c]["fotografar"], "iguais": p[c]["igual"], "rc": rc}
        resumo_f.write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"   {c} em {time.time() - t0:.0f}s rc={rc}", flush=True)
        if rc:
            raise SystemExit(f"!! crawl_menus falhou em {c}")
    reset_doc(app)
    print("titulo:", app.ActiveDocument.Title)


if __name__ == "__main__":
    main()
