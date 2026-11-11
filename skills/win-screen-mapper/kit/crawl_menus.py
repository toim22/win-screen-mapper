"""crawl_menus.py: etapa 2 (e 5), os menus da barra e todos os submenus de qualquer app, so por hover.

Nada e executado: so o menu da barra e clicado; os submenus abrem passando o mouse. Cada menu ou
submenu aberto vira dois prints: o recorte (titulo do menu + cascata) e, em tela-inteira/, a janela.

Como acha as coisas (app.json -> "rota_menus"):
  uia       posicao do menu na barra e dos itens com submenu pela UI Automation
  win32     posicoes pelos menus nativos (GetMenuItemRect)
  adaptador adaptador.rect_menu_raiz(nome) -> (L,T,R,B); itens pela UIA ou pela imagem
  visao     menus_raiz_manual (x,y relativos a janela principal); itens pela imagem
Se a UIA nao enxergar os itens de um popup, as linhas sao achadas pela imagem (winui.linhas_do_popup)
e cada linha recebe hover; os nomes vem do inventario quando a contagem de linhas bate.

Saida: MAPEAMENTO/02-menus/<contexto>/NN Menu/NNN Menu ▸ Sub.png (+ tela-inteira/)
Log:   90-relatorios/menus_<contexto>.json (path, status ok|sem_submenu|erro, image, rects, note)

Uso: python crawl_menus.py [File Edit ...] [--contexto doc-vazio] [--config app.json]
     O adaptador.montar_contexto(contexto) roda antes de cada menu (o Esc pode tirar a selecao).
"""
import argparse
import time

import projeto
import winui as w

MARGEM = 16


class Crawler:
    def __init__(self, P, ctx, inv):
        self.P, self.ctx, self.inv = P, ctx, inv
        self.base_dir = P.ROOT / "02-menus" / ctx
        self.log = []
        self.U = w.UIA() if P.cfg.get("rota_menus") in ("uia", "adaptador") else None
        self.kw = P.cfg.get("linhas_menu", {"modo": "tinta"})
        self.hm = w.user32.GetMenu(P.mw) if P.cfg.get("rota_menus") == "win32" else 0

    # ---------------------------------------------------------- saida
    def shot(self, caminho, cadeia):
        self.seq += 1
        nome = f"{self.seq:03d} " + w.safe_name(" > ".join(caminho)) + ".png"
        main = w.win32gui.GetWindowRect(self.P.mw)
        full = w.union([main] + cadeia)
        img = w.grab(full, self.out / "tela-inteira" / nome)
        c = w.union([self.titulo] + cadeia)
        c = (max(c[0] - MARGEM, full[0]), max(c[1] - MARGEM, full[1]),
             min(c[2] + MARGEM, full[2]), min(c[3] + MARGEM, full[3]))
        img.crop((c[0] - full[0], c[1] - full[1], c[2] - full[0], c[3] - full[1])).save(self.out / nome)
        return self.out / nome

    def record(self, caminho, status, img=None, rects=None, note=""):
        self.log.append({"path": " > ".join(caminho), "status": status, "contexto": self.ctx,
                         "image": projeto.rel(self.P, img) if img else "", "rects": rects or [], "note": note})
        print(f"  [{status}] {' > '.join(caminho)} {note}", flush=True)

    # ---------------------------------------------------------- alvos de um popup aberto
    def filhos_inv(self, caminho):
        pref = " > ".join(caminho) + " > "
        return [x for x in self.inv if x["path"].startswith(pref) and " > " not in x["path"][len(pref):]]

    def alvos(self, hwnd, rect, caminho, hmenu):
        """[{x, y, label}] dos itens a passar o mouse."""
        if self.hm and hmenu:  # win32: itens com submenu e seus retangulos (popup aberto: hwnd=0)
            out = []
            for f in w.menu_win32(hmenu, profundidade=1):
                if f["has_submenu"]:
                    r = w.rect_item_win32(0, hmenu, f["index"])
                    if r:
                        out.append({"x": r[0] + 30, "y": (r[1] + r[3]) // 2, "label": f["caption"], "sub": f["sub"]})
            return out
        if self.U:
            els = [e for e in self.U.dump(hwnd) if e["type"] == "MenuItem" and e["rect"][2] > e["rect"][0]]
            if els:
                return [{"x": e["rect"][0] + 30, "y": (e["rect"][1] + e["rect"][3]) // 2,
                         "label": w.limpa_rotulo(e["name"]) or "sem nome"}
                        for e in els if "expand" in e["patterns"]]
        linhas = w.linhas_do_popup(w.grab(rect), **self.kw)
        nomes = [x["caption"] for x in self.filhos_inv(caminho)]
        usar = len(nomes) == len(linhas)
        return [{"x": rect[0] + 40, "y": rect[1] + y, "label": nomes[i] if usar else f"linha {i + 1}"}
                for i, (y, _) in enumerate(linhas)]

    # ---------------------------------------------------------- exploracao
    def explore(self, base, cadeia, caminho, hmenu=0):
        hwnd, rect = cadeia[-1]
        velhos = {}
        for t in self.alvos(hwnd, rect, caminho, hmenu):
            conhecidos = {h for h, _ in cadeia}
            novos = w.hover_abre(self.P.pid, base, self.P.mw, t["x"], t["y"], conhecidos, velhos,
                                 2.0 if t["label"] and not t["label"].startswith("linha ") else 0.9)
            if not novos:
                if not t["label"].startswith("linha "):
                    self.record(caminho + [t["label"]], "sem_submenu",
                                note="tem submenu mas nao abriu (desativado neste contexto)")
                continue
            sub = max(novos, key=lambda x: (x[3][2] - x[3][0]) * (x[3][3] - x[3][1]))
            sr = w.win32gui.GetWindowRect(sub[0])
            p2 = caminho + [t["label"]]
            f = self.shot(p2, [r for _, r in cadeia] + [sr])
            self.record(p2, "ok", f, [list(r) for _, r in cadeia] + [list(sr)])
            self.explore(base, cadeia + [(sub[0], sr)], p2, t.get("sub", 0))
            velhos = {x[0]: x[3] for x in w.popups_novos(self.P.pid, base, self.P.mw) if x[0] not in conhecidos}

    def rect_raiz(self, raiz):
        P, rota = self.P, self.P.cfg.get("rota_menus", "uia")
        if rota == "win32" and self.hm:
            return w.rect_item_win32(P.mw, self.hm, int(raiz["index"]))
        if rota == "visao":
            m = next((m for m in P.cfg.get("menus_raiz_manual", []) if m["nome"] == raiz["caption"]), None)
            if m:
                L, T = w.win32gui.GetWindowRect(P.mw)[:2]
                return (L + m["x"] - 10, T + m["y"] - 8, L + m["x"] + 10, T + m["y"] + 8)
            return None
        if rota == "adaptador" and hasattr(P.AD, "rect_menu_raiz"):
            return P.AD.rect_menu_raiz(raiz["caption"])
        for e in self.U.dump(P.mw):
            if e["type"] == "MenuItem" and e["parent"].startswith("MenuBar|") and \
                    projeto.norm(e["name"]) == projeto.norm(raiz["caption"]):
                return tuple(e["rect"])
        return None

    def crawl_root(self, n, raiz):
        P = self.P
        cap = raiz["caption"]
        self.out = self.base_dir / f"{n:02d} {w.safe_name(cap)}"
        (self.out / "tela-inteira").mkdir(parents=True, exist_ok=True)
        self.seq = 0
        projeto.montar_contexto(P, self.ctx)
        if not w.force_foreground(P.mw):
            return self.record([cap], "erro", note="nao consegui trazer o app para frente")
        base = {t[0] for t in w.top_windows(P.pid)}
        r = self.rect_raiz(raiz)
        if not r:
            return self.record([cap], "erro", note="nao achei o menu na barra")
        self.titulo = r
        cx, cy = (r[0] + r[2]) // 2, (r[1] + r[3]) // 2
        w.click(cx, cy)
        pops = w.esperar_popups(P.pid, base, P.mw)
        fora = w.janelas_fora(P.pid, base, P.mw)
        if fora:
            print(f"  !! janela fora da area do app (nao fotografada): {[t[2] or t[1] for t in fora]}")
        if not pops:
            return self.record([cap], "erro", note="menu nao abriu (desativado ou oculto?)")
        w.move(cx, cy)  # cursor no titulo: nenhum item destacado
        time.sleep(0.3)
        pop = max(pops, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
        pr = w.win32gui.GetWindowRect(pop[0])
        f = self.shot([cap], [pr])
        self.record([cap], "ok", f, [list(pr)])
        sub_hm = w.user32.GetSubMenu(self.hm, int(raiz["index"])) if self.hm else 0
        self.explore(base, [(pop[0], pr)], [cap], sub_hm)
        w.esc(4)
        time.sleep(0.3)
        if w.popups_novos(P.pid, base, P.mw):
            w.esc(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("menus", nargs="*")
    ap.add_argument("--contexto", default="doc-vazio")
    ap.add_argument("--config")
    a = ap.parse_args()
    P = projeto.carregar(a.config)
    inv = projeto.inventario(P)
    fora = set(P.cfg.get("menus_fora", []))
    want = {projeto.norm(m) for m in a.menus}
    c = Crawler(P, a.contexto, inv)
    t0 = time.time()
    try:
        raizes = [x for x in inv if x["kind"] == "menu_root"]
        for n, raiz in enumerate(raizes, 1):
            if raiz["caption"] in fora or (want and projeto.norm(raiz["caption"]) not in want):
                continue
            if not w.vivo(P.pid, P.mw):
                projeto.recuperar(P, "app nao esta rodando ou nao responde")
            print(f"== {raiz['caption']}", flush=True)
            c.crawl_root(n, raiz)
    finally:
        if c.U:
            c.U.fechar()
        feitos = {r["path"].split(" > ")[0] for r in c.log}
        f = projeto.salvar_log(P, f"menus_{a.contexto}", c.log, lambda r: r["path"].split(" > ")[0] in feitos)
        print(f"{len(c.log)} registros em {time.time() - t0:.0f}s -> {f}")


if __name__ == "__main__":
    main()
