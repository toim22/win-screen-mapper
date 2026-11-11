# 02. Descoberta do app (etapa 0)

Objetivo: descobrir **como** listar e acionar os comandos do app sem clicar às cegas. Gaste tempo aqui.
No Corel, o modelo COM e o XML de interface transformaram um trabalho de "clicar e torcer" num
crawler determinístico.

## 1. Perguntas ao usuário

Use `modelos/perguntas-iniciais.md`. O mínimo:
- app, versão e idioma;
- pasta de saída;
- se é versão de avaliação (avisos de trial);
- o que fica fora (menus, recursos online);
- quantos monitores o PC tem e em qual o app fica.

## 2. Reconhecimento sem clicar

Rode e anote (num `etapa0_reconhecimento.md` na pasta de scripts):

1. **Processo e janelas.** Nome do .exe, título da janela principal e classes das janelas
   (`win32gui.EnumWindows` + `GetClassName`). Monitores e coordenadas (com app num monitor à esquerda,
   as coordenadas são negativas). DPI: chame `SetProcessDpiAwareness(2)` antes de qualquer coordenada.
2. **Tecnologia da interface**, pela classe das janelas:
   | classe / sinal | tecnologia | o que funciona |
   |---|---|---|
   | `#32768` (menu), `#32770` (diálogo) | Win32 padrão | UIA e mensagens Win32 veem tudo; menus nativos dá para ler com `GetMenu`/`GetMenuItemInfo` |
   | `Afx:...` | MFC com controles próprios (Corel) | UIA vê só diálogos #32770; menus, dockers e barras são desenhados → COM + visão |
   | `Qt5QWindowIcon`, `Qt6...` | Qt | UIA razoável se a acessibilidade do Qt estiver ligada; menus são janelas Qt |
   | `HwndWrapper[...]` | WPF | UIA muito boa (AutomationId) |
   | `WindowsForms10.*` | WinForms | UIA boa |
   | `Chrome_WidgetWin_1` | Electron/Chromium | UIA parcial; talvez dê para usar `--remote-debugging-port` e ler o DOM (pergunte antes) |
   | `NetUIHWND`, `MsoCommandBar` | Office (Ribbon) | UIA boa para Ribbon; o COM do Office tem `CommandBars` |
3. **Modelo de automação.** Procure, nesta ordem:
   - **COM**: `win32com.client.gencache.EnsureDispatch("<ProgID>")`. Para achar o ProgID, veja
     `HKEY_CLASSES_ROOT\*.Application*` ou a documentação. Leia a type library (o `com_typeinfo.py` do
     exemplo lista métodos e propriedades). Procure algo como `CommandBars`, `FrameWork`, `Automation`,
     `ExecuteCommand`, `InvokeItem`, `ShowDialog`, `ShowDocker`, `IsEnabled`.
   - **Script do próprio app**: ExtendScript, VBA, AutoLISP, Python embutido, plug-in SDK.
   - **Linha de comando**: parâmetros para abrir sem tela inicial ou com workspace padrão.
4. **Definição da interface em arquivo.** Procure na pasta de instalação e em `%APPDATA%`:
   XML/JSON de workspace, menus, atalhos; `strings.xml`/`.resx`/`.qm` com os textos; recursos do
   executável (`RT_MENU`, `RT_DIALOG`), que dá para ler com `win32api.LoadResource` ou ferramentas de
   recurso. No Corel:
   - `DrawUI.xml` tinha a definição de todos os menus, diálogos, dockers e barras (937 definições);
   - `caption.csv` + `Languages\EN\Data\strings.xml` davam os nomes.
5. **Material antigo.** Pergunte se já existe engenharia reversa ou mapeamento anterior do app. No Corel
   havia uma pasta de outro agente com docs do modelo de automação, que poupou horas.
6. **Prova de conceito.** Antes de escrever o crawler, prove três coisas num script de teste:
   - listar os itens do menu raiz;
   - abrir **um** menu e achar a posição de **um** item (no Corel: `GetItemScreenRect`, só com o menu aberto);
   - abrir e fechar **um** diálogo com segurança.

## 3. Escolha da rota (vira `rota_menus` e `abrir_telas` no app.json)

Testes rápidos, sem clicar em nada:
```python
import projeto, winui as w
P = projeto.carregar()
print(w.user32.GetMenu(P.mw))       # != 0 → há menu Win32 nativo → rota "win32" é candidata
U = w.UIA(); els = U.dump(P.mw)
print([e["name"] for e in els if e["type"] == "MenuItem" and e["parent"].startswith("MenuBar|")])
# lista com File, Edit... → rota "uia" é candidata
```

```
Tem menu Win32 nativo (GetMenu != 0)?
├─ sim → rota_menus "win32"; abrir_telas "win32" (WM_COMMAND pelo id, sem navegar o menu).
│        Submenus vazios no inventário? → inventario.py --fonte win32 --completar.
└─ não → a UIA lista os itens da barra de menus?
         ├─ sim → rota "uia" (inventário e telas pela UIA; o crawler de menus usa a UIA também para
         │        achar os itens com submenu).
         └─ não → o app tem COM/script/SDK que lista e aciona comandos?
                  ├─ sim → rota "adaptador": inventario(), abrir_comando(item), rect_menu_raiz(nome)
                  │        (exemplo real: exemplos/corel/, que usava FrameWork.Automation do Corel).
                  └─ não → rota "visao": marque os menus da barra em folhas_regua.py (menus_raiz_manual);
                           os itens dos menus são achados pela imagem; as telas, por alvos_visao.py.
```

A rota pode mudar por etapa: por exemplo, menus pela UIA e painéis por visão. **Dentro das telas** use a
UIA onde houver (diálogos padrão: `crawl_telas.py --dentro`) e a **visão** onde o app desenha os
controles. Antes de rodar em lote, valide a rota escolhida com um menu só (`--only`) e mostre o
resultado ao usuário.

## 4. Inventário (etapa 1)

Gere `01-inventario/inventory.json` + `.csv`. Cada item traz:
- `source`: live (lido do app rodando) ou xml/recurso;
- `kind`: menu_root, menu_item, dialog, docker, toolbar…;
- `path` ("File > Import"), `caption`, `id`/`guid`, `has_submenu`, `enabled`, `visible`.

Junte o que vem do app rodando com o que vem dos arquivos. As definições que só existem no arquivo
viram "definições internas" no relatório final; muitas são achadas por outro caminho (mesmo nome de
janela, docker, barra).

No Corel: 787 itens de menu ao vivo e 937 definições internas, das quais 177 foram fotografadas por
outro caminho.

## 5. Contextos (planejar já na etapa 0)

Liste os estados que mudam a interface:
- sem documento e documento vazio;
- um objeto de cada tipo selecionado (retângulo, elipse, curva, texto artístico, texto de parágrafo,
  bitmap, grupo, tabela, cota, conector…);
- seleção múltipla;
- modos de edição (texto, nós, PowerClip, símbolo).

Para cada contexto, um construtor via COM/script (`contextos.py` no exemplo). Antes de fotografar, gere
a **matriz de habilitação**: quais itens ficam habilitados em cada contexto. Fotografe só o que muda em
relação ao doc vazio.
