"""Reinicia o CorelDRAW e deixa um documento em branco (File > New > OK).

Sem documento aberto o Corel encolhe a barra de menus, entao o passo do File > New e obrigatorio.
Ao fechar, a pergunta "Save changes to Untitled-N?" e respondida com No (documento descartavel,
aprovado pelo usuario). Qualquer outra pergunta para o script.

Uso: python restart_corel.py [--no-close]   (--no-close: so abre e cria o documento)
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from corelui import corel_pid, top_windows, win32con, win32gui

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "MAPEAMENTO"
EXE = r"C:\Program Files\Corel\CorelDRAW Graphics Suite\27\Programs64\CorelDRW.exe"
inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
NEW = next(x["guid"] for x in inv if x["path"] == "File > New...")


def uia(*args):
    out = subprocess.run([sys.executable, "-W", "ignore", str(HERE / "uia_tool.py"), *map(str, args)],
                         capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out) if out.strip() else None


def main_win(pid):
    for t in top_windows(pid):
        if t[1] == "CorelDRAW27":
            return t[0]
    return None


def close_corel():
    pid = corel_pid()
    if not pid:
        return
    mw = main_win(pid)
    # Descarta os documentos de teste sem perguntar (WM_CLOSE com documento alterado
    # abriu direto o "Save Drawing"): marca como nao alterado e fecha pela automacao.
    from corelui import connect
    app, _ = connect()
    try:
        while app.Documents.Count:
            d = app.Documents.Item(1)
            print("descartando documento", d.Title)
            d.Dirty = False
            d.Close()
            time.sleep(1)
    except Exception as e:  # Corel inconsistente: segue pelo WM_CLOSE (a pergunta de salvar recebe No)
        print("automacao falhou ao fechar documento:", e)
    del app
    print("fechando Corel", pid)
    win32gui.PostMessage(mw, win32con.WM_CLOSE, 0, 0)
    t0 = time.time()
    while time.time() - t0 < 60:
        if not corel_pid():
            print("Corel fechado")
            return
        for h, cls, title, _ in top_windows(pid):
            if cls == "CorelDRAW27" or cls.startswith("CorelDRAW27-Frame"):
                continue  # janela principal e barras de ferramentas flutuantes (ex.: Internet)
            els = uia("dump", h) or []
            texts = " ".join(e["name"] for e in els if e["type"] == "Text")
            btns = [e["key"] for e in els if e["type"] == "Button" and e["name"] in ("No", "Não", "Don't Save")]
            if btns and ("Save changes" in texts or "save" in texts.lower()):
                print(f"pergunta '{title}': {texts[:80]!r} -> No")
                uia("do", h, "invoke", btns[0])
            elif "trial" in texts.lower() and any(e["key"] == "Button|Close|1" for e in els):
                print(f"aviso do trial '{title}' -> Close")
                uia("do", h, "invoke", "Button|Close|1")
            elif els:
                raise SystemExit(f"!! janela inesperada ao fechar: {title!r} {texts[:120]!r}")
        time.sleep(1)
    raise SystemExit("!! Corel nao fechou em 60s")


def open_corel():
    subprocess.Popen([EXE], close_fds=True)
    t0 = time.time()
    mw = None
    while time.time() - t0 < 180:
        pid = corel_pid()
        mw = pid and main_win(pid)
        if mw and win32gui.IsWindowVisible(mw):
            break
        time.sleep(1)
    if not mw:
        raise SystemExit("!! Corel nao abriu")
    print("janela principal", hex(mw))
    win32gui.ShowWindow(mw, win32con.SW_MAXIMIZE)
    time.sleep(15)  # carregamento da Welcome Screen / addons
    pid = corel_pid()
    # fecha janelas extras (ex.: aviso de versao de avaliacao) pelo Esc/Cancel
    for h, cls, title, _ in top_windows(pid):
        if cls not in ("CorelDRAW27",) and not cls.startswith("Afx:"):
            print("janela extra ao abrir:", cls, title)
            # Crash Report: o OK envia o relatorio; fecha pelo X (nao envia nada)
            try:
                win32gui.PostMessage(h, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass  # ja sumiu
            time.sleep(1.5)
    return pid


def new_document(pid):
    from corelui import force_foreground
    force_foreground(main_win(pid))
    base = {t[0] for t in top_windows(pid)}
    subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "invoke_one.py"), NEW],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    win, t0 = None, time.time()
    while time.time() - t0 < 30 and not win:
        w = [t for t in top_windows(pid) if t[0] not in base and not t[1].startswith("Afx:")]
        win = w[0][0] if w else None
        time.sleep(0.3)
    if not win:
        raise SystemExit("!! File > New nao abriu")
    time.sleep(2)
    print("File > New:", win32gui.GetWindowText(win), "-> OK")
    r = uia("do", win, "invoke", "Button|OK|1")
    if not (r and r.get("ok")):
        raise SystemExit(f"!! nao achei o OK do File > New: {r}")
    time.sleep(3)
    title = win32gui.GetWindowText(main_win(pid))
    print("titulo:", title)
    if "Untitled" not in title:
        raise SystemExit("!! documento em branco nao apareceu")


if __name__ == "__main__":
    if "--no-close" not in sys.argv:
        close_corel()
        time.sleep(3)
    p = open_corel()
    new_document(p)
    print("pronto")
