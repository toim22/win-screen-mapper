"""Chama Automation.InvokeItem(guid) e sai. Roda em processo separado porque
dialogos modais bloqueiam a chamada COM ate serem fechados."""
import sys

from win32com.client import gencache

app = gencache.EnsureDispatch("CorelDRAW.Application.27")
mode = sys.argv[2] if len(sys.argv) > 2 else "invoke"
try:
    if mode == "invoke":
        app.FrameWork.Automation.InvokeItem(sys.argv[1])
    elif mode == "dialog":
        app.FrameWork.ShowDialog(sys.argv[1])
    elif mode == "docker":
        app.FrameWork.ShowDocker(sys.argv[1])
    print("returned")
except Exception as e:
    print("error", e)
    sys.exit(2)
