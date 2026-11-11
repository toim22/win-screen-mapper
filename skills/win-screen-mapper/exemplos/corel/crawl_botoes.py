"""Etapa 4b: botoes dentro das telas que abrem janelas filhas ou menus.

Para cada tela (e cada pagina/aba dela), clica nos botoes "seguros", fotografa o que abriu
(janela filha: estado inicial + paginas + listas + rolagem; menu: o menu aberto), fecha pelo
Cancel/Esc e segue. Nunca clica em OK/Apply/Delete/Reset/Save etc. (regra do usuario).

Saida: <pasta da tela>/botoes/NNN <pagina> ▸ botao ▸ <nome> ....png
Log:   90-relatorios/botoes_<ctx>.json

Uso:
  python crawl_botoes.py --dry                 # so lista os botoes (clicaria / nao clicaria)
  python crawl_botoes.py --only "Tools > Options > CorelDRAW..."
"""
import argparse
import json
import re
import time
from pathlib import Path

from PIL import ImageChops

from crawl_dentro import SKIP, UIA, Explorer
from crawl_telas import ROOT, close_window, com, guard_prompts, new_windows, pid, wait_stable
from corelui import click, force_foreground, grab, key, top_windows, win32con, win32gui

# Nunca clicar (confirmam, apagam, salvam, mexem em conta/compra ou fecham a tela).
NEVER_EXACT = {"ok", "apply", "cancel", "close", "yes", "no", "help", "finish", "done", "x",
               "minimize", "maximize", "restore", "open", "save", "import", "export"}
NEVER_WORDS = ("delete", "remove", "reset", "restore", "save", "export", "print", "publish", "clear",
               "default", "buy", "purchase", "sign", "log in", "login", "upload", "share", "send",
               "update", "exit", "uninstall", "discard", "overwrite", "replace", "rename", "apply",
               "already purchased", "subscribe", "install", "download", "convert", "merge",
               # abrem o navegador / aceitam termos (fora do escopo, decisao do usuario)
               "policy", "privacy", "statement", "terms", "agree", "online", "website", "learn more",
               "web", "support", "feedback", "tutorial", "legal", "credential", "profile",
               "account",
               # 2026-11-08: fechar o "Security Options..." (dialogo do VBA) travou o Corel
               "security")
# Sem "..." so clica se o nome indicar que abre algo (janela/menu), nao que executa uma acao.
OPENER_WORDS = ("advanced", "edit", "options", "settings", "more", "details", "properties", "browse",
                "customize", "preview", "info", "setup", "configure", "manage", "show", "view")


def norm(name):
    return name.replace("&", "").strip()


ALWAYS = {"add color"}  # abre o seletor de cor (o Cancel da tela desfaz)


def classify(b):
    """('clica'|'nao', motivo)."""
    n = norm(b["name"]).lower()
    base = n.rstrip(".…").strip()
    if base in ALWAYS:
        return "clica", "liberado"
    if base in NEVER_EXACT:
        return "nao", "confirmacao/fechamento"
    for w in NEVER_WORDS:
        if re.search(rf"\b{re.escape(w)}", base):
            return "nao", f"palavra proibida: {w}"
    if n.endswith("...") or n.endswith("…"):
        return "clica", "abre janela (...)"
    if b["type"] == "SplitButton" or "expand" in b["patterns"]:
        return "clica", "botao com menu"
    for w in OPENER_WORDS:
        if re.search(rf"\b{w}\b", base):
            return "clica", f"abre algo: {w}"
    return "nao", "acao direta (sem ...)"


class ButtonExplorer(Explorer):
    def buttons(self, els):
        dl, dt, dr, db = win32gui.GetWindowRect(self.hwnd)
        out = []
        for e in els:
            if e["type"] not in ("Button", "SplitButton") or not e["name"].strip() or not e["enabled"]:
                continue
            x0, y0, x1, y1 = e["rect"]
            if x1 <= x0 or y1 <= y0 or not (dl <= x0 and x1 <= dr and dt + 25 <= y0 and y1 <= db):
                continue
            if e["parent"].split("|")[0] in ("TitleBar", "ScrollBar", "ComboBox", "Spinner"):
                continue
            out.append(e)
        return out

    def run_buttons(self, entry, dry):
        self.path, self.hashes, self.n, self.skipped = entry["path"], set(), 0, []
        img = Path(entry["image"])
        self.folder = ROOT / img.parent / img.stem / "botoes"
        self.found = []
        if not dry:
            self.folder.mkdir(parents=True, exist_ok=True)
            for old in self.folder.glob("*.png"):
                old.unlink()
        if not self.open_screen(entry):
            return "sem_janela"
        self.docs = com(lambda a, u: a.Documents.Count)
        status = "ok"
        try:
            els = self.uia.dump(self.hwnd)
            if self.is_file_dialog(els):
                status = "pulada (seletor de arquivos do Windows)"
            else:
                nav = self.pages(els)
                seen = set()
                for it in (nav or [None]):
                    prefix = ""
                    if it:
                        if not self.uia.do(self.hwnd, "select", it["key"]).get("ok"):
                            continue
                        self.settle()
                        prefix = f"{it['name']} ▸ "
                    for b in self.buttons(self.uia.dump(self.hwnd)):
                        ident = (norm(b["name"]), tuple(b["rect"]))
                        if ident in seen:
                            continue  # mesmo botao em todas as paginas (rodape da janela)
                        seen.add(ident)
                        decision, why = classify(b)
                        self.found.append({"pagina": it["name"] if it else "", "botao": norm(b["name"]),
                                           "tipo": b["type"], "decisao": decision, "motivo": why})
                        if dry or decision != "clica":
                            continue
                        self.press(prefix, b, it)
        except Exception as e:
            status = f"erro: {e}"
            print("   !!", e, flush=True)
        return self.finish(status)

    def reselect(self, it):
        if it:
            self.uia.do(self.hwnd, "select", it["key"])
            self.settle(0.3)

    def press(self, prefix, b, it, rect=None, label=None, explore_change=False):
        name = norm(b["name"]).rstrip(".…").strip()
        label = label or f"{prefix}botao ▸ {name}"
        parent = self.hwnd
        if rect is None:
            r = self.uia.do(parent, "rect", b["key"])  # posicao atual (pode ter mudado)
            if not r.get("ok"):
                return
            rect = r["rect"]
        x0, y0, x1, y1 = rect
        before_all = {t[0] for t in top_windows(pid)}
        pr = win32gui.GetWindowRect(parent)
        img0 = grab(pr, ROOT / "_tmp.png").convert("L")
        force_foreground(parent)
        if b["type"] == "SplitButton":
            click(x1 - 6, (y0 + y1) / 2)  # seta do botao dividido
        else:
            click((x0 + x1) / 2, (y0 + y1) / 2)
        new, t0 = [], time.time()
        while time.time() - t0 < 4 and not new:
            time.sleep(0.2)
            new = [t for t in top_windows(pid) if t[0] not in before_all]
        wins = [t for t in new if not t[1].startswith("Afx:")]
        pops = [t for t in new if t[1].startswith("Afx:")]
        if not win32gui.IsWindow(parent) or not win32gui.IsWindowVisible(parent):
            raise SystemExit(f"!! o botao {name!r} fechou a tela; parando para conferir")
        if wins:
            child = max(wins, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
            wait_stable(child[0])
            self.hwnd = child[0]
            try:
                self.shot(label, force=True)
                self.explore_window(f"{label} ▸ ")
            except Exception as e:
                self.skipped.append(f"{label}: erro explorando janela filha: {e}")
            finally:
                self.hwnd = parent
            for t in [t for t in top_windows(pid) if t[0] not in before_all]:
                if t[0] != child[0] and not t[1].startswith("Afx:") and win32gui.IsWindow(t[0]):
                    try:
                        close_window(t[0])
                    except Exception:
                        pass  # ja fechou sozinha
            how = close_window(child[0]) if win32gui.IsWindow(child[0]) else "ja fechada"
            prompts = guard_prompts(before_all)
            left = new_windows(before_all)
            if prompts or left or not how:
                raise SystemExit(f"!! parando em {label}: pergunta={prompts} sobrou={[t[2] for t in left]}")
            self.settle(0.3)
        elif pops:
            time.sleep(0.4)
            self.shot(label + " ▸ menu", [t[3] for t in pops])
            # fecha so o popup (Esc em paleta de cor do Corel fecha a tela inteira)
            for t in pops:
                win32gui.PostMessage(t[0], win32con.WM_CLOSE, 0, 0)
            time.sleep(0.6)
            if [t for t in top_windows(pid) if t[0] not in before_all]:
                key(win32con.VK_ESCAPE)
                time.sleep(0.3)
        else:
            time.sleep(0.6)
            img1 = grab(pr, ROOT / "_tmp.png").convert("L")
            diff = ImageChops.difference(img0, img1).point(lambda v: 255 if v > 24 else 0)
            if diff.histogram()[255] > 50:
                if explore_change:
                    self.settle(0.3)
                    self.shot(label, force=True)
                    self.explore_page(f"{label} ▸ ")
                else:
                    self.shot(label + " (mudou a tela, sem janela)")
                    self.skipped.append(f"{label}: mudou a tela sem abrir janela (desfeito pelo Cancel ao fechar)")
            else:
                self.skipped.append(f"{label}: nada aconteceu")
        if com(lambda a, u: a.Documents.Count) != self.docs:
            raise SystemExit(f"!! numero de documentos mudou depois de {label}; parando")
        if not win32gui.IsWindow(parent):
            raise SystemExit(f"!! a tela fechou depois de {label}")
        self.reselect(it)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--context", default="doc-vazio")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    telas = json.loads((ROOT / "90-relatorios" / f"telas_{a.context}.json").read_text(encoding="utf-8"))
    todo = [t for t in telas if t["status"] == "ok" and t["path"] not in SKIP]
    if a.only:
        todo = [t for t in todo if any(t["path"].startswith(o) for o in a.only)]
    ex = ButtonExplorer(UIA(), a.context)
    resumo, t0 = [], time.time()
    parou = None
    try:
        for entry in todo:
            print(f"== {entry['path']}", flush=True)
            n0 = len(ex.log)
            st = ex.run_buttons(entry, a.dry)
            for f in ex.found:
                print(f"     [{f['decisao']:5}] {f['pagina'][:25]:25} {f['botao'][:40]:40} {f['motivo']}", flush=True)
            for sk in ex.skipped:
                print(f"     - {sk}", flush=True)
            resumo.append({"tela": entry["path"], "status": st, "prints": len(ex.log) - n0,
                           "botoes": ex.found, "observacoes": ex.skipped})
    except SystemExit as e:  # parada de seguranca: grava o log do que ja foi feito
        parou = str(e)
        print(parou, flush=True)
    (ROOT / "_tmp.png").unlink(missing_ok=True)
    logf = ROOT / "90-relatorios" / f"botoes_{a.context}{'_dry' if a.dry else ''}.json"
    old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() else {"estados": [], "resumo": []}
    feitas = {r["tela"] for r in resumo}
    old["estados"] = [s for s in old["estados"] if s["tela"] not in feitas] + ex.log
    old["resumo"] = [s for s in old["resumo"] if s["tela"] not in feitas] + resumo
    logf.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ex.log)} prints em {time.time() - t0:.0f}s -> {logf}")
    if parou:
        raise SystemExit(parou)


if __name__ == "__main__":
    main()
