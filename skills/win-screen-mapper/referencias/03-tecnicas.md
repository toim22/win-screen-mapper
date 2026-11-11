# 03. Técnicas e armadilhas

Estas técnicas valem para qualquer app do Windows. Foram aprendidas na prática (no Corel), e os
detalhes de lá aparecem marcados como "no Corel", só como exemplo. As funções citadas estão em `kit/`
(genéricas); as originais ficam em `exemplos/corel/`. Ao mapear um app novo, acrescente aqui o que
aprender.

## Processo Python

- **`SetProcessDpiAwareness(2)`** antes de tudo. Sem isso, coordenadas e recortes saem deslocados em
  monitores com escala.
- **Multi-monitor:** coordenadas podem ser negativas. Use `ImageGrab.grab(bbox, all_screens=True)`.
- **COM + pywinauto no mesmo processo derrubou o Python 3.15** (exit 139). Toda UIA roda em
  subprocesso: `uia_tool.py` (dump/do/serve) e `close_one.py`.
- **Chamadas que podem bloquear** (abrir diálogo modal via COM) também vão para subprocesso
  (`invoke_one.py`), com timeout. O processo principal espera a janela nova aparecer e tira o print.
- **COM "fantasma":** se o app estiver fechado, `gencache.EnsureDispatch` **abre** uma instância nova,
  que some quando o script acaba. Antes de reconectar, confira se o processo existe (`vivo()`). Se não
  existir, reabra pelo `restart_app.py`.
- Rodadas longas em **segundo plano**, com log em arquivo (`print(..., flush=True)`) e retomada por
  `--only/--skip/--desde`.

## Foco

- Leve a janela à frente com `SetForegroundWindow` + `AttachThreadInput` (`force_foreground`).
- **Não use o truque da tecla Alt** para ganhar foco: ele liga o modo teclado do menu e abre o menu
  errado. Se precisar, clique na barra de título da janela principal.
- Depois de cada alvo, mova o mouse para um canto neutro (`away()`), para tooltips e hovers não entrarem no print.

## Menus

- Com modelo: abra o menu raiz, pegue a posição do item **com o menu aberto** (no Corel,
  `GetItemScreenRect`; com o menu fechado ele devolvia o retângulo de outra barra) e passe o mouse.
- **Hover precisa de micro-movimentos:** vários `SetCursorPos` de 1-2 px em ~150 ms. Um só movimento às
  vezes não abre o submenu.
- **Detecção do popup:** compare as janelas de topo do processo antes e depois (`popups_novos`).
  Filtre as de tamanho zero (causaram "cannot write empty image") e as **fora da área do app**.
- **Submenu anterior fecha com atraso:** ignore o hwnd antigo até ele sumir, senão o print sai com o
  submenu errado.
- Menus desenhados pelo app são invisíveis à UIA. As medidas de linha ajudam a calcular itens: no Corel,
  linha de 22 px, separador de 7 px, borda de 3 px.
- Itens ocultos: o modelo diz que existem, mas não aparecem (no Corel, `GetItemScreenRect` dava False).
  No relatório, a situação é "oculto".
- **Esc fecha o menu e pode tirar a seleção.** Remonte o contexto antes de cada menu raiz.
- Prints: recorte do popup (união menu + submenus) e, em `tela-inteira/`, a janela inteira do app.

## Telas (diálogos)

- Abra pelo id/comando, espere a janela nova estabilizar (≈1-2 s), tire o print e feche (Cancel/X).
- Antes de abrir, compare o título com a lista negra (`BLACKLIST`, `BLACK_WORDS`, `WEB`).
- Classifique o resultado:
  - **ok**;
  - **docker** (abriu um painel, não janela);
  - **sem janela** (o comando age direto; no Corel, os efeitos aplicam no objeto e abrem o Properties);
  - **não abriu** (desativado no contexto);
  - **não aberto de propósito**.
- Alguns comandos trocam de aba ou de documento (Help > What's New foi para a Welcome Screen). Volte
  ao documento de trabalho clicando na aba; `Activate()` via COM falhou.
- Diálogo que para de abrir depois de muitas aberturas (Color Management): reinicie o app.

## Dentro das telas

- **UIA** (diálogos padrão): `uia_tool.py dump <hwnd>` lista abas (`TabItem`), árvores (`TreeItem`),
  listas (`ComboBox`/`List`) e botões. Percorra:
  - cada aba (select);
  - cada página de árvore (select, com rolagem se necessário);
  - cada combo (expand → print → collapse/Esc);
  - botões que abrem janela filha.
- Classifique os botões por palavras (perigosos × que só abrem janela). Rode `--dry` primeiro e mostre a
  lista ao usuário.
- **Passe por visão** onde a UIA não enxerga (botões desenhados, sub-abas, ícones):
  1. tire um print de cada estado;
  2. monte **folhas com régua** (`kit/folhas_regua.py`);
  3. marque as coordenadas olhando a imagem (relativas à janela ou painel);
  4. escreva os alvos em JSON;
  5. rode o motor (`kit/alvos_visao.py`);
  6. revise em folha de contato. Erros comuns: converter mal a coordenada da folha (régua com
     deslocamento) e painéis cuja largura varia (ancore no lado certo).

## Formato dos alvos por visão

```json
{"nome": "Fill > Fountain > Type list", "painel": "Properties",
 "tipo": "lista",              // aba | lista | menu | expandir
 "x": 212, "y": 148,           // relativo ao painel/janela
 "antes": [[40, 60], {"x": 90, "y": 60, "manter": true}],  // cliques que preparam o estado
 "voltar": [[40, 60]],         // cliques que restauram o padrão
 "rolar": 3,                   // quantas partes de rolagem fotografar (roda do mouse)
 "submenus": true,             // explorar submenus do popup por hover
 "reiniciar_depois": false}    // reinício preventivo (alvo que deixa o app instável)
```

- `manter: true` deixa a lista aberta para o clique seguinte escolher um item. Sem isso, o motor dava Esc
  antes e o item nunca era selecionado.
- `voltar` é obrigatório quando o alvo troca uma opção.
- **Não clique em árvores que mudam o estado do documento.** No Corel, clicar na árvore do Objects
  trocava a camada ativa; esses alvos foram removidos.

## Painéis / dockers

- Ache o painel pela classe (no Corel, filhos `ViewHost` da janela principal com 150-900 px de largura
  e mais de 300 px de altura).
- O app reabre o workspace com painéis abertos. **Feche todos antes de cada alvo** (`fechar_todos()`:
  clicar no X do painel). Se o comando de abrir é um toggle e nada novo apareceu, invoque de novo.
- Rolagem com a roda do mouse dentro do painel. Fotografe cada parte até o conteúdo parar de mudar
  (compare imagens).

## Ferramentas e barras

- Flyouts da caixa de ferramentas: no Corel, clicar no canto inferior direito do botão.
- Barra de propriedades: ative cada ferramenta e recorte a faixa da barra (no Corel, y 88..137 da janela).
- Ativar ferramentas muda o ícone do flyout. No fim, restaure invocando o 1º item de cada flyout.
- Barras ocultas: ligue via modelo (`CommandBars(i).Visible = True`), tire o print e desligue.

## Menus de contexto (clique direito)

- Para cada tipo de objeto e cada lugar da interface (página, régua, paleta, painéis, abas), clique com o
  botão direito e use o mesmo explorador de menus (hover nos submenus).
- Dê Esc no fim e remonte o contexto.

## Contextos

- Construtor por contexto (`build(app, nome)`): descarta o doc, cria um novo, cria objetos via modelo e
  seleciona.
- Limitações do pywin32: não passa opcionais "Nothing". Passe todos os argumentos. Alguns métodos
  falham mesmo assim (no Corel, CreateBlend/Contour/DropShadow): use outro caminho ou pule e avise.
- Contextos que exigem mouse (células de tabela): ative a ferramenta via modelo e arraste com o mouse
  (`DocumentToScreen` dá as coordenadas).
- **Saia dos modos de edição** (PowerClip, símbolo, texto) antes de fechar o doc, senão a automação trava.
- **Soft reset:** fechar o doc logo depois de percorrer menus derrubou o Corel 3-4 vezes. Nas rodadas
  de menu, limpe a página em vez de fechar o documento.

## Quedas e recuperação

- `vivo()`: o processo existe e a janela principal responde (`SendMessageTimeout`).
- `recuperar(motivo)`:
  1. feche o Crash Report pelo X (nunca enviar);
  2. `taskkill` do app e do fantasma;
  3. `restart_app.py` (abre, espera, cria o doc base);
  4. reconecte o COM, refazendo as variáveis globais;
  5. registre e siga do próximo alvo.
- Alvos que derrubam o app de forma reproduzível: marque `reiniciar_depois` ou tire da lista e
  avise o usuário.
- Ao fechar o app com doc alterado, aparece "Save Drawing" direto. Antes, via modelo:
  `doc.Dirty=False; doc.Close()`. Na saída do trial, use o botão **Close** (nunca BUY NOW).

## Revisão visual

- Depois de cada lote, gere folhas de contato (`kit/folha_contato.py`) e **olhe**. Procure:
  - print vazio ou trocado (submenu errado);
  - tooltip salvo como janela;
  - outro monitor;
  - pastas pessoais;
  - "nada abriu" (alvo desativado ou coordenada errada).
- Apague os prints errados pelo caminho exato e registre no log (`fix_log.py`).

## Índice HTML

- `kit/gera_indice.py` gera `index.html` autocontido, com miniaturas JPEG em `_indice/`.
- O navegador interno do Claude não abre `file://`. Para testar, suba um `http.server` temporário via
  `.claude/launch.json` e **apague o launch.json depois**.
