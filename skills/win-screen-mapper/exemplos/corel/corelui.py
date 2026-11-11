"""Helpers compartilhados: conexao COM, janelas do Corel, foco, mouse e captura."""
import ctypes
import time
from ctypes import wintypes

ctypes.windll.shcore.SetProcessDpiAwareness(2)  # coordenadas em pixels fisicos

import win32api
import win32con
import win32gui
import win32process
from PIL import ImageGrab
from win32com.client import gencache

MENUBAR = "f3016f3c-2847-4557-b61a-a2d05319cf18"
SEPARATOR = "266435b4-6e53-460f-9fa7-f45be187d400"

user32 = ctypes.windll.user32


def connect():
    app = gencache.EnsureDispatch("CorelDRAW.Application.27")
    return app, app.FrameWork.Automation


def corel_pid():
    import subprocess
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CorelDRW.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[0].lower() == "corel drw.exe".replace(" ", ""):
            return int(parts[1])
    return None


def top_windows(pid):
    """Janelas top-level visiveis do processo: lista de (hwnd, classe, titulo, rect)."""
    res = []

    def cb(h, _):
        if not win32gui.IsWindowVisible(h):
            return True
        if win32process.GetWindowThreadProcessId(h)[1] != pid:
            return True
        r = win32gui.GetWindowRect(h)
        if r[2] - r[0] <= 1 or r[3] - r[1] <= 1:
            return True
        res.append((h, win32gui.GetClassName(h), win32gui.GetWindowText(h), r))
        return True

    win32gui.EnumWindows(cb, None)
    return res


def main_window(pid):
    best = None
    for h, cls, title, r in top_windows(pid):
        if "CorelDRAW" in title and win32gui.GetParent(h) == 0:
            area = (r[2] - r[0]) * (r[3] - r[1])
            if best is None or area > best[1]:
                best = (h, area)
    return best[0] if best else None


def _try_foreground(hwnd, alt):
    fg = win32gui.GetForegroundWindow()
    cur = win32api.GetCurrentThreadId()
    fg_thread = win32process.GetWindowThreadProcessId(fg)[0] if fg else 0
    tgt_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
    for t in {fg_thread, tgt_thread} - {cur, 0}:
        user32.AttachThreadInput(cur, t, True)
    try:
        if alt:  # libera o bloqueio de foreground do Windows
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32gui.BringWindowToTop(hwnd)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
    finally:
        for t in {fg_thread, tgt_thread} - {cur, 0}:
            user32.AttachThreadInput(cur, t, False)
    time.sleep(0.3)
    return win32gui.GetForegroundWindow() == hwnd


def force_foreground(hwnd):
    """Traz a janela para frente sem clicar. O truque do Alt so e usado como ultimo
    recurso e e desfeito com Esc, porque ele liga o modo teclado da barra de menus."""
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    if win32gui.GetForegroundWindow() == hwnd or _try_foreground(hwnd, False):
        return True
    ok = _try_foreground(hwnd, True)
    key(win32con.VK_ESCAPE, 2)
    time.sleep(0.2)
    return ok or win32gui.GetForegroundWindow() == hwnd


def move(x, y):
    win32api.SetCursorPos((int(x), int(y)))


def click(x, y):
    move(x, y)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)


def key(vk, times=1):
    for _ in range(times):
        win32api.keybd_event(vk, 0, 0, 0)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)


def union(rects):
    return (min(r[0] for r in rects), min(r[1] for r in rects),
            max(r[2] for r in rects), max(r[3] for r in rects))


def grab(rect, path):
    img = ImageGrab.grab(bbox=rect, all_screens=True)
    img.save(path)
    return img


def safe_name(s, maxlen=150):
    bad = '<>:"/\\|?*'
    s = "".join("_" if c in bad or ord(c) < 32 else c for c in s).strip(" .")
    return s[:maxlen] or "_"
