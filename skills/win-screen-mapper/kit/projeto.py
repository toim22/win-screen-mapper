"""projeto.py: carrega o app.json do projeto e prepara winui, pastas e logs.

Todos os scripts do kit comecam com:
    import projeto
    P = projeto.carregar()          # le app.json (pasta do script ou --config)
    P.ROOT, P.pid, P.mw, P.cfg, P.AD (adaptador ou None)

Formato de log padrao (um JSON por rodada em 90-relatorios): lista de registros com
    path (caminho "Menu > Item"), status, image (relativo ao ROOT), note, contexto, + campos livres.
status: ok | docker | sem_janela | nao_abriu | nao_aberto | oculto | sem_submenu | erro
"""
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

import winui as w

AQUI = Path(__file__).resolve().parent


class Projeto:
    pass


def carregar(caminho=None, precisa_app=True):
    cfgp = Path(caminho) if caminho else None
    if cfgp is None:
        for i, a in enumerate(sys.argv):
            if a == "--config" and i + 1 < len(sys.argv):
                cfgp = Path(sys.argv[i + 1])
    cfgp = cfgp or AQUI / "app.json"
    if not cfgp.exists():
        raise SystemExit(f"falta {cfgp}: copie app_modelo.json como app.json e preencha")
    cfg = json.loads(cfgp.read_text(encoding="utf-8"))
    w.configurar(cfg["exe"], cfg.get("titulo"), cfg.get("classe_principal") or None, cfg.get("classes_menu"))
    P = Projeto()
    P.cfg, P.cfg_path = cfg, cfgp
    P.ROOT = Path(cfg["saida"])
    P.R = P.ROOT / "90-relatorios"
    P.R.mkdir(parents=True, exist_ok=True)
    P.AD = None
    if cfg.get("adaptador"):
        sys.path.insert(0, str(cfgp.parent))
        P.AD = importlib.import_module(cfg["adaptador"])
    P.pid = P.mw = None
    if precisa_app:
        conectar(P)
    return P


def conectar(P):
    P.pid = w.app_pid()
    if not P.pid:
        raise SystemExit(f"{P.cfg['exe']} nao esta rodando: abra o app (ou rode restart_app.py)")
    P.mw = w.main_window(P.pid)
    if not P.mw:
        raise SystemExit("nao achei a janela principal: confira 'titulo'/'classe_principal' no app.json")
    return P


def recuperar(P, motivo):
    """App caiu/travou. Usa adaptador.recuperar() se existir; senao restart_app.py (deve imprimir 'pronto').
    O Crash Report e fechado pelo X dentro do restart (NUNCA enviar)."""
    print(f"  !! recuperando o app: {motivo}", flush=True)
    if P.AD and hasattr(P.AD, "recuperar"):
        P.AD.recuperar(motivo)
    else:
        rs = P.cfg_path.parent / "restart_app.py"
        if not rs.exists():
            raise SystemExit(f"o app caiu ({motivo}) e nao ha restart_app.py: pare e avise o usuario")
        w.matar_app()
        out = subprocess.run([sys.executable, str(rs), "--no-close"], capture_output=True, text=True,
                             encoding="utf-8")
        if "pronto" not in out.stdout:
            raise SystemExit("nao consegui reabrir o app: " + out.stdout[-600:] + out.stderr[-600:])
    time.sleep(2)
    return conectar(P)


def montar_contexto(P, nome):
    """Chama adaptador.montar_contexto(nome) se existir (ex.: documento novo + objeto selecionado)."""
    if P.AD and hasattr(P.AD, "montar_contexto"):
        P.AD.montar_contexto(nome)
        time.sleep(0.5)


def rel(P, path):
    try:
        return str(Path(path).relative_to(P.ROOT))
    except ValueError:
        return str(path)


def salvar_log(P, nome, registros, substituir=None):
    """Grava 90-relatorios/<nome>.json. substituir(reg_antigo)->bool: quais registros antigos saem
    (rodadas parciais com --only nao apagam o resto)."""
    f = P.R / f"{nome}.json"
    antigo = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    if substituir:
        antigo = [r for r in antigo if not substituir(r)]
    else:
        antigo = []
    f.write_text(json.dumps(antigo + registros, ensure_ascii=False, indent=1), encoding="utf-8")
    return f


def inventario(P):
    f = P.ROOT / "01-inventario" / "inventory.json"
    if not f.exists():
        raise SystemExit("rode inventario.py antes (etapa 1)")
    return json.loads(f.read_text(encoding="utf-8"))


def norm(s):
    return w.limpa_rotulo(s).lower().rstrip(".").strip()
