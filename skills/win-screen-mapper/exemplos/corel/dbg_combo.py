import json, subprocess, sys, time
from crawl_telas import HERE, ROOT, close_window, new_windows, pid, mw, wait_stable
from crawl_dentro import UIA
from corelui import force_foreground, grab, top_windows, win32gui
inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
g = next(x["guid"] for x in inv if x["path"] == "Tools > Options > CorelDRAW...")
force_foreground(mw)
base = {t[0] for t in top_windows(pid)}
subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "invoke_one.py"), g])
time.sleep(2.5)
h = max(new_windows(base), key=lambda t: (t[3][2]-t[3][0])*(t[3][3]-t[3][1]))[0]
u = UIA()
els = u.dump(h)
disp = next(e for e in els if e["type"] == "ListItem" and e["name"] == "Display")
u.do(h, "select", disp["key"]); time.sleep(1)
els = u.dump(h)
combos = [e for e in els if e["type"] == "ComboBox"]
print([(c["key"], c["rect"], c["enabled"]) for c in combos])
c = combos[0]
allw_before = {t[0] for t in top_windows(pid)}
print("focus", u.do(h, "focus", c["key"])); time.sleep(0.6)
c = next(e for e in u.dump(h) if e["key"] == c["key"]); print("rect agora", c["rect"])
from corelui import click
x0,y0,x1,y1 = c["rect"]; click(x1-8, (y0+y1)/2); time.sleep(0.8)
print("aberto:", [t for t in top_windows(pid) if t[0] not in allw_before])
for t in top_windows(pid):
    if t[0] not in allw_before: print("NEW", t)
# todas as janelas visiveis de qualquer processo que surgiram
import win32gui as wg
fg = wg.GetForegroundWindow(); print("fg", fg, wg.GetClassName(fg), wg.GetWindowText(fg))
els2 = u.dump(h)
print([ (e["type"], e["name"]) for e in els2 if e["type"] in ("ListItem","List") and e["parent"].startswith("ComboBox") or e["parent"].startswith("List|") and e["type"]=="ListItem" and e["name"] in ("Zoom","Scroll")])
grab(win32gui.GetWindowRect(h), ROOT / "_dbg.png")
click(x1-8, (y0+y1)/2); time.sleep(0.6)
print("depois de fechar:", [t for t in top_windows(pid) if t[0] not in allw_before])
grab(win32gui.GetWindowRect(h), ROOT / "_dbg2.png")
close_window(h)
