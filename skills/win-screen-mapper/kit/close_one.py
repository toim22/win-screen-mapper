"""Fecha uma janela pelo botao Cancel (ou Close, se nao houver Cancel) via UI Automation.
Roda isolado porque pywinauto/comtypes no Python 3.15 pode derrubar o processo.
Uso: python close_one.py <hwnd> [--info]
  sem --info: imprime o nome do botao usado, ou nada.
  --info: so lista os botoes (nao clica)."""
import sys
import warnings

warnings.filterwarnings("ignore")
from pywinauto import Desktop

PRIORITY = ("Cancel", "Cancelar", "Close", "Fechar")
hwnd = int(sys.argv[1])
d = Desktop(backend="uia").window(handle=hwnd)
buttons = {}
for b in d.descendants(control_type="Button"):
    name = b.window_text().strip()
    if name and b.rectangle().width() > 0:
        buttons.setdefault(name, b)
if "--info" in sys.argv:
    print("|".join(buttons))
    sys.exit(0)
for name in PRIORITY:
    if name in buttons:
        buttons[name].invoke()
        print(name)
        break
