"""lista_negra.py: o que nunca abrir (itens de menu) e nunca clicar (botoes dentro das telas).

Vem das regras aprovadas pelo usuario no mapeamento do CorelDRAW 2026. Ajuste por app,
MAS mostre a lista ao usuario na etapa 0 e pergunte antes de afrouxar qualquer coisa.

  from lista_negra import item_bloqueado, classificar_botao
  item_bloqueado("File > Save As...")   -> "lista negra: salvar"
  classificar_botao("Advanced...")      -> ("clica", "abre janela")
"""
import re

# ---- itens de menu (caminho completo) -------------------------------------------------
# Itens exatos, com motivo. Preencha com o que o inventario mostrar do app.
ITENS = {
    # "File > Save...": "lista negra: salvar",
    # "Tools > Scripts > Script Editor...": "fechar o editor pergunta 'Save changes?'",
}
# Menus raiz inteiros fora do escopo (decisao do usuario).
MENUS_FORA = {"Purchase", "Buy", "Store", "Debug"}
# Palavras no NOME do item (ultimo pedaco do caminho) que bloqueiam.
PALAVRAS_ITEM = ("exit", "quit", "close", "save", "export", "publish", "print", "send", "share",
                 "upload", "sync", "cloud", "purchase", "buy", "upgrade", "subscription", "license",
                 "sign in", "sign out", "log in", "log out", "account", "update", "recording",
                 "record macro", "run script", "temporary script", "save settings as default",
                 "reset workspace", "restore defaults", "uninstall")
# Itens que abrem navegador/pagina web: no Help, so menus e submenus.
WEB = ("help topics", "product help", "user guide", "video tutorials", "quick start", "support",
       "submit ideas", "feedback", "what's new", "learn", "community", "website", "online")


def item_bloqueado(caminho):
    """Motivo (str) se o item nao deve ser aberto; None se pode."""
    if caminho in ITENS:
        return ITENS[caminho]
    partes = [p.strip() for p in caminho.split(">")]
    if partes[0] in MENUS_FORA:
        return f"fora do escopo: menu {partes[0]}"
    nome = partes[-1].lower().rstrip(".…").strip()
    for w in PALAVRAS_ITEM:
        if re.search(rf"\b{re.escape(w)}\b", nome):
            return f"lista negra: '{w}'"
    if partes[0].lower() == "help":
        for w in WEB:
            if w in nome:
                return "decisao do usuario: no Help so os menus (o item abre o navegador)"
    return None


# ---- botoes dentro das telas ----------------------------------------------------------
NUNCA_EXATO = {"ok", "apply", "cancel", "close", "yes", "no", "help", "finish", "done", "x",
               "minimize", "maximize", "restore", "open", "save", "import", "export", "next", "back"}
NUNCA_PALAVRAS = ("delete", "remove", "reset", "restore", "save", "export", "print", "publish", "clear",
                  "default", "buy", "purchase", "sign", "log in", "login", "upload", "share", "send",
                  "update", "exit", "uninstall", "discard", "overwrite", "replace", "rename", "apply",
                  "already purchased", "subscribe", "install", "download", "convert", "merge",
                  "policy", "privacy", "statement", "terms", "agree", "accept", "online", "website",
                  "learn more", "web", "support", "feedback", "tutorial", "legal", "credential",
                  "profile", "account", "generate", "create", "add", "new", "load", "run", "start",
                  # Corel: fechar Options > VBA > Security Options travou o app
                  "security")
ABRE_PALAVRAS = ("advanced", "edit", "options", "settings", "more", "details", "properties", "browse",
                 "customize", "preview", "info", "setup", "configure", "manage", "show", "view")
SEMPRE = set()  # excecoes liberadas pelo usuario (ex.: {"add color"} no Corel: abre o seletor de cor)


def classificar_botao(nome):
    """('clica' | 'nao', motivo). Sem '...' so clica se o nome indicar que abre algo.
    Rode o crawler de botoes com --dry e mostre a classificacao ao usuario antes."""
    base = nome.replace("&", "").strip().lower().rstrip(".…").strip()
    if base in SEMPRE:
        return "clica", "liberado pelo usuario"
    if base in NUNCA_EXATO:
        return "nao", "confirmacao/fechamento"
    for w in NUNCA_PALAVRAS:
        if re.search(rf"\b{re.escape(w)}", base):
            return "nao", f"acao: '{w}'"
    if nome.strip().endswith(("...", "…")):
        return "clica", "abre janela ('...')"
    for w in ABRE_PALAVRAS:
        if re.search(rf"\b{re.escape(w)}\b", base):
            return "clica", f"abre janela ('{w}')"
    return "nao", "nao indica que abre janela"


# Perguntas que podem aparecer: responder SEMPRE com Cancel e parar a rodada.
PERGUNTAS = ("save changes", "do you want to save", "salvar alteracoes", "are you sure", "overwrite",
             "crash report", "send report", "error report")
