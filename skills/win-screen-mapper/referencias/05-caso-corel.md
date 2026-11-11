# 05. Caso de referência: CorelDRAW 2026 (v27.2, inglês), nov/2026

O projeto completo, para comparar e copiar. Os scripts originais estão em `exemplos/corel/` e o LEIA-ME
final em `exemplos/corel/LEIA-ME-resultado.md`.

- Pasta original: `<pasta do projeto>\corel-screenshots\`
  (`scripts\`, `MAPEAMENTO\`, `backup\`).
- Plano inicial: `modelos/plano-original-corel.md`.

## Ambiente

- Windows 11, dois monitores. O Corel ficava no da **esquerda** (coordenadas negativas).
- Python 3.15 com pywin32, Pillow e pywinauto (este só em subprocesso).
- Corel em versão de avaliação: aviso de trial ao sair (botão **Close**, nunca BUY NOW).
- Superfície de automação:
  - COM `CorelDRAW.Application.27`, com `app.FrameWork.Automation`
    (GetNumItemsOnBar, GetItem, GetSubBar, GetCaptionText, IsEnabled, GetItemScreenRect, InvokeItem,
    ShowDialog, ShowDocker);
  - `DrawUI.xml`, `caption.csv` e `strings.xml` para nomes e definições.
- GUID da barra de menus: `f3016f3c-2847-4557-b61a-a2d05319cf18`.

## Etapas e números

| etapa | o que | resultado | scripts |
|---|---|---|---|
| 1 | inventário | 1.724 itens (787 de menu ao vivo + 937 definições do XML) | inventory.py, com_probe.py, com_typeinfo.py |
| 2 | menus, doc vazio | 75 prints (12 menus + 63 submenus) | crawl_menus.py |
| 3 | telas, doc vazio | 43 telas; 189 desativadas passaram para a etapa 5 | crawl_telas.py, invoke_one.py, close_one.py |
| 4 | dentro das telas | 523 prints (382 UIA, 9 botões, 132 por visão) | crawl_dentro.py, crawl_botoes.py, crawl_visao.py, uia_tool.py |
| 5 | 17 contextos | 416 prints de menu e 157 telas (37 janelas + 120 efeitos no docker); 163 por dentro | contextos.py, matriz_contextos.py, menus_contextos.py, crawl_contextos.py |
| 6 | dockers, ferramentas, barras, clique direito | 45 dockers, 15 flyouts, 60 barras de propriedades, Pick em 18 contextos, 12 barras, 23 lugares de clique direito | crawl_dockers.py, crawl_properties.py, crawl_ferramentas.py, crawl_barras.py, crawl_menus_contexto.py |
| 6b | dockers por dentro | 223 alvos, 239 prints, 40 dockers | gera_alvos.py, crawl_dockers_dentro.py |
| 7 | cobertura + índice | 2.844 prints no index.html; 787 itens: 598 com print, 144 fora do escopo, 27 não abertos de propósito, 14 desativados, 3 ocultos, 1 sem janela | relatorio_final.py, gera_indice.py |

O total levou um dia longo de trabalho, com várias rodadas em segundo plano de 10 a 40 minutos cada.

## Decisões do usuário (viraram regra)

- Fora: menu **Purchase** (pedido) e menu Debug (oculto).
- Help: só menus e submenus; itens que abrem o navegador ficam fora.
- Seletores de arquivo: só o que é do app. Uma rodada navegou pelas pastas pessoais (575 prints) e foi
  refeita (16 prints).
- Botões que abrem janelas filhas podem ser clicados. OK, Apply, Delete, Reset, Save, conta e compra, nunca.
- Passe por visão (clique por coordenada) aprovado.
- Reiniciar permitido, sempre com File > New > OK.
- Dockers por dentro: primeiro ficou pendente. Depois o usuário pediu "o mais completo possível, mesmo
  que leve 2 horas", e foi feito.

## Incidentes (e o que virou regra)

| incidente | correção |
|---|---|
| Fechar o Script Editor perguntou "Save changes to Untitled-1?" | resposta Cancel; item na lista negra; qualquer Yes/No/Cancel → Cancel e para |
| Options > VBA > Security Options travou o Corel ao fechar | nunca clicar; Crash Report fechado pelo X sem enviar |
| Fechar o doc logo após percorrer menus derrubou o Corel (3-4x) | soft reset: limpar a página em vez de fechar |
| Menu engrenagem do Objects derrubava no passo seguinte | `reiniciar_depois` |
| WM_CLOSE em menu Afx derrubou o Corel | Esc para menus/listas do app |
| COM reconectou com o Corel fechado → instância fantasma | `vivo()` antes; taskkill + restart_corel.py |
| Esc do menu tirava a seleção (menus de contexto saíram sem seleção) | remontar o contexto antes de cada menu raiz |
| Popup de tamanho zero → "cannot write empty image" | filtrar visíveis com tamanho |
| Print pegou o outro monitor com o chat do usuário | apagado; popups só dentro da janela do app |
| Seletor de arquivos mostrou pastas pessoais | tarja no print |
| Janela tipo tooltip salva como "▸ janela" | apagada; filtro de tamanho mínimo |
| Clicar na árvore do Objects trocou a camada ativa | alvos removidos |
| Lista fechava (Esc) antes de escolher o item | opção `manter` |
| Coordenadas convertidas errado da folha (Fill gear, "...", Color Proofing) | refeitas; ancorar no lado certo quando o painel muda de largura |
| Color Management parou de abrir | reiniciar o Corel |
| Dockers voltavam abertos após reinício | `fechar_todos()` antes de cada alvo |
| `Documents.Item(1).Activate()` falhou após What's New | clicar na aba do documento |
| COM + pywinauto no mesmo processo derrubou o Python 3.15 | UIA só em subprocesso |
| Alt para foco abria o menu errado | clicar na barra de título |
| `file://` bloqueado no navegador interno | http.server temporário via launch.json (apagado) |

## O que eu faria diferente num app novo

1. Escrever o `restart_app.py` e o `vivo()/recuperar()` **no primeiro dia**, não depois da primeira queda.
2. Gravar todos os logs com o mesmo esquema (`path/status/image/note/contexto`) desde a etapa 2, para o
   relatório final sair sem adaptações.
3. Já na etapa 0, combinar com o usuário a lista negra, o Help e os seletores de arquivo.
4. Montar o filtro de "popup dentro da área do app" desde o primeiro crawler.
5. Folha de contato ao fim de cada rodada, sempre.
