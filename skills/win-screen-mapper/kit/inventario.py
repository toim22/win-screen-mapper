"""inventario.py: etapa 1, a lista-mestra dos menus de qualquer app.

Fontes (escolha com --fonte; padrao = "rota_menus" do app.json):
  uia       UI Automation: expande cada menu da barra e cada submenu (abre os menus na tela, mas
            NAO executa nenhum item). Serve para Win32 padrao, WPF, WinForms, boa parte do Qt.
  win32     menus nativos (HMENU) lidos direto, sem abrir nada. Classicos Win32/MFC com menu padrao.
            Submenus montados na hora podem vir vazios: --completar abre cada menu da barra e rele.
  adaptador adaptador.inventario() devolve a lista (ex.: modelo COM do app, arquivo XML de interface).
            Pode trazer tambem definicoes que nao estao em menu (kind dialog/docker/toolbar).

Saida: MAPEAMENTO/01-inventario/inventory.json e inventory.csv. Campos:
  source, kind (menu_root|menu_item|...), path ("File > Open..."), caption, id, index,
  has_submenu, enabled, abre_janela (termina em "..."), nota

Uso: python inventario.py [--fonte uia|win32|adaptador] [--completar] [--config app.json]
"""
import argparse
import csv
import json
import time

import projeto
import winui as w

CAMPOS = ["source", "kind", "path", "caption", "id", "index", "has_submenu", "enabled", "abre_janela", "nota"]


def item(source, kind, path, caption, **kw):
    d = {"source": source, "kind": kind, "path": path, "caption": caption, "id": kw.get("id", ""),
         "index": kw.get("index", ""), "has_submenu": bool(kw.get("has_submenu")),
         "enabled": kw.get("enabled", True), "abre_janela": caption.rstrip().endswith(("...", "…")),
         "nota": kw.get("nota", "")}
    return d


# ---------------------------------------------------------------- UIA
def via_uia(P, fora):
    U = w.UIA()
    try:
        els = U.dump(P.mw)
        raizes = [e for e in els if e["type"] == "MenuItem" and e["parent"].startswith("MenuBar|")
                  and e["parent"] not in ("MenuBar|System", "MenuBar|Sistema")]  # menu de sistema da janela
        if not raizes:
            raise SystemExit("a UI Automation nao enxerga uma barra de menus neste app: tente --fonte win32, "
                             "adaptador, ou a rota visao (menus_raiz_manual no app.json)")
        out = []
        for i, r in enumerate(raizes):
            cap = w.limpa_rotulo(r["name"])
            out.append(item("uia", "menu_root", cap, cap, id=r["auto_id"], index=i, has_submenu=True,
                            enabled=r["enabled"]))
            if cap in fora:
                out[-1]["nota"] = "fora do escopo (nao aberto)"
                continue
            print(f"== {cap}", flush=True)
            w.force_foreground(P.mw)
            base = {t[0] for t in w.top_windows(P.pid)}
            U.do(P.mw, "expand", r["key"], timeout=8)
            pops = w.esperar_popups(P.pid, base, P.mw)
            if not pops:  # alguns apps so abrem com clique
                x0, y0, x1, y1 = r["rect"]
                w.click((x0 + x1) // 2, (y0 + y1) // 2)
                pops = w.esperar_popups(P.pid, base, P.mw)
            if not pops:
                out[-1]["nota"] = "menu nao abriu"
                continue
            pop = max(pops, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
            _uia_popup(P, U, pop[0], [cap], base | {pop[0]}, out)
            w.esc(4)
            time.sleep(0.4)
        return out
    finally:
        U.fechar()


def _uia_popup(P, U, hwnd, caminho, conhecidos, out, nivel=0):
    els = [e for e in U.dump(hwnd) if e["type"] == "MenuItem"]
    for e in els:
        cap = w.limpa_rotulo(e["name"])
        if not cap:
            continue
        tem_sub = "expand" in e["patterns"]
        path = " > ".join(caminho + [cap])
        out.append(item("uia", "menu_item", path, cap, id=e["auto_id"], has_submenu=tem_sub, enabled=e["enabled"]))
        if not (tem_sub and e["enabled"]) or nivel > 6:
            continue
        U.do(hwnd, "expand", e["key"], timeout=8)
        t0, sub = time.time(), None
        while time.time() - t0 < 2.5 and not sub:
            novos = [t for t in w.popups_novos(P.pid, conhecidos, P.mw) if t[0] != hwnd]
            sub = max(novos, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1])) if novos else None
            time.sleep(0.1)
        if not sub:
            out[-1]["nota"] = "submenu nao abriu"
            continue
        _uia_popup(P, U, sub[0], caminho + [cap], conhecidos | {sub[0]}, out, nivel + 1)
        U.do(hwnd, "collapse", e["key"], timeout=5)
        t0 = time.time()
        while time.time() - t0 < 2 and w.win32gui.IsWindowVisible(sub[0]):
            time.sleep(0.1)
        if w.win32gui.IsWindowVisible(sub[0]):
            w.esc()
            time.sleep(0.3)


# ---------------------------------------------------------------- Win32 (HMENU)
def via_win32(P, fora, completar):
    hm = w.user32.GetMenu(P.mw)
    if not hm:
        raise SystemExit("a janela principal nao tem menu Win32 nativo (GetMenu = 0): use --fonte uia/adaptador/visao")
    raizes = w.menu_win32(hm, profundidade=1)
    out = []
    for r in raizes:
        if r["separator"] or not r["caption"]:
            continue
        out.append(item("win32", "menu_root", r["caption"], r["caption"], id=r["id"], index=r["index"],
                        has_submenu=r["has_submenu"], enabled=r["enabled"]))
        if r["caption"] in fora:
            out[-1]["nota"] = "fora do escopo (nao aberto)"
            continue
        if completar and r["sub"]:  # abre o menu para o app montar os itens (WM_INITMENUPOPUP)
            rect = w.rect_item_win32(P.mw, hm, r["index"])
            if rect:
                w.force_foreground(P.mw)
                w.click((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
                time.sleep(0.8)
        filhos = w.menu_win32(r["sub"], (r["caption"],)) if r["sub"] else []
        if completar:
            w.esc(3)
            time.sleep(0.3)

        def achata(lst):
            for f in lst:
                if f["separator"] or not f["caption"]:
                    continue
                out.append(item("win32", "menu_item", f["path"], f["caption"], id=f["id"], index=f["index"],
                                has_submenu=f["has_submenu"], enabled=f["enabled"],
                                nota="submenu vazio no inventario (montado na hora)"
                                if f["has_submenu"] and not f.get("filhos") else ""))
                achata(f.get("filhos", []))
        achata(filhos)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    ap.add_argument("--fonte", choices=["uia", "win32", "adaptador"])
    ap.add_argument("--completar", action="store_true", help="win32: abre cada menu antes de ler")
    a = ap.parse_args()
    P = projeto.carregar(a.config)
    fonte = a.fonte or {"visao": "uia"}.get(P.cfg.get("rota_menus"), P.cfg.get("rota_menus", "uia"))
    fora = set(P.cfg.get("menus_fora", []))
    if fonte == "uia":
        inv = via_uia(P, fora)
    elif fonte == "win32":
        inv = via_win32(P, fora, a.completar)
    else:
        if not (P.AD and hasattr(P.AD, "inventario")):
            raise SystemExit("o adaptador precisa de inventario() -> lista no formato do inventory.json")
        inv = [dict(item(x.get("source", "adaptador"), x["kind"], x["path"], x.get("caption", x["path"])), **x)
               for x in P.AD.inventario()]
    d = P.ROOT / "01-inventario"
    d.mkdir(parents=True, exist_ok=True)
    (d / "inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(d / "inventory.csv", "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=";", extrasaction="ignore")
        wr.writeheader()
        wr.writerows(inv)
    kinds = {}
    for x in inv:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    print(f"{len(inv)} itens {kinds}; abrem janela: {sum(x['abre_janela'] for x in inv)} -> {d}")


if __name__ == "__main__":
    main()
