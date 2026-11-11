# MAPEAMENTO: telas do CorelDRAW 2026 (inglês)

Prints de todos os menus, submenus, telas (janelas/diálogos), subtelas, dockers e barras do
CorelDRAW 2026 (v27.2, interface em inglês), para o time que monta o treinamento.

## Como está organizado

```
MAPEAMENTO/
├─ LEIA-ME.md            este arquivo
├─ 01-inventario/        a lista-mestra de tudo que existe na interface
│   ├─ inventory.csv     abre no Excel: caminho, nome em inglês, GUID, tem submenu, habilitado...
│   └─ inventory.json    o mesmo, para os scripts
├─ 02-menus/             prints dos menus abertos
│   └─ <contexto>/       ex.: doc-vazio = documento em branco, nada selecionado
│       └─ NN Menu/      um por menu da barra, na ordem da barra (01 File, 02 Edit...)
│           ├─ 001 File.png                       recorte: só o menu e a cascata aberta
│           ├─ 002 File ▸ Open Recent.png
│           └─ tela-inteira/                      o mesmo print com a janela inteira
├─ 03-telas/             prints das janelas que os itens abrem (diálogos), por contexto
├─ 04-dockers/           cada docker do Window > Dockers (painel lateral), com partes de rolagem;
│                         dentro/ = abas, listas e menus de cada docker
├─ 05-ferramentas/       caixa de ferramentas, flyouts e barra de propriedades de cada ferramenta
├─ 06-barras/            barras de ferramentas (Standard, status, paletas e as barras ocultas)
├─ 07-menus-de-contexto/ menus do clique direito (objetos, página, régua, barras...) e submenus
└─ 90-relatorios/        logs e relatórios de cobertura (o que tem print, o que faltou e por quê)
    └─ cobertura_menus_<contexto>.csv   cada submenu do inventário: ok / desativado / oculto / fora do escopo
```

**Fora do escopo por decisão:** o menu **Purchase** (não serve para o treinamento) e o menu
**Debug**, que é oculto e só aparece com uma opção interna de depuração.

**Itens dinâmicos:** listas montadas na hora (ex.: workspaces instalados em `Window > Workspace`)
não têm identificador próprio e saem como `item dinamico N`. Em `Window > Workspace`, o 3 é
**Touch** e o 4 é **Specialty**.

**Nomes dos arquivos:** número na ordem em que aparece no menu + caminho completo, com `▸` no
lugar de `>` (o Windows não aceita `>` em nome de arquivo).

**Contextos:** o mesmo menu muda conforme o que está selecionado (itens ativos ou cinza). Cada
rodada fica numa pasta de contexto: `doc-vazio`, depois `retangulo`, `texto`, `bitmap` etc.

## Colunas do inventory.csv

| coluna | significado |
|---|---|
| kind | `menu_root` (barra), `menu_item`, `other_menu` (menus de contexto/flyouts), `toolbar`, `docker`, `dialog` |
| path | caminho completo, ex.: `Tools > Options > CorelDRAW...` |
| caption | nome em inglês, como aparece na tela |
| guid | identificador interno do comando no Corel (abre o item direto, sem clicar) |
| has_submenu | se o item abre um submenu |
| enabled | se estava habilitado na hora do inventário (sem nada selecionado) |
| opens_dialog_hint | nome termina em `...` (por convenção, abre uma janela) |

## Etapas

| # | etapa | situação |
|---|---|---|
| 1 | Inventário (lista-mestra) | concluído: 1.724 itens |
| 2 | Menus e submenus, documento vazio | concluído: 75 prints (12 menus da barra + 63 submenus), ver `90-relatorios/cobertura_menus_doc-vazio.csv` |
| 3 | Telas que os itens abrem (diálogos) | concluído no doc vazio: 43 telas; 189 desativadas ficam para a etapa 5; ver `90-relatorios/cobertura_telas_doc-vazio.csv` |
| 4 | Dentro de cada tela (abas, páginas, listas com scroll, menus internos, janelas filhas) | concluído no doc vazio: 523 prints em 43 telas (382 por dentro, 9 de botões, 132 por visão); ver `90-relatorios/cobertura_dentro_doc-vazio.csv` |
| 5 | Repetir 2 a 4 com objetos selecionados (retângulo, texto, bitmap, grupo, tabela...) | concluído: 17 contextos; 416 prints de menus, 157 telas antes desativadas (37 janelas + 120 efeitos no docker), 163 prints por dentro; ver `90-relatorios/matriz_contextos.csv`, `cobertura_contextos.csv` e `menus_contextos.csv` |
| 6 | Dockers, barras de ferramentas, barra de propriedades de cada ferramenta, menus de contexto | concluído: 45 dockers, 15 flyouts, 60 barras de propriedades + Pick em 18 contextos, 12 barras, menus de contexto em 23 lugares; ver pastas 04 a 07 |
| 7 | Relatório de cobertura + índice HTML navegável | concluído: `index.html` (2.844 prints) e `90-relatorios/cobertura_final.csv` (787 itens de menu) |

### Etapa 3: telas

Para cada item de menu que abre uma janela (ex.: `File > New...`), o script abre pelo GUID, espera
a janela estabilizar, fotografa e fecha pelo **Cancel/Fechar**, sem confirmar nada.

**Lista negra** (aprovada; não são abertos, para não alterar nada): Exit, Close, Close All, Save,
Save As, Save to Cloud, Open from Cloud, Export, Publish, Print, Purchase, login/conta Corel,
atualizações, gravação de script, Save Settings as Default, redefinir workspace, Visual Studio
Editor (programa externo). Se alguma tela da lista negra precisar de print, decidimos caso a caso.

**Ocorrências e decisões da etapa 3:**
- `Tools > Scripts > Script Editor...` (editor VBA): o print foi feito, mas fechar o editor fez o
  Corel perguntar "Save changes to Untitled-1?". O script parou, a pergunta foi respondida com
  **Cancel** e nada foi salvo nem perdido. O item entrou na lista negra. Desde então, qualquer
  pergunta Yes/No/Cancel que aparecer é respondida com Cancel e a rodada para.
- `Help > What's New?...` não abre janela: troca para a aba **Welcome Screen**. O conteúdo web
  dessa aba não carregou, e o print mostra a aba assim.
- `Object > Perspective > Draw in Perspective...` não abre janela (liga um modo de desenho).
- **Pendente de decisão:** Product Help, Video Tutorials, Quick Start Guide, User Guide, Corel
  Support e Submit Ideas provavelmente abrem o navegador; não foram abertos.
- Com a aba Welcome Screen ativa (sem documento), a barra de menus encolhe para File, Tools,
  Window e Help. Isso será um contexto próprio (`sem-documento`) na etapa 5.

### Etapa 4: dentro de cada tela

Cada janela é explorada por dentro, e cada estado diferente vira um print:

- **abas** e **páginas** (ex.: a lista lateral do `Tools > Options`, com 14 páginas só em CorelDRAW);
- **listas e áreas com scroll** (ex.: modelos do `File > New`): rola até o fim, um print por "tela" de conteúdo;
- **menus e listas suspensas internas** (combos, botões com seta);
- **janelas filhas** (botões que abrem outra janela, como "Edit..." ou "Advanced..."), exploradas
  do mesmo jeito, com limite de profundidade;
- prints repetidos são descartados (comparação de imagem), para não entrar em loop.

O Corel desenha parte dos controles por conta própria, e a ferramenta de automação do Windows
não enxerga esses controles. Onde isso acontecer, o item vai para o relatório de cobertura para
ser tratado por outro método ou manualmente.

**Onde ficam os prints da etapa 4:** cada tela tem uma pasta com o mesmo nome do print da etapa 3
(ex.: `03-telas/doc-vazio/10 Tools/001 Tools ▸ Options ▸ CorelDRAW/`), com:
- os prints da exploração por dentro (`001 inicial`, `pagina ▸ ...`, `lista aberta ▸ ...`, `rolagem ▸ ... ▸ parte N`);
- `botoes/`: janelas filhas abertas pelos botões (ex.: `botao ▸ Edit Color` abre o Select Color);
- `visao/`: controles desenhados pelo Corel que a automação do Windows não enxerga (sub-abas,
  botões dentro das páginas do Options, caixas que liberam opções), clicados por coordenada.
  Os alvos estão em `scripts/visao_alvos.json`.

**Decisões do usuário (etapa 4):**
- Seletores de arquivo do Windows (Open, Import, Save as Template, Browse...): só o que é do
  aplicativo (estado inicial, tipos de arquivo, opções). Não navega pelas pastas do usuário.
- Botões que abrem janelas filhas podem ser clicados. Nunca: OK, Apply, Delete, Remove, Reset,
  Save, Export, conta/login/compra, termos, links para o navegador (`scripts/crawl_botoes.py`).
- Itens do Help que abrem o navegador ficam de fora (só os menus e submenus do Help importam).
- Reiniciar o Corel é permitido, sempre seguido de File > New > OK (`scripts/restart_corel.py`).

**Ocorrências da etapa 4:**
- A 1ª rodada navegou pelas pastas pessoais nos seletores de arquivo (575 prints); as 5 pastas foram
  refeitas só com o conteúdo do Corel (16 prints).
- Listas de conteúdo (linhas de tabulação, tipos de objeto, linhas do Document Properties e do
  Text Statistics) eram tratadas como páginas; agora o script compara a tela antes e depois.
- `Tools > Color Management...` parou de abrir; voltou após reiniciar o Corel. Ao fechar o Corel
  com o documento de teste alterado, abriu direto o "Save Drawing" (cancelado, nada salvo); agora o
  documento de teste é descartado pela automação antes de fechar.
- `Tools > Options > CorelDRAW > VBA > Security Options...` (diálogo do VBA): o print foi feito, mas
  ao fechar o Corel travou e encerrou. Nada foi salvo. Na reabertura apareceu o "Crash Report",
  fechado pelo X **sem enviar** o relatório. O botão saiu das rodadas seguintes.
- Paletas de cor do Corel: o Esc fecha a tela inteira; agora o popup é fechado sozinho.
- `Text > Line-Breaking Rules`: as caixas ficam desativadas no doc vazio (regras de texto asiático).

**Pendente na etapa 4 (próximas rodadas):** controles desenhados pelo Corel dentro das janelas
filhas (ex.: "Color viewers" no Select Color), as linhas do Options > Workspaces e caixas de
seleção comuns das páginas do Options (o estado delas já aparece nos prints).

### Etapa 5: contextos com objetos

Cada contexto é montado num **documento descartável novo** (nunca salvo), pelo script
`scripts/contextos.py`:

| pasta | o que está na página |
|---|---|
| `sem-documento` | nenhum documento aberto (barra de menus reduzida a File, Tools, Window, Help) |
| `retangulo`, `elipse`, `curva` | um objeto simples selecionado |
| `texto-artistico`, `texto-paragrafo` | um texto selecionado |
| `bitmap` | um bitmap RGB selecionado |
| `grupo`, `selecao-multipla` | dois objetos, agrupados ou só selecionados juntos |
| `tabela`, `tabela-celulas` | tabela 3x3 selecionada; ou ferramenta Table com 4 células selecionadas |
| `simbolo`, `powerclip`, `linha-de-cota`, `conector`, `rollover` | um objeto desse tipo selecionado |
| `varias-paginas` | documento com 3 páginas e um retângulo selecionado |
| `com-efeitos` | objetos com envelope, perspectiva e distorção na página + um retângulo selecionado |

**O que funciona com cada objeto:** `90-relatorios/matriz_contextos.csv` tem uma linha por item de
menu e uma coluna por contexto (`sim` = ativo). No doc vazio são 284 itens ativos; com objeto
selecionado, até 469.

**Menus (`02-menus/<contexto>/`):** um menu só é fotografado de novo quando o conjunto de itens
ativos dele muda. Quando fica igual a outro contexto, `menus_contextos.csv` diz a qual
(ex.: na `elipse` todos os menus são iguais aos do `retangulo`).

**Telas (`03-telas/<contexto>/`):** cada tela desativada no doc vazio foi aberta no primeiro
contexto que a liga (Effects e Bitmaps preferem o `bitmap`). `cobertura_contextos.csv` diz em qual.
- **Efeitos no Corel 2026 não abrem janela:** o efeito entra direto no objeto e os ajustes aparecem
  no docker **Properties > Bitmap Effects**. Esses prints são da tela inteira com o painel aberto e
  o nome termina em `(abre no docker Properties)`. São 120.
- Itens que só mudam a tela ou entram num modo (Edit PowerClip, Edit Master, Order > In Front Of,
  Copy Effect From...) têm print da tela inteira com o nome terminando em `(sem janela, tela principal)`.
- **Não abertos (mesmos critérios aprovados):** File > Export For > Office/Web/WordPress (exportar),
  File > Send To > Mail (envia e-mail), Bitmaps > Edit Bitmap (abre outro programa, o PHOTO-PAINT),
  Help > Share Your Experience (navegador).
- **Desativados em todos os contextos:** Acquire Image (sem scanner); Copy/Clone Effect de Blend,
  Extrude, Contour, Lens e Shadow (a automação não conseguiu criar esses efeitos); Edit Perspective
  Group; Open Last Trace Settings (precisa de um trace feito antes).
- `Object > Rollover > Edit Rollover...` abre a barra flutuante **Internet**: fica para a etapa 6.

**Ocorrências da etapa 5:**
- O Esc que fecha cada menu também tira a seleção do objeto; a 1ª rodada de menus saiu sem seleção
  a partir do 2º menu de cada contexto e foi refeita, remontando o contexto antes de cada menu.
- Duas vezes, logo depois de fotografar os menus no contexto `retangulo`, o Corel ficou
  inconsistente (aba Untitled-1 sem documento, menus reduzidos, automação com erro). Foi reiniciado
  pelo procedimento aprovado (File > New > OK); nada foi salvo.
- `Edit Master` deixa o documento no modo de edição de símbolo; fechar o documento nesse modo
  travava a automação. Agora o script sai dos modos de edição (Finish Editing) antes.
- `Edit Rollover` deixou a barra Internet visível no workspace; ela foi fechada de novo.

### Etapa 6: dockers, ferramentas, barras e menus de contexto

- **`04-dockers/retangulo/`**: os 45 dockers do `Window > Dockers` (inclusive `Effects > ...`), abertos
  com um retângulo selecionado. O recorte é só o painel; `tela-inteira/` mostra onde ele aparece.
  Quando o conteúdo é maior que o painel, há prints `▸ rolagem parte N` (rolagem com a roda do mouse).
  Os docker de **AI Generate** e **Learn** mostram conteúdo online como estava na hora.
- **`04-dockers/properties-abas/<contexto>/`**: as abas internas do docker **Properties** (ícones no
  topo do painel) em 5 contextos: retângulo (7 abas: Outline, Fill, Transparency, Bitmap Effects,
  Rectangle, Painterly Brush, Summary), texto artístico (6), texto de parágrafo (5), bitmap (5) e
  tabela (6). `00 aberto` é como o painel abre; `NN aba K` é a K-ª aba da esquerda para a direita,
  com as partes de rolagem. O título de cada aba aparece no topo do print. Só as abas foram
  clicadas; nada foi alterado. A aba Bitmap Effects com cada efeito está na etapa 5 (`03-telas/bitmap/06 Effects`).
- **`04-dockers/dentro/NNN Docker/`**: os dockers por dentro (abas, listas, menus, seções recolhíveis e
  opções de modo de cada um). Os controles são desenhados pelo Corel (a automação do Windows não os
  enxerga), então os alvos foram marcados a olho nos prints e ficam em `scripts/docker_alvos.json`
  (gerado por `scripts/gera_alvos.py`). Em cada pasta:
  - `000 inicial` (+ `▸ rolagem parte N`): o docker como abre, no contexto indicado no relatório;
  - `NNN <alvo>`: o painel depois do clique (aba aberta, seção expandida, opção escolhida) ou com a
    lista/menu aberto por cima. Diálogos que um botão abre (ex.: Edit Fill, Outline Pen, Edit Line Style,
    Object Data Manager) saem com a janela do Corel inteira; foram fechados pelo X (= Cancel);
  - `NNN <menu> ▸ submenus/`: submenus de menus de engrenagem e "...", abertos só passando o mouse.
  Exemplos do que tem: as 7 abas do Properties com as listas e os tipos de preenchimento e de
  transparência; as abas do Transform e do Coordinates; cada operação do Shape (Trim, Intersect...);
  cada um dos 12 tipos de lente do Lens; os modos do Step and Repeat, Corners, Join Curves, Bevel,
  Contour, Envelope, Blend e Extrude; as listas de fontes, cores e presets.
  **Nunca** foi clicado: Apply, Add, Create, Generate, I agree, Save, Export, Print, Load, Browse,
  botões de alinhar, ferramentas de comentário, zoom, itens do History (desfazem passos) e New do
  Scripts. Toda opção trocada voltou ao padrão depois do print.
  Relatório: `90-relatorios/dockers_dentro.csv` (223 alvos, 239 prints, 40 dockers). Sem alvos (5):
  Export e AI Generate (só botões de ação / termos de uso), Sources (tudo desativado sem vínculos),
  History (clicar desfaz passos) e PhotoCocktail (só Browse e campos numéricos). Os 18 alvos "nada abriu/mudou" são controles desativados nesse
  contexto (ex.: listas do Live Guides com as guias desligadas, cores do hotspot em Links and
  Rollovers, engrenagem do Views) ou que já estavam na opção padrão.
- **`05-ferramentas/`**:
  - `flyouts/`: a caixa de ferramentas e cada grupo aberto (o triângulo do botão);
  - `barra-de-propriedades/`: a barra de propriedades de cada uma das 60 ferramentas. Entre
    parênteses, o contexto usado (ex.: Shape com uma curva, Text com texto, Crop com bitmap);
  - `barra-pick-por-contexto/`: a barra da ferramenta Pick em cada contexto da etapa 5 (ela muda
    conforme o objeto selecionado).
  Ativar ferramentas troca o ícone que cada grupo mostra na caixa; no fim, cada grupo voltou para a
  1ª ferramenta (o padrão).
- **`06-barras/`**: recortes das barras sempre visíveis (Standard, status, paleta do documento, paleta
  lateral) e das barras ocultas (Layout, Text, Transform, Macros, Internet, Zoom/Pan, Parallel Lines,
  Project Timer), mostradas e ocultadas de novo.
- **`07-menus-de-contexto/`**: clique direito em cada tipo de objeto, nas células da tabela, dentro do
  texto em edição (saiu o menu de erro de ortografia, porque o texto de teste é em português), nos nós
  de uma curva com a ferramenta Shape, na página, na área de trabalho, na régua, na aba da página,
  na barra Standard, na barra de status e na caixa de ferramentas. Os submenus foram abertos só
  passando o mouse. Na paleta de cores, na paleta do documento e na aba do documento o clique
  direito não abre menu.

**Ocorrências da etapa 6:**
- Mais uma vez, fechar o documento descartável logo depois de percorrer um menu derrubou o Corel
  (encerrou sozinho, nada salvo; o Crash Report da reabertura foi fechado pelo X **sem enviar**).
  Nas rodadas de menu, o documento agora é limpo (apaga os objetos) em vez de fechado, e não houve
  mais queda.
- A barra "StatusBar" da lista de barras mostrou uma janela vazia; a barra de status está no recorte.
- Dockers por dentro: abrir o **menu da engrenagem do docker Objects** deixou o Corel instável e ele
  caiu no passo seguinte (3 vezes). O print desse menu e dos 2 submenus foi feito, e o script
  reinicia o Corel logo depois desse alvo. Nas quedas o Crash Report foi fechado pelo X **sem enviar**.
- No `Effects ▸ Bitmap Mask`, o botão da pasta abre o seletor de arquivos do Windows; a lista de
  pastas pessoais foi **tarjada** no print (ficam só o tipo de arquivo e os botões).
- Um print do "..." do Fill saiu com a tela dos dois monitores (pegou janelas fora do Corel); foi
  apagado e refeito, e o script agora ignora qualquer janela fora da área do Corel.

### Etapa 7: índice e cobertura

- **`index.html`** (abra com dois cliques; funciona sem internet): árvore de pastas à esquerda,
  miniaturas, busca pelo nome e visualizador (setas ← → passam os prints, Esc fecha, "tamanho real"
  mostra sem reduzir). A caixa **tela inteira** mostra também as cópias com a janela inteira. A aba
  **Cobertura** lista cada item dos menus com a situação, o contexto, quantos prints por dentro e o
  motivo quando não há print; clicar no nome abre o print. As miniaturas ficam em `_indice/`
  (refeitas por `scripts/gera_indice.py`; não apague a pasta, senão a página fica sem imagens).
- **`90-relatorios/cobertura_final.csv`**: os 787 itens dos menus da barra cruzados com todos os logs.
  Resumo: 598 com print (155 telas/submenus, 120 efeitos que abrem no docker, 12 comandos sem janela
  com print da tela principal, 311 comandos que aparecem no print do menu); 144 fora do escopo
  (menu Debug oculto e Purchase); 27 não abertos de propósito (lista negra e itens do Help que abrem
  o navegador); 14 telas desativadas em todos os contextos testados (Acquire Image, Copy/Clone
  Effect, Edit Perspective Group, Open Last Trace Settings: dependem de scanner ou de efeitos que a
  automação não consegue criar); 3 ocultos (`File > Document Management`); 1 sem janela
  (`Draw in Perspective`, que ativa um modo na área de desenho).
- **`90-relatorios/cobertura_definicoes_internas.csv`**: as 937 definições que só existem no arquivo
  interno do Corel (diálogos, dockers, barras e menus sem item de menu próprio). 177 foram
  fotografadas por outro caminho (mesmo nome de docker, barra ou tela); as outras são partes
  internas que não abrem sozinhas.
- `90-relatorios/resumo_final.json`: os totais acima. Para refazer: `python scripts/relatorio_final.py`
  e depois `python scripts/gera_indice.py`.

## Material de apoio

- Plano original: `modelos/plano-original-corel.md` (nesta skill)
- Mapeamento anterior, feito com outro agente (fora desta skill).
  Dele veio a cadeia de nomes `Resources\caption.csv` → `Languages\EN\Data\strings.xml`, que dá
  nome aos dockers e diálogos.
- Engenharia reversa do Corel: documentos locais do modelo de automação (fora desta skill).
- Scripts: `<pasta do projeto>\scripts\` (cópia em `exemplos/corel/`)
- Backup do Workspace do Corel (antes de tudo): `<pasta do projeto>\backup\`
