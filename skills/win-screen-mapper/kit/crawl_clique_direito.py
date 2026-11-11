"""crawl_clique_direito.py: etapa 6, menus de contexto (clique direito) de qualquer app.

Lugares em app.json -> "cliques_direitos" (x, y relativos a janela principal; marque numa folha com regua):
  [{"nome": "Pagina vazia", "x": 700, "y": 500, "contexto": "doc-vazio"},
   {"nome": "Retangulo", "x": 640, "y": 420, "contexto": "retangulo"},
   {"nome": "Regua", "x": 400, "y": 118}]
Antes de cada clique roda adaptador.montar_contexto(contexto). Os submenus abrem so por hover
(mesmo motor do crawl_menus.py). Nada e clicado dentro do menu.

Saida: 07-menus-de-contexto/NN Nome/... (+ tela-inteira/)   Log: 90-relatorios/menus_contexto.json
Uso: python crawl_clique_direito.py [--only "Pagina vazia"] [--config app.json]
"""
import argparse
import time

import projeto
import winui as w
from crawl_menus import Crawler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--config")
    a = ap.parse_args()
    P = projeto.carregar(a.config)
    lugares = P.cfg.get("cliques_direitos", [])
    if not lugares:
        raise SystemExit("preencha 'cliques_direitos' no app.json")
    c = Crawler(P, "", [])
    c.base_dir = P.ROOT / "07-menus-de-contexto"
    c.hm = 0  # menus de contexto: itens pela UIA ou pela imagem
    try:
        for n, l in enumerate(lugares, 1):
            if a.only and l["nome"] not in a.only:
                continue
            if not w.vivo(P.pid, P.mw):
                projeto.recuperar(P, "app nao esta rodando ou nao responde")
            c.ctx = l.get("contexto", "doc-vazio")
            projeto.montar_contexto(P, c.ctx)
            w.force_foreground(P.mw)
            c.out = c.base_dir / f"{n:02d} {w.safe_name(l['nome'])}"
            (c.out / "tela-inteira").mkdir(parents=True, exist_ok=True)
            c.seq = 0
            L, T = w.win32gui.GetWindowRect(P.mw)[:2]
            x, y = L + l["x"], T + l["y"]
            c.titulo = (x - 6, y - 6, x + 6, y + 6)
            base = {t[0] for t in w.top_windows(P.pid)}
            w.right_click(x, y)
            pops = [t for t in w.esperar_popups(P.pid, base, P.mw) if w.eh_menu(t)]
            if not pops:
                c.record([l["nome"]], "sem_menu", note="o clique direito nao abriu menu aqui")
                w.esc()
                continue
            pop = max(pops, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
            pr = w.win32gui.GetWindowRect(pop[0])
            w.move(x, y)
            time.sleep(0.3)
            c.record([l["nome"]], "ok", c.shot([l["nome"]], [pr]), [list(pr)])
            c.explore(base, [(pop[0], pr)], [l["nome"]])
            w.esc(4)
            time.sleep(0.3)
    finally:
        if c.U:
            c.U.fechar()
        feitos = {r["path"].split(" > ")[0] for r in c.log}
        f = projeto.salvar_log(P, "menus_contexto", c.log, lambda r: r["path"].split(" > ")[0] in feitos)
        print(f"{len(c.log)} registros -> {f}")


if __name__ == "__main__":
    main()
