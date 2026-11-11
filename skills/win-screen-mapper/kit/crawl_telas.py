"""crawl_telas.py: etapas 3 e 4 de qualquer app. Abre cada comando que abre janela, fotografa,
explora por dentro (opcional) e fecha por Cancel/X, sem confirmar nada.

Quais itens: os do inventario com abre_janela (nome termina em "...") e que nao estao na lista negra
(lista_negra.item_bloqueado + menus_fora do app.json). --incluir acrescenta caminhos exatos aprovados.
Itens bloqueados entram no log como nao_aberto, com o motivo.

Como abre (app.json -> "abrir_telas"):
  uia       expande o caminho do menu pela UI Automation e invoca o item final
  win32     WM_COMMAND com o id do item (menus nativos), sem mexer no menu
  adaptador adaptador.abrir_comando(item) (ex.: COM do app)

Dentro da janela (--dentro), so pela UI Automation e so o que muda a VISAO:
  abas (TabItem), paginas de arvore (TreeItem, ate 60), listas suspensas (ComboBox: abre e fecha sem
  escolher), botoes que so abrem outra janela (lista_negra.classificar_botao) com 1 nivel de profundidade.
  Prints repetidos sao descartados. Controles desenhados pelo app: use alvos_visao.py depois.

Seguranca:
  - pergunta (Save changes?, Are you sure?, Crash Report...) -> Cancel/X e a rodada PARA;
  - seletor de arquivos do Windows -> area de pastas/arquivos TARJADA, sem explorar por dentro;
  - janela que abrir fora da area do app nao e fotografada;
  - app caiu -> restart (adaptador.recuperar ou restart_app.py) e segue do proximo item.

Saida: 03-telas/<ctx>/NN Menu/NNN Caminho.png (+ tela-inteira/) e, com --dentro,
       03-telas/<ctx>/NN Menu/NNN Caminho/NNN estado.png
Logs:  90-relatorios/telas_<ctx>.json e dentro_<ctx>.json

Uso: python crawl_telas.py [--contexto doc-vazio] [--dentro] [--only "File >" ...] [--dry]
     [--incluir "Tools > Macro Manager"] [--config app.json]
     --dry so lista o que seria aberto e o que fica de fora (mostre ao usuario antes da 1a rodada).
"""
import argparse
import time

import lista_negra as ln
import projeto
import winui as w

P = U = None


# ---------------------------------------------------------------- abrir pelo menu
def abrir_uia(item):
    """Expande o caminho e invoca o ultimo item. Devolve (ok, nota)."""
    partes = item["path"].split(" > ")
    els = U.dump(P.mw)
    raiz = next((e for e in els if e["type"] == "MenuItem" and e["parent"].startswith("MenuBar|")
                 and projeto.norm(e["name"]) == projeto.norm(partes[0])), None)
    if not raiz:
        return False, "menu raiz nao encontrado"
    base = {t[0] for t in w.top_windows(P.pid)}
    U.do(P.mw, "expand", raiz["key"], timeout=8)
    hwnd = None
    for i, parte in enumerate(partes[1:], 1):
        pops = w.esperar_popups(P.pid, base, P.mw)  # so as janelas novas (base cresce a cada nivel)
        if not pops:
            return False, f"menu '{' > '.join(partes[:i])}' nao abriu"
        hwnd = max(pops, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))[0]
        base |= {t[0] for t in pops}
        e = next((e for e in U.dump(hwnd) if e["type"] == "MenuItem"
                  and projeto.norm(e["name"]) == projeto.norm(parte)), None)
        if not e:
            return False, f"item '{parte}' nao encontrado (oculto?)"
        if not e["enabled"]:
            return False, "desativado neste contexto"
        if i < len(partes) - 1:
            U.do(hwnd, "expand", e["key"], timeout=8)
        else:
            U.do(hwnd, "invoke", e["key"], timeout=6)  # pode travar se o modal abrir: o cliente reinicia
    return True, ""


def abrir(item):
    modo = P.cfg.get("abrir_telas", "uia")
    if modo == "win32":
        if not item.get("id") or int(item["id"]) <= 0:
            return False, "sem id de comando"
        if not item.get("enabled", True):
            return False, "desativado neste contexto"
        w.comando_win32(P.mw, int(item["id"]))
        return True, ""
    if modo == "adaptador":
        r = P.AD.abrir_comando(item)
        return (True, "") if r is None else r
    return abrir_uia(item)


# ---------------------------------------------------------------- seguranca
def textos(els):
    return " ".join(e["name"] for e in els if e["type"] in ("Text", "Window", "Document")).lower()


def eh_pergunta(els, titulo):
    t = (titulo + " " + textos(els)).lower()
    botoes = {e["name"].lower() for e in els if e["type"] == "Button"}
    return any(p in t for p in ln.PERGUNTAS) and bool(botoes & {"yes", "no", "sim", "não", "don't save", "send"})


def eh_seletor_arquivos(els):
    nomes = {(e["type"], e["name"].lower()) for e in els}
    return (("Tree", "navigation pane") in nomes or ("Tree", "painel de navegação") in nomes
            or ("List", "items view") in nomes or ("List", "exibição de itens") in nomes)


def tarjar_seletor(path, els, wr, origem):
    """Tarja da barra de endereco ate o fim da lista de pastas/arquivos (ficam o tipo de arquivo e os
    botoes). wr = retangulo do dialogo na tela; origem = canto superior esquerdo da imagem na tela."""
    areas = [e["rect"] for e in els if e["type"] in ("Tree", "List") and e["rect"][2] > e["rect"][0]]
    fundo = max(r[3] for r in areas) if areas else wr[1] + int((wr[3] - wr[1]) * 0.75)
    ox, oy = origem
    w.tarjar(path, [(wr[0] - ox, wr[1] + 32 - oy, wr[2] - ox, fundo - oy)])


# ---------------------------------------------------------------- dentro da janela
def explorar_janela(hwnd, pasta, stem, prof=1, vistos=None, regs=None, tela=""):
    """Abas, paginas de arvore, listas suspensas e botoes que abrem janelas. So muda a visao."""
    vistos = vistos if vistos is not None else set()
    regs = regs if regs is not None else []
    limite = P.cfg.get("max_prints_por_tela", 80)
    wr = w.win32gui.GetWindowRect(hwnd)

    def foto(nome, rect=None):
        if len([r for r in regs if r["tela"] == tela]) >= limite or not w.win32gui.IsWindow(hwnd):
            return False
        img = w.esperar_estavel(rect or w.win32gui.GetWindowRect(hwnd), timeout=2)
        a = w.assinatura(img)
        if a in vistos:
            return False
        vistos.add(a)
        f = pasta / f"{len([r for r in regs if r['tela'] == tela]) + 1:03d} {w.safe_name(nome)}.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        img.save(f)
        regs.append({"tela": tela, "estado": nome, "image": projeto.rel(P, f)})
        return True

    foto(f"{stem} inicial")
    els = U.dump(hwnd)
    abas = [e for e in els if e["type"] == "TabItem" and e["enabled"] and "select" in e["patterns"]]
    estados = [None] + abas
    feitos = set()
    for aba in estados:
        if aba:
            U.do(hwnd, "select", aba["key"])
            time.sleep(0.8)
            foto(f"aba > {aba['name']}")
            els = U.dump(hwnd)
        wr = w.win32gui.GetWindowRect(hwnd)
        visiveis = [e for e in els if e["key"] not in feitos and e["enabled"] and e["rect"][2] > e["rect"][0]
                    and w.dentro(e["rect"], wr, 0)]
        arvore = [e for e in visiveis if e["type"] == "TreeItem" and "select" in e["patterns"]][:60]
        for e in arvore:
            feitos.add(e["key"])
            U.do(hwnd, "select", e["key"])
            time.sleep(0.7)
            foto(f"pagina > {e['name']}")
        for e in [e for e in visiveis if e["type"] == "ComboBox" and "expand" in e["patterns"]]:
            feitos.add(e["key"])
            base = {t[0] for t in w.top_windows(P.pid)}
            U.do(hwnd, "expand", e["key"])
            time.sleep(0.7)
            pops = w.popups_novos(P.pid, base, P.mw)
            rect = w.union([wr] + [t[3] for t in pops]) if pops else None
            foto(f"lista > {e['name'] or e['auto_id'] or 'sem nome'}", rect)
            U.do(hwnd, "collapse", e["key"])
            time.sleep(0.3)
            if [t for t in w.popups_novos(P.pid, base, P.mw) if w.eh_menu(t)]:
                w.esc()
        if prof > 0:
            for e in [e for e in visiveis if e["type"] in ("Button", "SplitButton") and "invoke" in e["patterns"]]:
                feitos.add(e["key"])
                acao, motivo = ln.classificar_botao(e["name"])
                if acao != "clica":
                    continue
                base = {t[0] for t in w.top_windows(P.pid)}
                U.do(hwnd, "invoke", e["key"], timeout=5)
                time.sleep(P.cfg.get("espera_janela", 2.5))
                novos = [t for t in w.popups_novos(P.pid, base, P.mw)]
                for t in novos:
                    filho_els = U.dump(t[0])
                    if eh_pergunta(filho_els, t[2]):
                        w.fechar_dialogo(t[0])
                        raise SystemExit(f"!! pergunta inesperada depois do botao {e['name']!r}: {t[2]!r}")
                for t in [t for t in novos if not w.eh_menu(t)]:
                    sub = pasta / f"botao > {w.safe_name(e['name'])}"
                    explorar_janela(t[0], sub, "", 0, vistos, regs, tela)
                    w.fechar_dialogo(t[0])
                for t in [t for t in novos if w.eh_menu(t)]:
                    foto(f"botao > {e['name']} (menu)", w.union([wr, t[3]]))
                    w.esc()
    if abas:
        U.do(hwnd, "select", abas[0]["key"])
    return regs


# ---------------------------------------------------------------- uma tela
def uma_tela(n_raiz, seq, item, ctx, dentro, log, log_dentro):
    rec = {"path": item["path"], "contexto": ctx, "status": "", "image": "", "note": "", "window_title": ""}
    raiz = item["path"].split(" > ")[0]
    pasta = P.ROOT / "03-telas" / ctx / f"{n_raiz:02d} {w.safe_name(raiz)}"
    nome = f"{seq:03d} {w.safe_name(item['path'])}"
    projeto.montar_contexto(P, ctx)
    w.force_foreground(P.mw)
    base = {t[0] for t in w.top_windows(P.pid)}
    antes = w.grab(w.win32gui.GetWindowRect(P.mw))
    ok, nota = abrir(item)
    if not ok:
        w.esc(3)
        rec.update(status="nao_abriu", note=nota)
        return rec
    t0, jan = time.time(), []
    while time.time() - t0 < P.cfg.get("espera_janela", 2.5) + 3 and not jan:
        time.sleep(0.3)
        jan = [t for t in w.popups_novos(P.pid, base, P.mw) if not w.eh_menu(t)]
    fora = [t for t in w.janelas_fora(P.pid, base, P.mw) if not w.eh_menu(t)]
    if not jan and fora:
        for t in fora:
            w.fechar_dialogo(t[0])
        rec.update(status="erro", note="abriu janela fora da area do app (nao fotografada; mova o app)")
        return rec
    if not jan:
        w.esc(3)
        time.sleep(0.5)
        depois = w.grab(w.win32gui.GetWindowRect(P.mw))
        if w.mudou(antes, depois):
            f = pasta / "tela-inteira" / f"{nome} (sem janela, tela principal).png"
            f.parent.mkdir(parents=True, exist_ok=True)
            depois.save(f)
            rec.update(status="sem_janela", image=projeto.rel(P, f), note="o comando mudou a tela sem abrir janela")
        else:
            rec.update(status="sem_janela", note="nada abriu")
        return rec
    h = max(jan, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
    wr = w.win32gui.GetWindowRect(h[0])
    els = U.dump(h[0])
    rec["window_title"] = h[2]
    if eh_pergunta(els, h[2]):
        w.fechar_dialogo(h[0])
        raise SystemExit(f"!! pergunta inesperada ao abrir {item['path']!r}: {h[2]!r} -> Cancel; rodada parada")
    img = w.esperar_estavel(wr)
    f = pasta / f"{nome}.png"
    f.parent.mkdir(parents=True, exist_ok=True)
    img.save(f)
    w.grab(w.union([w.win32gui.GetWindowRect(P.mw), wr]), pasta / "tela-inteira" / f"{nome}.png")
    rec.update(status="ok", image=projeto.rel(P, f))
    if eh_seletor_arquivos(els):
        tarjar_seletor(f, els, wr, wr[:2])
        tarjar_seletor(pasta / "tela-inteira" / f"{nome}.png", els, wr,
                       w.union([w.win32gui.GetWindowRect(P.mw), wr])[:2])
        rec["note"] = "seletor de arquivos: pastas/arquivos tarjados (conferir); nao explorado por dentro"
    elif dentro:
        try:
            log_dentro.extend(explorar_janela(h[0], pasta / nome, "", 1, set(), [], item["path"]))
        except SystemExit:
            raise
        except Exception as e:
            rec["note"] = f"erro ao explorar por dentro: {e}"[:200]
    for t in [t for t in w.popups_novos(P.pid, base, P.mw) if t[0] != h[0]]:
        w.fechar_dialogo(t[0])
    if not w.fechar_dialogo(h[0]):
        w.esc()
        time.sleep(0.5)
        if w.win32gui.IsWindow(h[0]) and w.win32gui.IsWindowVisible(h[0]):
            raise SystemExit(f"!! nao consegui fechar {h[2]!r}: pare e veja com o usuario")
    return rec


def main():
    global P, U
    ap = argparse.ArgumentParser()
    ap.add_argument("--contexto", default="doc-vazio")
    ap.add_argument("--dentro", action="store_true")
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--incluir", nargs="*", default=[])
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--config")
    a = ap.parse_args()
    P = projeto.carregar(a.config)
    inv = projeto.inventario(P)
    fora = set(P.cfg.get("menus_fora", [])) | ln.MENUS_FORA
    raizes = [x["caption"] for x in inv if x["kind"] == "menu_root"]
    itens = [x for x in inv if x["kind"] == "menu_item" and not x["has_submenu"]
             and (x["abre_janela"] or x["path"] in a.incluir)]
    if a.only:
        itens = [x for x in itens if any(x["path"].startswith(o) for o in a.only)]
    log, log_dentro, abrir_lista = [], [], []
    for x in itens:
        raiz = x["path"].split(" > ")[0]
        motivo = f"fora do escopo: menu {raiz}" if raiz in fora else ln.item_bloqueado(x["path"])
        if motivo and x["path"] not in a.incluir:
            log.append({"path": x["path"], "contexto": a.contexto, "status": "nao_aberto", "image": "",
                        "note": motivo})
        else:
            abrir_lista.append(x)
    print(f"{len(abrir_lista)} telas para abrir; {len(log)} de fora")
    if a.dry:
        for x in abrir_lista:
            print("  abre:", x["path"])
        for r in log:
            print("  NAO :", r["path"], "|", r["note"])
        return
    U = w.UIA()
    seq = {}
    try:
        for x in abrir_lista:
            raiz = x["path"].split(" > ")[0]
            n_raiz = raizes.index(raiz) + 1 if raiz in raizes else 99
            seq[raiz] = seq.get(raiz, 0) + 1
            if not w.vivo(P.pid, P.mw):
                projeto.recuperar(P, "app nao esta rodando ou nao responde")
            try:
                rec = uma_tela(n_raiz, seq[raiz], x, a.contexto, a.dentro, log, log_dentro)
            except SystemExit:
                raise
            except Exception as e:
                rec = {"path": x["path"], "contexto": a.contexto, "status": "erro", "image": "", "note": str(e)[:200]}
                if not w.vivo(P.pid, P.mw):
                    rec["note"] = "app caiu: " + rec["note"]
                    log.append(rec)
                    projeto.recuperar(P, str(e)[:120])
                    continue
            log.append(rec)
            print(f"  [{rec['status']}] {x['path']} {rec['note']}", flush=True)
    finally:
        U.fechar()
        feitos = {r["path"] for r in log}
        projeto.salvar_log(P, f"telas_{a.contexto}", log, lambda r: r["path"] in feitos)
        telas = {r["tela"] for r in log_dentro}
        f = projeto.salvar_log(P, f"dentro_{a.contexto}", log_dentro, lambda r: r.get("tela") in telas)
        print(f"{len(log)} telas no log; {len(log_dentro)} prints por dentro -> {f.parent}")


if __name__ == "__main__":
    main()
