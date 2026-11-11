---
name: win-screen-mapper
description: "Maps an entire Windows desktop application into an organized screenshot atlas: every menu and submenu, dialog with its tabs, pages and dropdowns, panels, toolboxes, toolbars and right-click menus, across selection contexts, ending with a coverage report and an offline HTML index. App-agnostic: works through UI Automation, native Win32 menus, the app's own automation (COM/scripting) or vision-based clicks, with strict safety rules (never confirms, saves, buys or sends anything; redacts personal folders). Use when the user wants screenshots of every screen or menu of a program, a UI inventory for training material or documentation, or asks to map an app's interface (e.g. 'tirar print de todas as telas e menus')."
---

# Mapear todas as telas de um app desktop (qualquer app)

Método genérico para fotografar a interface inteira de um programa do Windows. O **kit** (`kit/`) não
depende de nenhum app: tudo que muda de um app para outro fica em dois arquivos do projeto:
- **`app.json`**: exe, título, pasta de saída, rota, menus fora, lugares de clique direito;
- **adaptador** (opcional): `adaptador_<app>.py`, para o que só aquele app tem, como automação COM,
  painéis próprios e contextos.

O método nasceu no mapeamento do CorelDRAW 2026 (2.844 prints, 7 etapas). O Corel é só o **caso de
referência** (`referencias/05-caso-corel.md`, `exemplos/corel/`), não um requisito.

Comunicação: **no idioma do usuário** (a skill está escrita em português). Entregável: **só os prints**, organizados, com relatório do
que tem e do que faltou e por quê. **Não** escreva material de treinamento.

## Leia antes

| arquivo | quando |
|---|---|
| `referencias/01-regras-e-seguranca.md` | **sempre, antes de clicar em qualquer coisa** |
| `referencias/02-descoberta-do-app.md` | etapa 0: identificar a tecnologia do app e escolher a rota |
| `referencias/03-tecnicas.md` | ao rodar ou adaptar os crawlers (foco, hover, popups, visão, quedas) |
| `referencias/04-saida-e-relatorios.md` | pastas, nomes, formato dos logs, LEIA-ME, índice |
| `referencias/05-caso-corel.md` | exemplo completo com números e incidentes |
| `modelos/` | perguntas iniciais e modelo de LEIA-ME |

## As rotas (escolha na etapa 0; pode misturar)

| rota (`app.json`) | quando serve | como lista os menus | como abre as telas |
|---|---|---|---|
| `uia` | a UI Automation enxerga a barra de menus (Win32 padrão, WPF, WinForms, muito Qt) | `inventario.py --fonte uia` | `abrir_telas: uia` (expande o caminho e invoca) |
| `win32` | menu nativo do Windows (`GetMenu` ≠ 0; apps clássicos/MFC) | `inventario.py --fonte win32 [--completar]` | `abrir_telas: win32` (WM_COMMAND pelo id) |
| `adaptador` | o app tem automação própria (COM, script, SDK) ou arquivo de interface | `adaptador.inventario()` | `adaptador.abrir_comando(item)` |
| `visao` | nada disso enxerga (interface toda desenhada pelo app) | marcar os menus da barra em folhas com régua (`menus_raiz_manual`); itens achados pela imagem | `alvos_visao.py` com alvos marcados a olho |

Dentro das janelas, a UI Automation cobre abas, árvores, listas e botões padrão (`crawl_telas.py --dentro`).
O que o app desenha sozinho vai para o passe por visão (`alvos_visao.py`).

## Fluxo (uma etapa por vez, com o "sim" do usuário entre elas)

0. **Combinados e descoberta.** Pergunte o que está em `modelos/perguntas-iniciais.md`. Depois:
   - crie `<pasta>\scripts\` e copie o `kit/` para lá;
   - crie o `app.json` a partir de `app_modelo.json`;
   - descubra a tecnologia e a rota (`02-descoberta-do-app.md`);
   - escreva o `restart_app.py` a partir de `restart_app_modelo.py`;
   - faça backup do workspace/configuração do app;
   - mostre a lista negra (`lista_negra.py`) ao usuário.
1. **Inventário:** `python inventario.py`. Confira as contagens com o usuário.
2. **Menus:** `python crawl_menus.py --contexto doc-vazio`. Depois, folha de contato e revisão.
3. **Telas:** primeiro `python crawl_telas.py --dry`, mostrando ao usuário o que abre e o que fica de
   fora. Depois `python crawl_telas.py`.
4. **Dentro das telas:** `python crawl_telas.py --dentro` (UIA). Para o que a UIA não vê, o passe por
   visão: `folhas_regua.py` para marcar, depois `alvos_visao.py` com o adaptador.
5. **Contextos:** escreva `montar_contexto(nome)` no adaptador e repita as etapas 2 a 4 com
   `--contexto <nome>`. Fotografe só o que muda (compare habilitados por contexto).
6. **Painéis, ferramentas, barras, clique direito:**
   - `crawl_clique_direito.py`, com os lugares em `cliques_direitos`;
   - painéis e barras por dentro com `alvos_visao.py` e o adaptador (`abrir`/`fechar` do painel).
7. **Cobertura e índice:**
   - `python relatorio_cobertura.py [--extra <logs do alvos_visao>]`;
   - `python gera_indice.py --root <MAPEAMENTO> --titulo "<App>"`;
   - atualize o LEIA-ME (`modelos/LEIA-ME-modelo.md`) e dê o resumo final.

Rodadas longas vão **em segundo plano**, com log. Avise o tempo estimado. Ao terminar cada rodada,
gere **folhas de contato** (`folha_contato.py`) e **olhe os prints** antes de relatar.

## Como trabalhar com o usuário

- Ao fim de cada etapa, dê os números, o que ficou de fora e por quê, e as ocorrências. Depois pergunte
  se pode seguir.
- **Qualquer decisão ou problema, consulte o usuário**: item arriscado, janela inesperada, queda do app,
  algo que pareça pessoal, rota que não funcionou.
- Antes de instalar qualquer coisa (pywinauto, Pillow…), confira se já está instalado, pergunte ao usuário e siga as regras de instalação dele, se houver (ex.: um registro de instalações citado no CLAUDE.md).

## Regras que não se negociam (detalhes em 01)

- Nunca clicar em: OK, Apply, Save, Delete, Reset, Export, Print, Publish, Send, Buy/Purchase,
  "I agree", login/conta, atualizar, links que abrem o navegador. Também não fechar o app pelo menu.
- Fechar janelas por **Cancel / X**. Menus e listas desenhados pelo app fecham com **Esc**.
- Pergunta inesperada (Save changes?, Are you sure?): **Cancel** e a rodada para.
- **Crash Report: nunca enviar.** Feche pelo X.
- **Privacidade:**
  - capture só o que está **dentro da área do app**;
  - nos seletores de arquivo, **tarje** pastas e arquivos (o `crawl_telas.py` já faz isso; confira);
  - os arquivos do usuário não importam para o mapeamento.
- Use um documento descartável. Toda opção trocada volta ao padrão. Ao reiniciar o app, volte ao estado
  base (`restart_app.py`).

## Kit (`kit/`, tudo genérico)

| arquivo | papel |
|---|---|
| `app_modelo.json` | modelo do `app.json` do projeto (exe, título, saída, rota, menus fora, cliques direitos…) |
| `projeto.py` | carrega o `app.json`, conecta ao app, logs padrão, recuperação de quedas, contexto via adaptador |
| `winui.py` | janelas, foco sem Alt, mouse, hover com micro-movimentos, popups dentro do app, `eh_menu`, linhas de menu pela imagem, menus Win32, cliente UIA em subprocesso, captura, tarja |
| `uia_tool.py`, `close_one.py` | UI Automation (pywinauto) em processo separado (misturar com COM derrubou o Python) |
| `lista_negra.py` | o que nunca abrir (`item_bloqueado`) e nunca clicar (`classificar_botao`); perguntas que param a rodada |
| `inventario.py` | etapa 1 (uia / win32 / adaptador) → `01-inventario/inventory.json` e `.csv` |
| `crawl_menus.py` | etapas 2 e 5: menus e submenus só por hover |
| `crawl_telas.py` | etapas 3 e 4: abre, fotografa, explora por dentro (UIA) e fecha; tarja seletores de arquivo |
| `crawl_clique_direito.py` | etapa 6: menus de contexto nos lugares do `app.json` |
| `alvos_visao.py` + `adaptador_modelo.py` | passe por visão: alvos por coordenada (aba/lista/menu/expandir, antes/manter/voltar/rolar), submenus por hover, recuperação de quedas |
| `folhas_regua.py`, `folha_contato.py` | marcar alvos olhando a imagem; revisar dezenas de prints de uma vez |
| `restart_app_modelo.py` | reinício com estado base (descarta o doc, trial → Close, Crash Report → X) |
| `relatorio_cobertura.py`, `gera_indice.py` | etapa 7: cobertura cruzada e `index.html` offline |

Requisitos Python: `pywin32`, `Pillow` e `pywinauto` (este só nos subprocessos).

Os crawlers genéricos foram escritos a partir dos do Corel e testados com prints dele. **No primeiro app
novo, valide cada um numa rodada curta** (`--only` com um menu) e ajuste o kit com o que aprender.
Anote a lição em `referencias/03-tecnicas.md`.
