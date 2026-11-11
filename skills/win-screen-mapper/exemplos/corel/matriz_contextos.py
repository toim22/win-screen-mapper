"""Etapa 5: matriz de habilitacao. Para cada contexto, pergunta ao Corel (IsEnabled) se cada
item de menu do inventario esta ativo. Nao abre nada.

Saida: 90-relatorios/matriz_contextos.json e .csv (linha = item de menu, coluna = contexto)
Uso: python matriz_contextos.py
"""
import csv
import json

from contextos import CONTEXTOS, build, reset_doc
from corelui import connect

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
itens = [x for x in inv if x["kind"] == "menu_item" and not x["path"].startswith(("<", "Purchase"))]
app, au = connect()


def estado():
    out = {}
    for x in itens:
        try:
            out[x["path"]] = bool(au.IsEnabled(x["guid"]))
        except Exception:
            out[x["path"]] = None
    return out


mat = {}
reset_doc(app)
mat["doc-vazio"] = estado()
for c in CONTEXTOS:
    build(app, c)
    mat[c] = estado()
    print(f"{c:18s} ativos={sum(1 for v in mat[c].values() if v)} (doc-vazio={sum(1 for v in mat['doc-vazio'].values() if v)})",
          flush=True)
reset_doc(app)
(ROOT / "90-relatorios" / "matriz_contextos.json").write_text(json.dumps(mat, ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
cols = list(mat)
with (ROOT / "90-relatorios" / "matriz_contextos.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["item de menu"] + cols)
    for x in itens:
        w.writerow([x["path"]] + [{True: "sim", False: "-", None: "?"}[mat[c][x["path"]]] for c in cols])
print("ok")
