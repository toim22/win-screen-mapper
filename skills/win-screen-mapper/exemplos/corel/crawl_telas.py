"""Etapa 3: abre cada item de menu que gera uma janela, fotografa e fecha pelo Cancel.

Uso:
  python crawl_telas.py                       # todos os candidatos habilitados
  python crawl_telas.py --only "Tools > Options" "File > New..."   # filtro por prefixo do caminho
  python crawl_telas.py --context doc-vazio --list                 # so lista, nao abre nada

Nunca clica em OK/Apply/Save: fecha por Cancel, depois botao fechar da janela (WM_CLOSE), depois Esc.
Se uma janela nao fechar, o script para (para nao acumular janelas abertas).
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from corelui import (connect, corel_pid, force_foreground, grab, key, main_window, safe_name,
                     top_windows, win32con, win32gui)

ROOT = Path(__file__).resolve().parent.parent / "MAPEAMENTO"
HERE = Path(__file__).resolve().parent

# Lista negra aprovada pelo usuario (2026-11-08) + conta/login + programas externos.
BLACKLIST = {
    "File > Save...": "lista negra: salvar",
    "File > Save As...": "lista negra: salvar",
    "File > Save to Cloud...": "lista negra: salvar / conta Corel",
    "File > Open from Cloud...": "lista negra: conta Corel (login)",
    "Tools > Save Settings as Default...": "lista negra: altera configuracao padrao",
    "Tools > Scripts > Visual Studio Editor...": "abre programa externo (Visual Studio)",
    # 2026-11-08: fechar o editor VBA disparou "Save changes to Untitled-1?". Print ja feito.
    "Tools > Scripts > Script Editor...": "fechar o editor VBA pede para fechar o documento (print ja feito)",
    "Help > Updates...": "lista negra: atualizacoes",
    "Help > Account Settings...": "lista negra: conta Corel",
    "Help > Restore Purchases...": "lista negra: conta/compra",
}
BLACK_WORDS = ("Exit", "Close", "Print", "Export", "Publish", "Recording", "Temporary Script", "Purchase")
# Provavelmente abrem o navegador: pendentes de decisao do usuario.
WEB = {
    "Help > Product Help...", "Help > Video Tutorials...", "Help > Quick Start Guide...",
    "Help > User Guide...", "Help > Corel Support...", "Help > Submit Ideas and Feedback...",
}
CLOSE_NAMES = ("Cancel", "Close", "Fechar", "Cancelar")

app, au = connect()
pid = corel_pid()
mw = main_window(pid)


def com(fn):
    """Chama fn(app, au); se a conexao COM caiu, reconecta e tenta de novo."""
    global app, au
    try:
        return fn(app, au)
    except Exception:
        time.sleep(0.5)
        app, au = connect()
        return fn(app, au)


def candidates(inv):
    out = []
    for x in inv:
        if x["kind"] != "menu_item" or x["has_submenu"] or not x["opens_dialog_hint"]:
            continue
        p = x["path"]
        if p.startswith("<") or p.startswith("Purchase"):
            continue
        reason = BLACKLIST.get(p)
        if not reason and any(w in p.split(" > ")[-1] for w in BLACK_WORDS):
            reason = "lista negra: " + p.split(" > ")[-1]
        if not reason and p in WEB:
            reason = "pendente: provavelmente abre o navegador"
        out.append((x, reason))
    return out


def new_windows(base):
    return [t for t in top_windows(pid) if t[0] not in base and t[0] != mw
            and not t[1].startswith("Afx:")]  # Afx:...:808 = popups de menu


def img_hash(rect):
    im = grab(rect, ROOT / "_tmp.png")
    return hashlib.md5(im.tobytes()).hexdigest()


def wait_stable(hwnd, timeout=6.0):
    """Espera retangulo e conteudo pararem de mudar."""
    t0, last = time.time(), None
    while time.time() - t0 < timeout:
        if not win32gui.IsWindow(hwnd):
            return False
        r = win32gui.GetWindowRect(hwnd)
        cur = (r, img_hash(r))
        if cur == last:
            return True
        last = cur
        time.sleep(0.4)
    return True


def close_window(hwnd):
    """Cancel -> WM_CLOSE -> Esc. Devolve o metodo que funcionou ou ''."""
    if not win32gui.IsWindow(hwnd):
        return "ja fechada"
    try:
        out = subprocess.run([sys.executable, "-W", "ignore", str(HERE / "close_one.py"), str(hwnd)],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        if out and gone(hwnd):
            return f"botao {out}"
    except Exception:
        pass
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    except Exception:  # sumiu entre a checagem e o PostMessage
        return "ja fechada"
    if gone(hwnd):
        return "WM_CLOSE"
    force_foreground(hwnd)
    key(win32con.VK_ESCAPE)
    if gone(hwnd):
        return "Esc"
    return ""


def is_prompt(hwnd):
    """Pergunta de confirmacao do Corel (ex.: 'Save changes to ...?'): tem Yes, No e Cancel."""
    try:
        out = subprocess.run([sys.executable, "-W", "ignore", str(HERE / "close_one.py"), str(hwnd), "--info"],
                             capture_output=True, text=True, timeout=20).stdout.strip().split("|")
    except Exception:
        return False
    return {"Yes", "No", "Cancel"} <= set(out)


def guard_prompts(base):
    """Rede de seguranca: qualquer pergunta Yes/No/Cancel nova e respondida com Cancel."""
    hit = []
    for t in new_windows(base):
        if t[1] == "#32770" and is_prompt(t[0]):
            subprocess.run([sys.executable, "-W", "ignore", str(HERE / "close_one.py"), str(t[0])],
                           capture_output=True, text=True, timeout=20)
            hit.append(t[2])
    return hit


def gone(hwnd, timeout=2.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
            return True
        time.sleep(0.1)
    return False


def capture(x, context, order, roots, rec):
    """Abre a tela do item x, fotografa e fecha. Devolve 'parar' se algo saiu do esperado."""
    force_foreground(mw)
    base = {t[0] for t in top_windows(pid)}
    docs_before = com(lambda a, u: a.Documents.Count)
    proc = subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "invoke_one.py"), x["guid"]],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    wins, t1 = [], time.time()
    while time.time() - t1 < 8:
        wins = new_windows(base)
        if wins:
            break
        time.sleep(0.15)
    if not wins:
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        rec(x, "sem_janela", note="nenhuma janela nova do Corel em 8s")
        return None
    main_w = max(wins, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
    wait_stable(main_w[0])
    wins = new_windows(base)  # pode ter aparecido mais alguma (ex.: aviso)
    main_w = max(wins, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1])) if wins else main_w
    h, cls, title, _ = main_w
    r = win32gui.GetWindowRect(h)
    parts = x["path"].split(" > ")
    root_n = roots.get(parts[0], 0)
    folder = ROOT / "03-telas" / context / f"{root_n:02d} {safe_name(parts[0])}"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{order[x['path']]:03d} " + safe_name(" ▸ ".join(parts)) + ".png"
    grab(r, folder / name)
    extra = [t for t in wins if t[0] != h]
    note = f"+{len(extra)} janela(s) extra: {[t[2] for t in extra]}" if extra else ""
    # fecha tudo que abriu, da mais nova para a principal
    failed = []
    for t in extra + [main_w]:
        if win32gui.IsWindow(t[0]) and win32gui.IsWindowVisible(t[0]):
            how = close_window(t[0])
            if not how:
                failed.append(t[2] or t[1])
            elif t[0] == h:
                note = (note + f" fechado por {how}").strip()
    try:
        proc.wait(5)
    except subprocess.TimeoutExpired:
        proc.kill()
    rec(x, "ok", str((folder / name).relative_to(ROOT)), title, note, cls)
    if com(lambda a, u: a.Documents.Count) != docs_before:
        print("!! numero de documentos mudou; parando para conferir", flush=True)
        return "parar"
    prompts = guard_prompts(base)
    if prompts:
        print(f"!! apareceu pergunta de confirmacao {prompts}; respondida com Cancel; parando", flush=True)
        rec(x, "aviso", note="ATENCAO: fechar esta tela gerou pergunta de confirmacao (Cancel)")
        return "parar"
    left = new_windows(base)
    if failed or left:
        print(f"!! janela nao fechou: {failed or [t[2] for t in left]}; parando", flush=True)
        return "parar"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--context", default="doc-vazio")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
    roots = {x["caption"]: x["index"] + 1 for x in inv if x["kind"] == "menu_root"}
    cands = candidates(inv)
    # numero fixo por menu raiz, na ordem do inventario (nao muda entre rodadas parciais)
    order, cnt = {}, {}
    for x, _ in cands:
        r0 = x["path"].split(" > ")[0]
        cnt[r0] = cnt.get(r0, 0) + 1
        order[x["path"]] = cnt[r0]
    if a.only:
        cands = [(x, r) for x, r in cands if any(x["path"].startswith(o) for o in a.only)]
    log, seq = [], {}
    logf = ROOT / "90-relatorios" / f"telas_{a.context}.json"
    old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() else []

    def rec(x, status, img="", title="", note="", cls=""):
        log.append({"path": x["path"], "guid": x["guid"], "status": status, "image": img,
                    "window_title": title, "window_class": cls, "note": note})
        print(f"  [{status}] {x['path']} {('-> ' + title) if title else ''} {note}", flush=True)

    t0 = time.time()
    for x, reason in cands:
        en = com(lambda a, u: u.IsEnabled(x["guid"]))
        if a.list:
            print("PULA" if reason else ("ABRE" if en else "OFF "), x["path"], reason or "")
            continue
        if reason:
            rec(x, "nao_aberto", note=reason)
            continue
        if not en:
            rec(x, "desativado", note="desativado neste contexto")
            continue
        if capture(x, a.context, order, roots, rec):
            break
        time.sleep(0.3)
    if a.list:
        return
    (ROOT / "_tmp.png").unlink(missing_ok=True)
    keep = [r for r in old if r["path"] not in {l["path"] for l in log}]
    logf.write_text(json.dumps(keep + log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(log)} registros em {time.time() - t0:.0f}s -> {logf}")


if __name__ == "__main__":
    main()
