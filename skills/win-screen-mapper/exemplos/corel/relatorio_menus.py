"""Relatorio de cobertura dos menus: cada item com submenu do inventario e o que aconteceu.

Uso: python relatorio_menus.py [contexto]   (padrao: doc-vazio)
Saida: MAPEAMENTO/90-relatorios/cobertura_menus_<contexto>.csv
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
ctx = sys.argv[1] if len(sys.argv) > 1 else "doc-vazio"
inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
log = json.loads((ROOT / "90-relatorios" / f"menus_{ctx}.json").read_text(encoding="utf-8"))
by_guid = {}
for r in log:
    if r["guid"]:
        by_guid.setdefault(r["guid"].lower(), r)

DEBUG_ROOT = "67cfe9c0"
rows = []
for x in inv:
    if x["kind"] not in ("menu_root", "menu_item") or not x["has_submenu"]:
        continue
    r = by_guid.get(x["guid"].lower())
    if x["path"].startswith("<" + DEBUG_ROOT):
        status, motivo, img = "fora_do_escopo", "menu Debug oculto (so aparece com depuracao interna ligada)", ""
    elif r and r["status"] == "ok":
        status, motivo, img = "ok", r.get("note", ""), r["image"]
    elif r:
        status, motivo, img = r["status"], r.get("note", ""), ""
    else:
        status, motivo, img = "oculto", "item existe no inventario mas nao aparece no menu", ""
    rows.append({"caminho": x["path"], "guid": x["guid"], "status": status, "motivo": motivo, "imagem": img})
# itens dinamicos (sem GUID) que abriram submenu
for r in log:
    if not r["guid"] and r["status"] == "ok":
        rows.append({"caminho": r["path"], "guid": "", "status": "ok",
                     "motivo": "item de lista dinamica (sem GUID)", "imagem": r["image"]})

out = ROOT / "90-relatorios" / f"cobertura_menus_{ctx}.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["caminho", "status", "motivo", "imagem", "guid"])
    w.writeheader()
    w.writerows(rows)
from collections import Counter
print(out)
for k, v in Counter(r["status"] for r in rows).items():
    print(f"  {k}: {v}")
