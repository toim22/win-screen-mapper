# 01. Regras e segurança

Estas regras vêm das decisões do usuário durante o mapeamento do CorelDRAW 2026 e valem como padrão
para qualquer app. Se o novo app pedir uma exceção, **pergunte ao usuário**; não decida sozinho.

## O pedido

- O entregável são **só os prints**, organizados e com relatório de cobertura. O usuário disse, com
  ênfase: "NÃO TÔ PEDINDO PRA VOCÊ CRIAR NENHUM DOCUMENTO DE TREINAMENTO". Não escreva tutoriais nem
  explicações de cada tela. LEIA-ME e relatórios só descrevem o acervo.
- Comunicação no idioma do usuário. Os nomes de arquivo seguem o idioma do app (ex.: inglês).
- "Qualquer decisão ou problema que aparecer, me consulte para que possamos seguir no melhor caminho
  possível." Pergunte quando houver opções reais. Para escolhas óbvias, siga e conte no resumo.
- Trabalhe por etapas, com aprovação explícita entre elas.

## Lista negra (nunca abrir ou acionar)

Itens que **não** se executam. Eles entram no relatório como "não aberto de propósito", com o motivo.

| categoria | exemplos |
|---|---|
| encerrar / fechar | Exit, Close, Close All, Quit, Sign out |
| gravar / sair do app | Save, Save As, Save a Copy, Export, Publish, Print, Send, Share, Upload |
| conta e compra | Purchase/Buy/Upgrade (o menu Purchase inteiro ficou fora a pedido), Sign in, Account, Subscription, licença |
| atualização e rede | Check for Updates, Download, Sync, qualquer item que abre o navegador |
| alteração permanente | Save Settings as Default, Reset Workspace, Restore defaults, Delete, Purge, Clear history |
| gravação e scripts | Start/Stop Recording de macro, executar macro, Run Script |
| programas externos | itens que abrem outro executável (editor externo, gerenciador de fontes, utilitários) |
| diálogos perigosos | no Corel: Options > VBA > **Security Options** travou o app ao fechar; Script Editor gera "Save changes?" |

Ajuda (Help): **só menus e submenus**. Os itens que abrem navegador ou página web não são abertos.

## Controles que nunca se clicam dentro de uma janela

OK, Apply, Save, Delete, Remove, Reset, Restore, Export, Import (quando grava), Send, Submit, Buy,
Purchase, "I agree"/Accept, Sign in/Log in, Create account, Update, links (texto azul ou sublinhado).

Pode clicar em controles que **só mudam a visão**: abas, páginas de árvore, expandir/recolher, listas
para ver as opções, rolagem, botões que abrem janelas filhas ("...", "Advanced", "Edit…"). Pode também
trocar uma opção para mostrar o painel que ela revela, **desde que volte ao padrão** logo depois
(campo `voltar` nos alvos).

## Como fechar

- Janela/diálogo: botão **Cancel / Close / Fechar** via UIA (`close_one.py`), senão **WM_CLOSE**.
  Esc nem sempre fecha diálogo (o Options do Corel ignorava).
- Menus, listas e popups **desenhados pelo app** (classes Afx, Qt, Chrome_Widget etc.): **Esc**.
  WM_CLOSE num popup de menu do Corel derrubou o app.
- Paletas que fecham a janela inteira com Esc: WM_CLOSE só no popup.
- **Crash Report / "Send error report": nunca enviar.** Feche pelo X/WM_CLOSE e avise o usuário.
- Se aparecer "Save changes?", responda **Cancel** (nunca Yes/No sem perguntar) e investigue a causa.

## Privacidade

- Os arquivos do usuário não têm relevância nenhuma: "Meus arquivos têm ZERO relevância nesse processo."
- Em seletores de arquivo do Windows (Open/Import/Browse), mostre **só o que o diálogo oferece para o
  app**: tipos de arquivo, opções, botões. Não navegue pelas pastas pessoais. Se a lista de pastas ou
  arquivos aparecer no print, **tarje** essa região (retângulo cinza) antes de entregar.
- Capture **só janelas dentro da área da janela principal do app** (±40 px de folga). Num print de
  "popup novo" saiu o outro monitor, com o chat do usuário: o print foi apagado e o filtro criado.
- Prefira recortar a janela do app a capturar a área de trabalho inteira.
- Revise as folhas de contato procurando nomes de pastas, e-mails, nomes de arquivos recentes ("Recent
  files"), avatares de conta. Na dúvida, tarje e avise.

## Estado do app

- Faça backup do workspace/configuração do app antes de começar (no Corel: copiar a pasta Workspace).
- Trabalhe num documento novo e descartável. Feche-o sem gravar (no Corel, via COM: `doc.Dirty=False` e `doc.Close()`).
- Reiniciar o app é permitido. Depois de reiniciar, **sempre volte ao estado base** (no Corel:
  File > New > OK, porque sem documento vários menus somem). Automatize num `restart_app.py`.
- Se o app cair: mate o processo (e o processo "fantasma" que o COM pode ter aberto), reabra, volte ao
  estado base, reconecte e continue do alvo seguinte. Registre a queda no log e no LEIA-ME.
- Ao terminar: feche janelas que o crawler abriu, volte ferramentas e opções ao padrão, avise o usuário
  do estado final.

## Instalações

Antes de instalar qualquer pacote ou programa (pywinauto, Pillow, Tesseract…), confira se já está instalado e pergunte ao usuário. Se ele tiver uma regra de registro de instalações (ex.: um arquivo citado no CLAUDE.md com o que foi instalado, versão, data e para quê), siga-a.

## Operações de arquivo

- Apague arquivos pelo **caminho exato**. `rm -rf` com curinga foi barrado pela verificação de segurança.
- Nunca apague prints sem conferir. Se for refazer, mova para `_descartados/` e apague depois.
