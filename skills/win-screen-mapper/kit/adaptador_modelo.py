"""adaptador_modelo.py: a parte especifica de UM app. Copie como adaptador_<app>.py e ponha o nome
(sem .py) em app.json -> "adaptador". Implemente so o que o app precisar; tudo e opcional, exceto
abrir/fechar para o alvos_visao.py.

Funcoes que os scripts do kit procuram:
  iniciar(P)                 uma vez no comeco (P = projeto carregado: P.pid, P.mw, P.cfg, P.ROOT)
  montar_contexto(nome)      deixa o app no contexto ("doc-vazio", "retangulo", "texto"...) via
                             automacao do app (COM, script) ou cliques; chamado antes de cada menu raiz
  abrir_comando(item)        abre o comando de um item do inventario (rota "adaptador" do crawl_telas):
                             ex.: COM ExecuteCommand/InvokeItem(item["id"]). NAO bloqueie: se a chamada
                             for modal, rode em subprocesso (ver exemplos/corel/invoke_one.py)
  abrir(alvo) -> rect|None   alvos_visao: abre o painel/janela do alvo["painel"] e devolve o retangulo
  fechar(alvo)               alvos_visao: fecha o que abrir() abriu, sem confirmar nada
  fechar_janela(hwnd)        se Cancel/X padrao nao servir para as janelas do app
  recuperar(motivo)          app caiu: matar, reabrir, estado base (senao o kit usa restart_app.py)

Abaixo, um abrir/fechar GENERICO por diferenca de janelas: funciona para paineis que sao janelas
filhas novas ou janelas top-level novas. Ajuste COMO abrir (atalho, menu, comando).
"""
import time

import winui as w

P = None
_aberto = {}


def iniciar(p):
    global P
    P = p


def montar_contexto(nome):
    # Ex.: documento novo descartavel + um objeto do tipo `nome` selecionado, via automacao do app.
    pass


def _disparar(painel):
    """AJUSTE: como abrir o painel/janela `painel` (comando por id, menu por UIA, atalho de teclado...)."""
    raise NotImplementedError("diga no adaptador como abrir o painel " + painel)


def abrir(alvo):
    w.force_foreground(P.mw)
    montar_contexto(alvo.get("contexto", "doc-vazio"))
    filhos0 = set(w.child_windows(P.mw))
    tops0 = {t[0] for t in w.top_windows(P.pid)}
    _disparar(alvo["painel"])
    time.sleep(P.cfg.get("espera_janela", 2.5))
    tops = [t for t in w.popups_novos(P.pid, tops0, P.mw) if not w.eh_menu(t)]
    if tops:  # abriu uma janela top-level
        h = max(tops, key=lambda t: (t[3][2] - t[3][0]) * (t[3][3] - t[3][1]))
        _aberto[alvo["painel"]] = ("janela", h[0])
        return w.win32gui.GetWindowRect(h[0])
    novos = [(h, v[1]) for h, v in w.child_windows(P.mw).items()
             if h not in filhos0 and v[1][2] - v[1][0] > 100 and v[1][3] - v[1][1] > 100]
    if novos:  # abriu um painel dentro da janela principal: o maior filho novo
        h, r = max(novos, key=lambda t: (t[1][2] - t[1][0]) * (t[1][3] - t[1][1]))
        _aberto[alvo["painel"]] = ("painel", h)
        return r
    return None


def fechar(alvo):
    w.esc()
    tipo, h = _aberto.pop(alvo["painel"], (None, None))
    if tipo == "janela" and w.win32gui.IsWindow(h):
        w.fechar_dialogo(h)
    elif tipo == "painel":
        # AJUSTE: como fechar o painel (o mesmo comando de novo, se for liga/desliga; ou o X do painel).
        # No Corel: clicar em (r[2]-17, r[1]+13), o X do docker.
        _disparar(alvo["painel"])
        time.sleep(1)
