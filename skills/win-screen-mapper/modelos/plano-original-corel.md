# Projeto: Crawler de screenshots de todas as telas do CorelDRAW

> Handoff de uma conversa no Claude (chat) para continuar no Claude Code.
> Data: 2026-11-08

## Objetivo

Percorrer de forma **automática e completa** todos os menus, submenus, telas, subtelas, diálogos, abas, dockers, barras de propriedades e menus de contexto do **CorelDRAW**. O resultado deve ser **um screenshot de cada um**, sem deixar nenhum de fora (são centenas ou milhares de itens).

## Conclusões da pesquisa

### Easy UIAuto não resolve sozinho
- `easy-uiauto` (PyPI, v0.1.8) é só um kit de automação baseado em `pyautogui` + `uiautomation`, com controller de mouse/teclado, destaque de controles e gravação de ações.
- Ele **executa** cliques, mas não **descobre/explora** telas sozinho. Não é um crawler.
- Não existe ferramenta pronta de "explorar tudo e tirar print" para apps desktop Windows. O caminho é um **crawler sob medida**.

### Por que o CorelDRAW facilita
1. **A UI inteira é definida em XML, com GUIDs.**
   - Definição base: `C:\Program Files\Corel\CorelDRAW Graphics Suite <versão>\Draw\UIConfig\DrawUI.xml`. **Somente leitura, nunca editar.**
   - Contém `commandBarData` (menus, toolbars, menus de contexto, property bars por modo), `itemData` com GUIDs, dockers e dialogs.
   - Exemplo: GUID `f3016f3c-2847-4557-b61a-a2d05319cf18` = barra de menus principal (Menu Bar).
   - Personalizações do usuário ficam em `%APPDATA%\Corel\CorelDRAW Graphics Suite <versão>\Draw\Workspace\*.cdws`. O `.cdws` é um ZIP que contém `content/workspace.xml`.
2. **Qualquer comando pode ser aberto pelo GUID, sem clicar:**
   ```vb
   Application.FrameWork.Automation.InvokeItem "3324df3f-e302-4946-8ba9-6b1511700818" ' Propriedades do documento
   ```
   - Funciona via VBA e via COM externo (Python `win32com.client.Dispatch("CorelDRAW.Application")`).
   - Dockers: `Application.FrameWork.ShowDocker "<guid>"`.
   - Também é possível listar controles e IDs em tempo de execução via `Application.CommandBars(...).Controls(i).ID` / `.Caption`.

## Plano de implementação

### Etapa 1: Inventário (seguro, não clica em nada)
- Script Python que faz o parse do `DrawUI.xml` + `workspace.xml` ativo.
- Gera `inventory.json`/`.csv` com: caminho hierárquico (ex.: `Efeitos > Contorno`), GUID, tipo (menu item, flyout, docker, dialog, toolbar, context menu, property bar), caption.
- Resolver captions: via XML e/ou via COM (`CommandBars`), comparando as duas fontes.
- Saída: total de itens. É a "lista-mestra" que garante a cobertura completa.

### Etapa 2: Piloto
- Rodar a captura em **um único menu** (ex.: Ferramentas) para validar abrir → print → fechar.

### Etapa 3: Captura completa
Para cada item do inventário:
1. Abrir via `InvokeItem` (ou `ShowDocker` para dockers).
2. Esperar a janela/diálogo estabilizar.
3. Screenshot da janela nova (ex.: `mss` + recorte pelo retângulo da janela via UIA/win32).
4. Fechar com Esc/Cancelar e verificar que voltou ao estado base.
5. Registrar o resultado: ok / desativado / erro / timeout.

### Etapa 4: Subtelas dentro dos diálogos
- Usar **Windows UI Automation** (`pywinauto`, backend `uia`) para percorrer abas, páginas e tree views dentro de cada diálogo.
- Caso crítico: a árvore de **Ferramentas > Opções** tem centenas de páginas.
- Fallback por visão (screenshot + modelo de visão) onde o Corel usa controles próprios invisíveis à UIA.
- Dedupe: hash da estrutura UIA de cada tela, para evitar repetição e loops.

### Etapa 5: Contextos (muitos comandos ficam desativados sem seleção)
Repetir a varredura em vários estados:
- sem documento aberto;
- documento vazio;
- com retângulo, elipse, curva, texto artístico, texto de parágrafo, bitmap, grupo, tabela, seleção múltipla, linha de cota, conector etc. selecionados.

Além disso:
- ativar **cada ferramenta** da caixa de ferramentas e fotografar sua **barra de propriedades**;
- **menus de contexto**: clique direito em cada tipo de objeto, na página e na área de trabalho.

### Segurança
- **Lista negra** de comandos: Sair, Fechar, Salvar/Salvar como, Exportar, Imprimir, Publicar, conta/login Corel, atualizações, redefinir workspace, gerenciadores que alteram arquivos.
- Fazer **backup da pasta Workspace** antes e restaurar depois.
- Trabalhar sempre num arquivo `.cdr` de teste descartável.
- Ideal (opcional): rodar numa VM com snapshot.

### Saída final
- Pasta com um PNG por tela, nomeado pelo caminho (`Efeitos > Contorno.png`, sanitizado), separado por contexto.
- `index.html` navegável (árvore + miniaturas).
- **Relatório de cobertura**: itens do inventário sem print e o motivo, para nada sumir em silêncio.

### Limitação honesta
Algumas telas dependem de condições que o script não adivinha: dados específicos, erros, licença, login, plugins. O relatório de cobertura serve para tratar esses casos manualmente.

## Pendências (perguntar ao usuário / verificar no PC)
- [ ] Versão do CorelDRAW (2024? 2025?) e idioma da interface (PT-BR?).
- [ ] Componente **VBA** instalado? Aparece em Ferramentas > Scripts. Se não, adicionar pelo instalador do Corel em "Modificar". Confirmar se o COM externo funciona sem ele.
- [ ] Python instalado? Libs: `pywin32`, `pywinauto`, `mss`, `Pillow`, `lxml`.
- [ ] Pasta de trabalho sugerida: `<Documentos>\corel-screenshots\`.

## Regras permanentes do usuário (obrigatórias)
- **Antes de instalar qualquer coisa** no PC Windows, consultar o registro de instalações do usuário para ver se já está instalado.
- **Depois de instalar**, registrar no registro de instalações do usuário: o que foi instalado, versão e data. O arquivo tem uma única tabela "Instalado"; só adicionar/atualizar linhas. Entradas sem data usam "data desconhecida".
- **Depois de instalar**, salvar também um guia `.md` na pasta de guias do usuário explicando para que serve e como foi instalado/usado.
- Idioma de comunicação: português.

## Fontes
- easy-uiauto (PyPI): https://pypi.org/project/easy-uiauto/
- DrawUI.xml / GUID da Menu Bar: https://community.coreldraw.com/collaborate/w/howto/94/how-to-create-a-menu-or-a-button-for-your-macro-with-xml-in-coreldraw-x5-automatically
- workspace.xml dentro do .cdws / GUIDs de dockers: https://community.coreldraw.com/sdk/f/coreldraw-and-corel-designer-api/68254/hide-dockers-in-coreldraw
- `FrameWork.Automation.InvokeItem`: https://community.coreldraw.com/sdk/f/code-snippets-feedback/57979/vba-document-properties/277618
