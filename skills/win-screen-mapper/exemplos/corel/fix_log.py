"""Correcao pontual do log de telas (doc-vazio): caminho da imagem do What's New."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
p = ROOT / "90-relatorios" / "telas_doc-vazio.json"
r = json.loads(p.read_text(encoding="utf-8"))
img = next((ROOT / "03-telas" / "doc-vazio" / "12 Help").glob("005 *What*New*.png"))
for x in r:
    if x["path"] == "Help > What's New?...":
        x["image"] = str(img.relative_to(ROOT))
p.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
print(img.name)
