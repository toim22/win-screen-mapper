"""Relatorio de cobertura das telas (etapa 3).

Uso: python relatorio_telas.py [contexto]   (padrao: doc-vazio)
Saida: MAPEAMENTO/90-relatorios/cobertura_telas_<contexto>.csv
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
ctx = sys.argv[1] if len(sys.argv) > 1 else "doc-vazio"
log = json.loads((ROOT / "90-relatorios" / f"telas_{ctx}.json").read_text(encoding="utf-8"))
STATUS_PT = {
    "ok": "capturada",
    "desativado": "desativado neste contexto (fica para a etapa 5, com objetos selecionados)",
    "nao_aberto": "nao aberta de proposito",
    "sem_janela": "o comando nao abre janela",
}
rows, missing = [], []
for r in log:
    img = r.get("image", "")
    if r["status"] == "ok" and img and not (ROOT / img).exists():
        missing.append(r["path"])
    rows.append({"caminho": r["path"], "status": r["status"], "significado": STATUS_PT.get(r["status"], ""),
                 "titulo_da_janela": r.get("window_title", ""), "motivo_ou_nota": r.get("note", ""),
                 "imagem": img, "guid": r["guid"]})
out = ROOT / "90-relatorios" / f"cobertura_telas_{ctx}.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(out)
for k, v in Counter(r["status"] for r in rows).items():
    print(f"  {k}: {v}")
print("ok sem arquivo:", missing)
