"""Relatorio da etapa 5.

cobertura_contextos.csv: cada tela que estava desativada no documento vazio -> em que contexto
abriu, o que aconteceu (janela, docker, so mudou a tela), print e prints por dentro.
menus_contextos.csv: por contexto, quais menus foram fotografados e quais ficaram iguais a outro.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
R = ROOT / "90-relatorios"
telas = json.loads((R / "telas_contextos.json").read_text(encoding="utf-8"))
dentro = json.loads((R / "dentro_contextos.json").read_text(encoding="utf-8"))
menus = json.loads((R / "menus_contextos.json").read_text(encoding="utf-8"))
STATUS = {"ok": "abriu janela", "docker": "abre no docker (sem janela)",
          "sem_janela": "sem janela (muda a tela / entra num modo)", "desativado": "desativado em todos os contextos",
          "nao_aberto": "nao aberto (lista negra)"}

n = {}
with (R / "cobertura_contextos.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["tela", "contexto", "resultado", "print", "prints_dentro", "observacao"])
    for t in telas:
        pd = sum(1 for s in dentro["estados"] if s["tela"] == t["path"])
        n[t["status"]] = n.get(t["status"], 0) + 1
        w.writerow([t["path"], t["contexto"], STATUS.get(t["status"], t["status"]), t["image"], pd, t["note"]])

with (R / "menus_contextos.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["contexto", "menus fotografados", "prints", "menus iguais a outro contexto"])
    for c, v in menus.items():
        mf = R / f"menus_{c}.json"
        k = sum(1 for x in json.loads(mf.read_text(encoding="utf-8")) if x["status"] == "ok") if mf.exists() else 0
        fot = v["fotografados"] if isinstance(v["fotografados"], str) else ", ".join(v["fotografados"])
        w.writerow([c, fot, k, ", ".join(f"{m} = {o}" for m, o in v["iguais"].items())])

print("telas:", n, "| prints por dentro:", len(dentro["estados"]))
