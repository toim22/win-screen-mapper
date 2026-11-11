"""Relatorio da etapa 4: por tela, quantos prints por dentro (paginas/listas/rolagem), por botoes
e por visao, e o que ficou de fora. Gera 90-relatorios/cobertura_dentro_<ctx>.csv."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
ctx = sys.argv[1] if len(sys.argv) > 1 else "doc-vazio"
R = ROOT / "90-relatorios"


def load(name):
    f = R / f"{name}_{ctx}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"estados": [], "resumo": []}


dentro, botoes, visao = load("dentro"), load("botoes"), load("visao")
telas = [t for t in json.loads((R / f"telas_{ctx}.json").read_text(encoding="utf-8")) if t["status"] == "ok"]


def count(d, tela):
    return sum(1 for s in d["estados"] if s["tela"] == tela)


def obs(d, tela, key):
    for r in d["resumo"]:
        if r["tela"] == tela:
            return [o for o in r.get(key, []) if "tratada como conteudo" not in o]
    return []


out = R / f"cobertura_dentro_{ctx}.csv"
tot = [0, 0, 0]
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["tela", "pasta", "prints_dentro", "prints_botoes", "prints_visao", "status", "observacoes"])
    for t in telas:
        p = t["path"]
        st = next((r["status"] for r in dentro["resumo"] if r["tela"] == p), "nao explorada")
        a, b, c = count(dentro, p), count(botoes, p), count(visao, p)
        tot = [tot[0] + a, tot[1] + b, tot[2] + c]
        o = obs(dentro, p, "nao_capturado") + obs(botoes, p, "observacoes") + obs(visao, p, "observacoes")
        img = Path(t["image"])
        w.writerow([p, str(img.parent / img.stem), a, b, c, st, " | ".join(o)])
print(f"{len(telas)} telas; prints: dentro={tot[0]} botoes={tot[1]} visao={tot[2]} -> {out}")
