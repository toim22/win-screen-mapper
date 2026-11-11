"""restart_app_modelo.py: reinicia o app e o deixa no ESTADO BASE. Copie como restart_app.py e ajuste.

Escreva isto no 1o dia (no Corel ele so veio depois da 1a queda). Regras:
- documento de teste: descartar sem gravar pela automacao do app (Corel: doc.Dirty=False; doc.Close());
  WM_CLOSE com documento alterado abriu direto o "Save Drawing";
- pergunta "Save changes?" ao fechar: so o documento descartavel e aprovado pelo usuario pode receber
  No/Don't Save; qualquer outra janela inesperada PARA o script;
- aviso de trial: botao Close (nunca BUY NOW);
- Crash Report na reabertura: fechar pelo X (WM_CLOSE). O OK ENVIA o relatorio;
- estado base no fim (Corel: File > New > OK, porque sem documento varios menus somem);
- imprime "pronto" no fim (o adaptador procura essa palavra).

Uso: python restart_app.py [--no-close]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import projeto
import winui as w

P = projeto.carregar(precisa_app=False)            # exe, caminho_exe e classe_principal vem do app.json
EXE = P.cfg["caminho_exe"]
AQUI = Path(__file__).resolve().parent
CLASSE_PRINCIPAL = P.cfg.get("classe_principal", "")
ESPERA_CARREGAR = P.cfg.get("espera_carregar", 15)  # s depois da janela aparecer (tela inicial, addons)


def uia(*args):
    out = subprocess.run([sys.executable, "-W", "ignore", str(AQUI / "uia_tool.py"), *map(str, args)],
                         capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out) if out.strip() else None


def janela_principal(pid):
    return w.main_window(pid)  # usa classe_principal do app.json se houver, senao o titulo


def descartar_documentos():
    """AJUSTE: feche os documentos de teste pela automacao do app, sem gravar."""
    # from win32com.client import gencache
    # app = gencache.EnsureDispatch("App.Application")   # cuidado: com o app fechado isto ABRE um fantasma
    # while app.Documents.Count: d = app.Documents.Item(1); d.Dirty = False; d.Close()
    pass


def fechar_app():
    pid = w.app_pid()
    if not pid:
        return
    try:
        descartar_documentos()
    except Exception as e:
        print("automacao falhou ao fechar documento:", e)
    mw0 = janela_principal(pid)
    w.fechar_janela(mw0)
    t0 = time.time()
    while time.time() - t0 < 60:
        if not w.app_pid():
            print("app fechado")
            return
        for h, cls, title, _ in w.top_windows(pid):
            if h == mw0:
                continue
            els = uia("dump", h) or []
            texto = " ".join(e["name"] for e in els if e["type"] == "Text").lower()
            nao = [e["key"] for e in els if e["type"] == "Button" and e["name"] in ("No", "Não", "Don't Save")]
            if nao and "save" in texto:
                print(f"pergunta '{title}' (documento descartavel) -> No")
                uia("do", h, "invoke", nao[0])
            elif "trial" in texto and any(e["name"] == "Close" for e in els if e["type"] == "Button"):
                uia("do", h, "invoke", next(e["key"] for e in els if e["type"] == "Button" and e["name"] == "Close"))
            elif els:
                raise SystemExit(f"!! janela inesperada ao fechar: {title!r} {texto[:120]!r}")
        time.sleep(1)
    raise SystemExit("!! o app nao fechou em 60s")


def abrir_app():
    subprocess.Popen([EXE], close_fds=True)
    t0, mw = time.time(), None
    while time.time() - t0 < 180:
        pid = w.app_pid()
        mw = pid and janela_principal(pid)
        if mw and w.win32gui.IsWindowVisible(mw):
            break
        time.sleep(1)
    if not mw:
        raise SystemExit("!! o app nao abriu")
    w.win32gui.ShowWindow(mw, w.win32con.SW_MAXIMIZE)
    time.sleep(ESPERA_CARREGAR)
    pid = w.app_pid()
    mw = janela_principal(pid)
    for h, cls, title, _ in w.top_windows(pid):
        if h != mw:
            print("janela extra ao abrir (fechando pelo X, sem enviar nada):", cls, title)
            w.fechar_janela(h)
    return pid


def estado_base(pid):
    """AJUSTE: deixe o app como as rodadas esperam (ex.: documento novo em branco)."""
    pass


if __name__ == "__main__":
    if "--no-close" not in sys.argv:
        fechar_app()
        time.sleep(3)
    estado_base(abrir_app())
    print("pronto")
