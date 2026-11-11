"""Abre uma tela pelo caminho do menu, faz o dump UIA, salva em scratch e fecha pelo Cancel.
Uso: python probe_tela.py "File > New..." <pasta_saida>"""
import json
import subprocess
import sys
import time
from pathlib import Path

from corelui import corel_pid, force_foreground, main_window, top_windows, win32gui

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "MAPEAMENTO"
inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
path, outdir = sys.argv[1], Path(sys.argv[2])
g = next(x["guid"] for x in inv if x["path"] == path)
pid = corel_pid()
mw = main_window(pid)
force_foreground(mw)
base = {t[0] for t in top_windows(pid)}
subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "invoke_one.py"), g],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = None
for _ in range(60):
    w = [t for t in top_windows(pid) if t[0] not in base and not t[1].startswith("Afx:")]
    if w:
        win = max(w, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
        break
    time.sleep(0.15)
if not win:
    print("sem janela")
    sys.exit(1)
time.sleep(1.5)
out = subprocess.run([sys.executable, "-W", "ignore", str(HERE / "uia_tool.py"), "dump", str(win[0])],
                     capture_output=True, text=True).stdout
els = json.loads(out)
safe = path.replace(">", "_").replace(".", "").replace(" ", "")
(outdir / f"dump_{safe}.json").write_text(out, encoding="utf-8")
from collections import Counter
print(path, "->", win[2], win[1], "| elementos:", len(els), Counter(e["type"] for e in els).most_common(12))
for e in els:
    if e["type"] in ("TabItem", "TreeItem", "ComboBox", "Hyperlink", "SplitButton") or \
       (e["type"] == "ListItem") or (e["type"] == "Button" and e["name"]) or "scroll" in e["patterns"]:
        print(f"   {e['type']:10} {e['name'][:50]!r:52} {e['patterns']} parent={e['parent'][:40]} en={e['enabled']}")
subprocess.run([sys.executable, "-W", "ignore", str(HERE / "close_one.py"), str(win[0])])
time.sleep(0.8)
print("aberta ainda:", win32gui.IsWindow(win[0]) and win32gui.IsWindowVisible(win[0]))
