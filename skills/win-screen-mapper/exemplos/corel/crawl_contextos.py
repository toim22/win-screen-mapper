"""Etapa 5 (telas): abre as telas que estavam desativadas no documento vazio, cada uma no
primeiro contexto de objeto em que ela fica ativa (matriz_contextos.json).

Antes de CADA tela o contexto e remontado do zero (documento descartavel novo + objetos), para
que modos de edicao (simbolo, PowerClip, conta-gotas) de uma tela nao contaminem a seguinte.
Efeitos e Bitmaps preferem o contexto "bitmap" quando ele liga o item.

Quando o item nao abre janela (ex.: entra num modo, abre docker), fotografa a janela principal
para registrar o que aconteceu, fecha dockers que tenham aberto e cancela o modo com Esc.

Saida: 03-telas/<contexto>/...    Log: 90-relatorios/telas_contextos.json
Uso: python crawl_contextos.py [--only "Effects > Blur"] [--list]
"""
import argparse
import json
import time

import crawl_telas as ct
from contextos import CONTEXTOS, build
from corelui import force_foreground, grab, key, safe_name, win32con, win32gui

ROOT = ct.ROOT
# Lista negra extra da etapa 5 (mesmos criterios aprovados: exportar, enviar, outro programa, web)
SKIP5 = {
    "File > Export For > Office...": "lista negra: exportar",
    "File > Export For > Web...": "lista negra: exportar",
    "File > Export For > WordPress...": "lista negra: exportar / conta WordPress",
    "File > Send To > Mail...": "lista negra: envia e-mail",
    "Bitmaps > Edit Bitmap...": "abre outro programa (Corel PHOTO-PAINT)",
    "Help > Share Your Experience...": "Help: abre navegador/feedback (usuario: so menus do Help)",
}
DOCKER_NAME = {x["guid"]: x["caption"] for x in json.loads(
    (ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8")) if x["kind"] == "docker"}
DOCKERS = list(DOCKER_NAME)


def visible_dockers():
    out = set()
    for g in DOCKERS:
        try:
            if ct.com(lambda a, u: a.FrameWork.IsDockerVisible(g)):
                out.add(g)
        except Exception:
            pass
    return out


def escolher(path, mat):
    on = [c for c in CONTEXTOS if mat[c].get(path)]
    if not on:
        return None
    if path.startswith(("Effects >", "Bitmaps >")) and "bitmap" in on:
        return "bitmap"
    return on[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    inv = json.loads((ROOT / "01-inventario" / "inventory.json").read_text(encoding="utf-8"))
    roots = {x["caption"]: x["index"] + 1 for x in inv if x["kind"] == "menu_root"}
    order, cnt = {}, {}
    for x, _ in ct.candidates(inv):
        r0 = x["path"].split(" > ")[0]
        cnt[r0] = cnt.get(r0, 0) + 1
        order[x["path"]] = cnt[r0]
    byp = {x["path"]: x for x in inv if x["kind"] == "menu_item"}
    vazio = json.loads((ROOT / "90-relatorios" / "telas_doc-vazio.json").read_text(encoding="utf-8"))
    mat = json.loads((ROOT / "90-relatorios" / "matriz_contextos.json").read_text(encoding="utf-8"))
    todo = [byp[t["path"]] for t in vazio if t["status"] == "desativado"]
    if a.only:
        todo = [x for x in todo if any(x["path"].startswith(o) for o in a.only)]

    log = []

    def rec(x, status, img="", title="", note="", cls=""):
        log.append({"path": x["path"], "guid": x["guid"], "contexto": x.get("_ctx", ""), "status": status,
                    "image": img, "window_title": title, "window_class": cls, "note": note})
        print(f"  [{status}] ({x.get('_ctx', '')}) {x['path']} {('-> ' + title) if title else ''} {note}",
              flush=True)

    plano = []
    for x in todo:
        x = dict(x)
        x["_ctx"] = escolher(x["path"], mat) or ""
        plano.append(x)
        if a.list:
            print(f"{x['_ctx'] or '(nenhum)':18s} {x['path']}  {SKIP5.get(x['path'], '')}")
    if a.list:
        return

    logf = ROOT / "90-relatorios" / "telas_contextos.json"
    old = json.loads(logf.read_text(encoding="utf-8")) if logf.exists() else []

    def save():  # grava a cada tela: se a automacao travar, o que ja foi feito fica no log
        feitos = {r["path"] for r in log}
        logf.write_text(json.dumps([r for r in old if r["path"] not in feitos] + log, ensure_ascii=False,
                                   indent=1), encoding="utf-8")

    dock0 = visible_dockers()
    t0, parou = time.time(), None
    for x in plano:
        if x["path"] in SKIP5:
            rec(x, "nao_aberto", note=SKIP5[x["path"]])
            continue
        if not x["_ctx"]:
            rec(x, "desativado", note="desativado em todos os contextos testados")
            continue
        ct.com(lambda app, au: build(app, x["_ctx"]))
        if not ct.com(lambda app, au: au.IsEnabled(x["guid"])):
            rec(x, "desativado", note="nao ligou ao remontar o contexto")
            continue
        n0 = len(log)
        stop = ct.capture(x, x["_ctx"], order, roots, rec)
        if log[n0:] and log[n0]["status"] == "sem_janela":
            # registra o que aconteceu na janela principal. No Corel 2026 os efeitos nao abrem
            # janela: entram no objeto e os ajustes aparecem no docker Properties.
            time.sleep(1.5)
            novos = visible_dockers() - dock0
            nomes = [DOCKER_NAME.get(g, g) for g in sorted(novos)]
            parts = x["path"].split(" > ")
            folder = ROOT / "03-telas" / x["_ctx"] / f"{roots.get(parts[0], 0):02d} {safe_name(parts[0])}"
            folder.mkdir(parents=True, exist_ok=True)
            suf = f" (abre no docker {', '.join(nomes)})" if novos else " (sem janela, tela principal)"
            name = f"{order[x['path']]:03d} " + safe_name(" ▸ ".join(parts)) + suf + ".png"
            grab(win32gui.GetWindowRect(ct.mw), folder / name)
            log[n0]["image"] = str((folder / name).relative_to(ROOT))
            if novos:
                log[n0]["status"] = "docker"
                log[n0]["note"] = f"sem janela; abriu o docker {', '.join(nomes)}"
                for g in novos:
                    ct.com(lambda app, au: app.FrameWork.HideDocker(g))
            force_foreground(ct.mw)
            key(win32con.VK_ESCAPE, 2)
        save()
        if stop:
            parou = f"parada de seguranca em {x['path']}"
            print("!!", parou, flush=True)
            break
    from contextos import reset_doc
    ct.com(lambda app, au: reset_doc(app))
    (ROOT / "_tmp.png").unlink(missing_ok=True)
    save()
    print(f"{len(log)} registros em {time.time() - t0:.0f}s -> {logf}")
    if parou:
        raise SystemExit(parou)


if __name__ == "__main__":
    main()
