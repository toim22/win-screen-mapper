"""Etapa 6b: caixa de ferramentas, flyouts e barra de propriedades de cada ferramenta.

1. flyouts: clica no triangulo de cada botao da caixa de ferramentas que tem flyout e fotografa.
2. ferramentas: ativa cada ferramenta (pelo GUID) num contexto adequado e fotografa a barra de
   propriedades (recorte) + a janela inteira. Ativar ferramenta nao altera o documento.
3. pick: barra de propriedades da ferramenta Pick em cada contexto de objeto (ela muda conforme
   o que esta selecionado).

Saida: 05-ferramentas/{flyouts,barra-de-propriedades,barra-pick-por-contexto}/
Log:   90-relatorios/ferramentas.json
Uso: python crawl_ferramentas.py [flyouts] [ferramentas] [pick]
"""
import json
import sys
import time

import win32gui

import crawl_telas as ct
from contextos import CONTEXTOS, build, reset_doc
from corelui import click, force_foreground, grab, key, safe_name, win32con

ROOT = ct.ROOT
TOOLBOX = "7c905e2a-cb64-4ba1-aff0-c306f392680c"
PROP_Y = (88, 137)  # faixa da barra de propriedades, relativa ao topo da janela principal
OUT = ROOT / "05-ferramentas"
DOCKER_NAME = {x["guid"]: x["caption"] for x in json.loads(
    (ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8")) if x["kind"] == "docker"}
# ferramenta -> contexto em que a barra de propriedades mostra mais coisa
CTX = {"Shape": "curva", "Smooth": "curva", "Smear": "curva", "Twirl": "curva", "Attract and Repel": "curva",
       "Smudge": "curva", "Roughen": "curva", "Text": "texto-artistico", "Table": "tabela",
       "Parallel Dimension": "linha-de-cota", "Horizontal or Vertical Dimension": "linha-de-cota",
       "Angular Dimension": "linha-de-cota", "Segment Dimension": "linha-de-cota", "2-Leg Callout": "linha-de-cota",
       "Connector": "conector", "Anchor Editing": "conector", "Crop": "bitmap"}
log = []


def clean(c):
    return (c or "").replace("&", "").strip()


def toolbox():
    """[(indice, guid, legenda, rect, [(guid, legenda) da flyout])]"""
    def f(app, au):
        out = []
        for i in range(au.GetNumItemsOnBar(TOOLBOX)):
            g, has = au.GetItem(TOOLBOX, i)
            ok, x, y, w, h = au.GetItemScreenRect(TOOLBOX, g)
            if not ok or h < 10:
                continue  # separador ou botao fora da caixa
            sub = []
            if has:
                ok2, sb = au.GetSubBar(g)
                for j in range(au.GetNumItemsOnBar(sb) if ok2 else 0):
                    gg, _ = au.GetItem(sb, j)
                    if clean(au.GetCaptionText(gg)):
                        sub.append((gg, clean(au.GetCaptionText(gg))))
            else:
                sub.append((g, clean(au.GetCaptionText(g))))
            out.append((i, g, clean(au.GetCaptionText(g)), (x, y, x + w, y + h), has, sub))
        return out
    return ct.com(f)


def visible_dockers():
    out = set()
    for g in DOCKER_NAME:
        try:
            if ct.com(lambda a, u: a.FrameWork.IsDockerVisible(g)):
                out.add(g)
        except Exception:
            pass
    return out


def save_log():
    f = ROOT / "90-relatorios" / "ferramentas.json"
    old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    keys = {(r["parte"], r["nome"]) for r in log}
    f.write_text(json.dumps([r for r in old if (r["parte"], r["nome"]) not in keys] + log, ensure_ascii=False,
                            indent=1), encoding="utf-8")


def flyouts(tb):
    out = OUT / "flyouts"
    out.mkdir(parents=True, exist_ok=True)
    ct.com(lambda app, au: build(app, "retangulo"))
    full = win32gui.GetWindowRect(ct.mw)
    grab((full[0], full[1] + 135, full[0] + 45, full[3] - 60), out / "000 caixa de ferramentas.png")
    for i, g, cap, r, has, sub in tb:
        if not has:
            continue
        nome = f"{i + 1:02d} flyout " + " ▸ ".join(s[1] for s in sub[:1]) + f" ({len(sub)} itens)"
        force_foreground(ct.mw)
        base = {t[0] for t in ct.top_windows(ct.pid)}
        click(r[2] - 3, r[3] - 3)
        time.sleep(1)
        pop = [t for t in ct.top_windows(ct.pid) if t[0] not in base and t[1].startswith("Afx:")]
        if pop:
            p = pop[0][3]
            grab((r[0] - 4, min(r[1], p[1]) - 4, p[2] + 4, max(r[3], p[3]) + 4), out / (safe_name(nome) + ".png"))
            st = "ok"
        else:
            st = "nao_abriu"
        log.append({"parte": "flyout", "nome": nome, "status": st, "itens": [s[1] for s in sub]})
        print(f"  [{st}] {nome}", flush=True)
        key(win32con.VK_ESCAPE)
        time.sleep(0.4)
    save_log()


def shoot_prop(folder, name):
    full = win32gui.GetWindowRect(ct.mw)
    grab((full[0], full[1] + PROP_Y[0], full[2], full[1] + PROP_Y[1]), folder / name)
    grab(full, folder / "tela-inteira" / name)


def ferramentas(tb):
    out = OUT / "barra-de-propriedades"
    (out / "tela-inteira").mkdir(parents=True, exist_ok=True)
    dock0 = visible_dockers()
    n = 0
    for i, g, cap, r, has, sub in tb:
        for gg, nome in sub:
            n += 1
            ctx = CTX.get(nome, "retangulo")
            ct.com(lambda app, au: build(app, ctx))
            force_foreground(ct.mw)
            base = {t[0] for t in ct.top_windows(ct.pid)}
            ct.com(lambda app, au: au.InvokeItem(gg))
            time.sleep(1.2)
            fname = f"{n:03d} {safe_name(nome)} ({ctx}).png"
            shoot_prop(out, fname)
            rec = {"parte": "ferramenta", "nome": nome, "guid": gg, "contexto": ctx, "status": "ok",
                   "image": str((out / fname).relative_to(ROOT)), "note": ""}
            novos = visible_dockers() - dock0
            if novos:
                rec["note"] = f"abriu docker {[DOCKER_NAME.get(d, d) for d in novos]} (aparece no print da tela inteira)"
                for d in novos:
                    ct.com(lambda app, au: app.FrameWork.HideDocker(d))
            win = [t for t in ct.new_windows(base) if t[1] not in ("SysShadow", "tooltips_class32")]
            if win:
                big = max(win, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
                grab(big[3], out / f"{n:03d} {safe_name(nome)} ▸ janela {safe_name(big[2] or big[1])}.png")
                rec["note"] += f" abriu janela {big[2] or big[1]!r}"
                for t in win:
                    ct.close_window(t[0])
            print(f"  [{rec['status']}] {nome} ({ctx}) {rec['note']}", flush=True)
            log.append(rec)
            key(win32con.VK_ESCAPE, 2)
            ct.com(lambda app, au: setattr(app, "ActiveTool", 1))
            save_log()
            if [t for t in ct.new_windows(base) if t[1] not in ("SysShadow", "tooltips_class32")]:
                raise SystemExit(f"!! janela sobrou depois de {nome}")


def pick():
    out = OUT / "barra-pick-por-contexto"
    (out / "tela-inteira").mkdir(parents=True, exist_ok=True)
    from contextos import reset_doc as rd
    for k, ctx in enumerate(["doc-vazio"] + list(CONTEXTOS), 1):
        if ctx == "doc-vazio":
            ct.com(lambda app, au: rd(app))
        else:
            ct.com(lambda app, au: build(app, ctx))
        ct.com(lambda app, au: setattr(app, "ActiveTool", 1) if ctx != "tabela-celulas" else None)
        force_foreground(ct.mw)
        time.sleep(1)
        fname = f"{k:02d} Pick com {ctx}.png"
        shoot_prop(out, fname)
        log.append({"parte": "pick", "nome": ctx, "status": "ok", "image": str((out / fname).relative_to(ROOT))})
        print(f"  [ok] pick {ctx}", flush=True)
    save_log()


if __name__ == "__main__":
    partes = sys.argv[1:] or ["flyouts", "ferramentas", "pick"]
    tb = toolbox()
    if "flyouts" in partes:
        flyouts(tb)
    if "ferramentas" in partes:
        ferramentas(tb)
    if "pick" in partes:
        pick()
    ct.com(lambda app, au: reset_doc(app))
    print("ok")
