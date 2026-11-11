"""winui.py: helpers genericos para automatizar e fotografar QUALQUER app desktop do Windows.

Nada aqui e de um app especifico. O que muda por app vem do app.json (ver projeto.py), que chama
configurar(). Partes:
- processo e janelas (pid pelo .exe, janela principal pelo titulo/classe, filhos, vivo/responde);
- foco sem o truque do Alt (ele liga o modo teclado do menu e abre o menu errado);
- mouse/teclado (clique, clique direito, roda, hover com micro-movimentos);
- popups: so os visiveis, com tamanho e DENTRO da janela do app (uma captura ja pegou o outro
  monitor com o chat do usuario); eh_menu() separa menu/lista (fecha com Esc) de janela (fecha pelo X);
- linhas de um menu pela imagem (para menus que a UI Automation nao enxerga);
- menus Win32 nativos (HMENU): ler itens, ids, estado e retangulos; abrir comando por WM_COMMAND;
- cliente da UI Automation em subprocesso (UIA): pywinauto no mesmo processo que COM derrubou o Python;
- captura multi-monitor, diferenca de imagens, tarja de areas pessoais, nomes de arquivo seguros.
"""
import ctypes
import json
import queue
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

ctypes.windll.shcore.SetProcessDpiAwareness(2)  # pixels fisicos

import win32api
import win32con
import win32gui
import win32process
from PIL import Image, ImageChops, ImageDraw, ImageGrab

user32 = ctypes.windll.user32
AQUI = Path(__file__).resolve().parent

APP_EXE = "App.exe"          # nome do executavel
APP_TITULO = "App"           # trecho do titulo da janela principal
CLASSE_PRINCIPAL = ""        # classe da janela principal (opcional, mais seguro que o titulo)
CLASSES_MENU = ("#32768",)   # popups de menu/lista: fecham com Esc. Acrescente as do app (Qt, MFC Afx...)
CLASSES_IGNORAR = ("SysShadow", "tooltips_class32", "IME", "MSCTFIME UI", "Shell_TrayWnd")
FOLGA = 40                   # px de folga ao redor da janela principal para aceitar popups


def configurar(exe=None, titulo=None, classe=None, classes_menu=None):
    global APP_EXE, APP_TITULO, CLASSE_PRINCIPAL, CLASSES_MENU
    APP_EXE = exe or APP_EXE
    APP_TITULO = titulo or APP_TITULO
    CLASSE_PRINCIPAL = classe or CLASSE_PRINCIPAL
    if classes_menu:
        CLASSES_MENU = tuple(dict.fromkeys(("#32768",) + tuple(classes_menu)))


# ---------------------------------------------------------------- processo e janelas
def app_pid():
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {APP_EXE}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[0].lower() == APP_EXE.lower():
            return int(parts[1])
    return None


def top_windows(pid):
    """Janelas top-level visiveis e com tamanho do processo: [(hwnd, classe, titulo, rect)]."""
    res = []

    def cb(h, _):
        try:
            if not win32gui.IsWindowVisible(h) or win32process.GetWindowThreadProcessId(h)[1] != pid:
                return True
            r = win32gui.GetWindowRect(h)
            if r[2] - r[0] > 4 and r[3] - r[1] > 4:
                res.append((h, win32gui.GetClassName(h), win32gui.GetWindowText(h), r))
        except Exception:
            pass
        return True

    win32gui.EnumWindows(cb, None)
    return res


def main_window(pid):
    """Janela principal: pela classe (se configurada), senao a maior janela sem pai com APP_TITULO."""
    best = None
    for h, cls, title, r in top_windows(pid):
        if win32gui.GetParent(h) != 0:
            continue
        if CLASSE_PRINCIPAL and cls != CLASSE_PRINCIPAL:
            continue
        if not CLASSE_PRINCIPAL and APP_TITULO.lower() not in title.lower():
            continue
        area = (r[2] - r[0]) * (r[3] - r[1])
        if best is None or area > best[1]:
            best = (h, area)
    return best[0] if best else None


def child_windows(hwnd):
    """Filhos (recursivo) visiveis: {hwnd: (classe, rect, titulo)}. Util para achar paineis novos."""
    out = {}

    def cb(h, _):
        try:
            if win32gui.IsWindowVisible(h):
                out[h] = (win32gui.GetClassName(h), win32gui.GetWindowRect(h), win32gui.GetWindowText(h))
        except Exception:
            pass
        return True

    win32gui.EnumChildWindows(hwnd, cb, None)
    return out


def responde(hwnd, ms=3000):
    """True se a janela processa mensagens (app nao travado)."""
    try:
        res = ctypes.c_size_t()
        return bool(user32.SendMessageTimeoutW(hwnd, 0, 0, 0, 0x0002, ms, ctypes.byref(res)))
    except Exception:
        return False


def vivo(pid, hwnd):
    return bool(pid) and app_pid() == pid and bool(win32gui.IsWindow(hwnd)) and responde(hwnd)


def matar_app():
    subprocess.run(["taskkill", "/IM", APP_EXE, "/F"], capture_output=True)
    time.sleep(4)


# ---------------------------------------------------------------- foco
def _try_foreground(hwnd, alt):
    fg = win32gui.GetForegroundWindow()
    cur = win32api.GetCurrentThreadId()
    fg_t = win32process.GetWindowThreadProcessId(fg)[0] if fg else 0
    tg_t = win32process.GetWindowThreadProcessId(hwnd)[0]
    for t in {fg_t, tg_t} - {cur, 0}:
        user32.AttachThreadInput(cur, t, True)
    try:
        if alt:
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32gui.BringWindowToTop(hwnd)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
    finally:
        for t in {fg_t, tg_t} - {cur, 0}:
            user32.AttachThreadInput(cur, t, False)
    time.sleep(0.3)
    return win32gui.GetForegroundWindow() == hwnd


def force_foreground(hwnd, clicar_titulo=True):
    """Traz a janela para frente: AttachThreadInput; clique na barra de titulo; so por ultimo o Alt
    (desfeito com Esc)."""
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    if win32gui.GetForegroundWindow() == hwnd or _try_foreground(hwnd, False):
        return True
    if clicar_titulo:
        r = win32gui.GetWindowRect(hwnd)
        click((r[0] + r[2]) // 2, r[1] + 12)
        time.sleep(0.4)
        if win32gui.GetForegroundWindow() == hwnd:
            return True
    ok = _try_foreground(hwnd, True)
    key(win32con.VK_ESCAPE, 2)
    time.sleep(0.2)
    return ok or win32gui.GetForegroundWindow() == hwnd


# ---------------------------------------------------------------- mouse e teclado
def move(x, y):
    win32api.SetCursorPos((int(x), int(y)))


def click(x, y, botao="esq"):
    move(x, y)
    time.sleep(0.05)
    d, u = ((win32con.MOUSEEVENTF_RIGHTDOWN, win32con.MOUSEEVENTF_RIGHTUP) if botao == "dir"
            else (win32con.MOUSEEVENTF_LEFTDOWN, win32con.MOUSEEVENTF_LEFTUP))
    win32api.mouse_event(d, 0, 0)
    win32api.mouse_event(u, 0, 0)


def right_click(x, y):
    click(x, y, "dir")


def key(vk, times=1):
    for _ in range(times):
        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)


def esc(times=1):
    key(win32con.VK_ESCAPE, times)


def wheel(rect, n, para_baixo=True, passo=15):
    """Roda do mouse no centro do rect (n giros de `passo` entalhes)."""
    move((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
    for _ in range(n):
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, (-120 if para_baixo else 120) * passo, 0)
        time.sleep(0.5 if para_baixo else 0.2)
    time.sleep(0.3)


def away(rect, dx=-150, dy=300):
    """Tira o mouse de cima do alvo (tooltips e hovers estragam o print). Mantem o cursor dentro
    da janela principal quando possivel."""
    move(rect[0] + dx, rect[1] + dy)
    time.sleep(0.9)


# ---------------------------------------------------------------- popups
def dentro(rect, area, folga=FOLGA):
    a, b, c, d = rect
    L, T, R, B = area
    return a >= L - folga and c <= R + folga and b >= T - folga and d <= B + folga


def eh_menu(t):
    """t = (hwnd, classe, titulo, rect). Menu/lista/popup (fecha com Esc) x janela (fecha pelo X)."""
    cls, title = t[1], t[2]
    if any(cls.startswith(c) for c in CLASSES_MENU):
        return True
    if cls == "#32770" or title:
        return False
    return True  # sem titulo e nao e dialogo padrao: quase sempre popup desenhado pelo app


def popups_novos(pid, baseline, hwnd_principal, ignorar=CLASSES_IGNORAR):
    """Janelas novas do processo (fora de baseline), visiveis, com tamanho e dentro da principal."""
    area = win32gui.GetWindowRect(hwnd_principal)
    return [t for t in top_windows(pid)
            if t[0] not in baseline and t[0] != hwnd_principal and t[1] not in ignorar and dentro(t[3], area)]


def janelas_fora(pid, baseline, hwnd_principal):
    """Janelas novas do processo FORA da area do app: nao fotografar; avisar o usuario."""
    area = win32gui.GetWindowRect(hwnd_principal)
    return [t for t in top_windows(pid)
            if t[0] not in baseline and t[0] != hwnd_principal and not dentro(t[3], area)]


def esperar_popups(pid, baseline, hwnd_principal, minimo=1, timeout=2.5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if len(popups_novos(pid, baseline, hwnd_principal)) >= minimo:
            time.sleep(0.25)  # deixa terminar de desenhar
            break
        time.sleep(0.05)
    return popups_novos(pid, baseline, hwnd_principal)


def esperar_estavel(rect, timeout=4.0, intervalo=0.4):
    """Espera o conteudo do rect parar de mudar (janela terminando de desenhar)."""
    prev, t0 = grab(rect), time.time()
    while time.time() - t0 < timeout:
        time.sleep(intervalo)
        cur = grab(rect)
        if not mudou(prev, cur):
            return cur
        prev = cur
    return prev


def hover_abre(pid, baseline, hwnd_principal, x, y, conhecidos, velhos, timeout=2.0):
    """Passa o mouse em (x, y) e espera um submenu NOVO. `velhos` = {hwnd: rect} do submenu
    anterior, que fecha com atraso: enquanto ele estiver aberto, nada novo conta (senao o print
    sai com o submenu errado). Micro-movimentos: alguns apps so armam o hover com varios WM_MOUSEMOVE."""
    move(x - 6, y)
    time.sleep(0.05)
    move(x, y)
    t0, k = time.time(), 0
    while time.time() - t0 < timeout:
        k += 1
        if k % 6 == 0:
            move(x + (2 if (k // 6) % 2 else -2), y)
        novos, velho_aberto = [], False
        for w in popups_novos(pid, baseline, hwnd_principal):
            if w[0] in conhecidos:
                continue
            if w[0] in velhos and tuple(w[3]) == tuple(velhos[w[0]]):
                velho_aberto = True
                continue
            novos.append(w)
        if novos and not velho_aberto:
            time.sleep(0.25)
            return novos
        time.sleep(0.05)
    return []


def linhas_do_popup(img, modo="tinta", row_h=22, sep_h=7, pad=3, x0=None, x1=None):
    """Linhas de item de um menu desenhado pelo app, pela imagem. Devolve [(y_centro, segmento)].

    modo "tinta" (padrao, serve para qualquer app): acha as faixas horizontais que tem texto/icone
    (pixels diferentes do fundo); faixas com menos de 5 px de altura sao separadores (mudam o
    segmento). Nao precisa medir nada.
    modo "medidas": usa altura fixa de linha/separador (no Corel: 22/7/3). Use se o "tinta" juntar
    linhas (itens muito colados)."""
    W, H = img.size
    rgb = img.convert("RGB")
    px = rgb.load()
    x0 = 8 if x0 is None else x0
    x1 = W - 8 if x1 is None else x1
    bg = max(rgb.crop((x0, 0, x1, H)).getcolors(W * H), key=lambda t: t[0])[1]
    if modo == "tinta":
        def tinta(y):
            n = 0
            for x in range(x0, x1, 2):
                c = px[x, y]
                if abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2]) > 90:
                    n += 1
            return n
        faixas, ini = [], None
        for y in range(pad, H - pad):
            if tinta(y):
                ini = y if ini is None else ini
            elif ini is not None:
                faixas.append((ini, y))
                ini = None
        if ini is not None:
            faixas.append((ini, H - pad))
        rows, seg = [], 0
        for a, b in faixas:
            if b - a < 5:
                seg += 1  # separador (linha fina)
            else:
                rows.append(((a + b) // 2, seg))
        return rows
    # modo "medidas"
    seps = []
    for y in range(pad, H - pad):
        row = {px[x, y] for x in range(x0 + 28, x1 - 4, 3)}
        if len(row) == 1:
            c = next(iter(row))
            if c != bg and abs(sum(c) - sum(bg)) > 60:
                seps.append(y)
    grupos = []
    for y in seps:
        if not grupos or y - grupos[-1][-1] > 1:
            grupos.append([y])
        else:
            grupos[-1].append(y)
    rows, seg, start = [], 0, pad
    bounds = [(g[0] - sep_h // 2, g[-1] + sep_h - sep_h // 2) for g in grupos] + [(H - pad, H)]
    for s0, s1 in bounds:
        for i in range(max(round((s0 - start) / row_h), 0)):
            rows.append((start + i * row_h + row_h // 2, seg))
        seg += 1
        start = s1
    return rows


# ---------------------------------------------------------------- menus Win32 nativos (HMENU)
MF_GRAYED, MF_DISABLED, MF_POPUP, MF_SEPARATOR = 0x1, 0x2, 0x10, 0x800


def limpa_rotulo(s):
    """'&File\tCtrl+N' -> 'File' ; '&&' -> '&'."""
    s = (s or "").split("\t")[0]
    return s.replace("&&", "\0").replace("&", "").replace("\0", "&").replace("…", "...").strip()


def menu_win32(hmenu, caminho=(), profundidade=6):
    """Le um HMENU (funciona entre processos: menus sao objetos globais do USER).
    Devolve [{path, caption, id, index, has_submenu, enabled, separator, hmenu, sub}].
    Submenus montados na hora (WM_INITMENUPOPUP) podem vir vazios: complete com UIA ou com o crawler."""
    out = []
    n = user32.GetMenuItemCount(hmenu)
    for i in range(max(n, 0)):
        st = user32.GetMenuState(hmenu, i, win32con.MF_BYPOSITION)
        buf = ctypes.create_unicode_buffer(512)
        user32.GetMenuStringW(hmenu, i, buf, 512, win32con.MF_BYPOSITION)
        cap = limpa_rotulo(buf.value)
        sub = user32.GetSubMenu(hmenu, i)
        sep = bool(st & MF_SEPARATOR) and not cap
        item = {"path": " > ".join(caminho + (cap,)), "caption": cap, "index": i,
                "id": user32.GetMenuItemID(hmenu, i) if not sub else -1, "has_submenu": bool(sub),
                "enabled": not (st & (MF_GRAYED | MF_DISABLED)), "separator": sep, "hmenu": hmenu, "sub": sub}
        out.append(item)
        if sub and profundidade > 1:
            item["filhos"] = menu_win32(sub, caminho + (cap,), profundidade - 1)
    return out


def rect_item_win32(hwnd, hmenu, index):
    """Retangulo na tela do item `index` de hmenu. Barra: hwnd = janela principal; popup aberto: hwnd=0."""
    r = wintypes.RECT()
    if user32.GetMenuItemRect(hwnd or None, hmenu, index, ctypes.byref(r)):
        return (r.left, r.top, r.right, r.bottom)
    return None


def comando_win32(hwnd, cmd_id):
    """Executa o comando de menu pelo id (como clicar no item). So para itens aprovados (lista negra!)."""
    win32gui.PostMessage(hwnd, win32con.WM_COMMAND, cmd_id, 0)


# ---------------------------------------------------------------- UI Automation (subprocesso)
class UIA:
    """Cliente do uia_tool.py em modo serve. Cada chamada tem timeout; se o servidor travar
    (ex.: Invoke que abriu um modal), ele e reiniciado e a chamada devolve {"ok": False, "timeout": True}."""

    def __init__(self, timeout=20):
        self.timeout = timeout
        self.p = None
        self._start()

    def _start(self):
        self.p = subprocess.Popen([sys.executable, "-W", "ignore", str(AQUI / "uia_tool.py"), "serve"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, encoding="utf-8")
        self.q = queue.Queue()
        p, q = self.p, self.q
        threading.Thread(target=lambda: [q.put(l) for l in p.stdout], daemon=True).start()

    def _cmd(self, c, timeout=None):
        if self.p.poll() is not None:
            self._start()
        try:
            self.p.stdin.write(json.dumps(c) + "\n")
            self.p.stdin.flush()
            return json.loads(self.q.get(timeout=timeout or self.timeout))
        except queue.Empty:
            self.p.kill()
            self._start()
            return {"ok": False, "timeout": True}
        except Exception as e:
            self.p.kill()
            self._start()
            return {"ok": False, "erro": str(e)[:200]}

    def dump(self, hwnd, timeout=None):
        r = self._cmd({"cmd": "dump", "hwnd": int(hwnd)}, timeout)
        return r if isinstance(r, list) else []

    def do(self, hwnd, action, key, timeout=None):
        return self._cmd({"cmd": "do", "hwnd": int(hwnd), "action": action, "key": key}, timeout)

    def fechar(self):
        try:
            self.p.kill()
        except Exception:
            pass


def fechar_por_botao(hwnd):
    """Fecha um dialogo pelo Cancel/Close via UIA (close_one.py). Devolve o nome do botao ou ''."""
    out = subprocess.run([sys.executable, "-W", "ignore", str(AQUI / "close_one.py"), str(hwnd)],
                         capture_output=True, text=True, encoding="utf-8", timeout=30).stdout.strip()
    time.sleep(0.6)
    return out


def fechar_dialogo(hwnd):
    """Cancel/Close; se nao houver, X (WM_CLOSE). NAO use em menus desenhados pelo app (Esc)."""
    try:
        fechar_por_botao(hwnd)
    except Exception:
        pass
    if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
        fechar_janela(hwnd)
    return not (win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd))


# ---------------------------------------------------------------- captura
def union(rects):
    return (min(r[0] for r in rects), min(r[1] for r in rects),
            max(r[2] for r in rects), max(r[3] for r in rects))


def grab(rect, path=None):
    img = ImageGrab.grab(bbox=tuple(int(v) for v in rect), all_screens=True)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
    return img


def mudou(a, b):
    """Retangulo da diferenca entre duas imagens (None = iguais)."""
    if a.size != b.size:
        return (0, 0) + b.size
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox()


def assinatura(img):
    """Hash curto da imagem, para descartar prints repetidos."""
    import hashlib
    return hashlib.md5(img.convert("L").resize((64, 64)).tobytes()).hexdigest()


def tarjar(path, rects, cor=(128, 128, 128), texto="conteudo pessoal ocultado"):
    """Cobre regioes (coordenadas da imagem) com uma tarja. Use em seletores de arquivo."""
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    for r in rects:
        d.rectangle(r, fill=cor)
        d.text((r[0] + 6, r[1] + 6), texto, fill=(255, 255, 255))
    im.save(path)


def safe_name(s, maxlen=150):
    bad = '<>:"/\\|?*'
    s = s.replace(" > ", " ▸ ")
    s = "".join("_" if c in bad or ord(c) < 32 else c for c in s).strip(" .")
    return s[:maxlen] or "_"


def fechar_janela(hwnd):
    """WM_CLOSE (equivale ao X). NAO use em menus/listas desenhados pelo app: use esc()."""
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    except Exception:
        pass
    time.sleep(0.6)
