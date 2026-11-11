# MAPEAMENTO: telas do <APP> <VERSÃO> (<idioma>)

Prints de todos os menus, submenus, telas (janelas/diálogos), subtelas, painéis e barras do
<APP> <VERSÃO>, interface em <idioma>, para o time que monta o treinamento. Feito em <data>.

**Comece pelo `index.html`** (dois cliques; funciona offline). Ele tem a árvore de pastas, a busca, o
visualizador e a aba **Cobertura** (o que tem print e o que ficou de fora, com o motivo).

## Como está organizado

```
MAPEAMENTO/
├─ LEIA-ME.md            este arquivo
├─ index.html            índice navegável
├─ 01-inventario/        lista-mestra de tudo que existe na interface (inventory.csv abre no Excel)
├─ 02-menus/<contexto>/  NN Menu/ → 001 Menu.png, 002 Menu ▸ Submenu.png … + tela-inteira/
├─ 03-telas/<contexto>/  um print por janela + pasta com o que tem dentro (abas, páginas, listas)
├─ 04-<painéis>/         cada painel, com partes de rolagem; dentro/ = abas, listas e menus
├─ 05-ferramentas/       flyouts e barra de propriedades de cada ferramenta
├─ 06-barras/            barras de ferramentas (inclusive as ocultas)
├─ 07-menus-de-contexto/ clique direito por objeto e por lugar
└─ 90-relatorios/        logs e relatórios de cobertura
```

**Nomes:** número na ordem do menu + caminho completo, com `▸` no lugar de `>`.
**Contextos:** pastas como `doc-vazio`, `retangulo`, `texto` mostram a mesma tela com aquele objeto
selecionado.

## Números

| etapa | o que | situação |
|---|---|---|
| 1 | Inventário | <n> itens |
| 2 | Menus e submenus | <n> prints |
| 3 | Telas | <n> telas |
| 4 | Dentro das telas | <n> prints |
| 5 | Contextos | <n> contextos; <n> prints |
| 6 | Painéis, ferramentas, barras, clique direito | <n> |
| 7 | Cobertura + índice | <n> prints no índice; <n> itens na cobertura |

## Fora do escopo e não aberto de propósito

- <menu X> (decisão do usuário).
- Lista negra: Exit, Save, Export, Print, Publish, conta, compra, atualizações, macros, reset de
  configurações, programas externos.
- Help: só menus e submenus (os itens que abrem o navegador não foram abertos).
- Seletores de arquivo: só o que é do app; as pastas pessoais foram **tarjadas**.

## Ocorrências

- <data>: <o que aconteceu> → <o que foi feito>. Nada foi salvo; o Crash Report foi fechado sem enviar.

## Como refazer

Os scripts ficam em `<pasta>\scripts`. Ordem: inventário → menus → telas → dentro → contextos →
painéis/ferramentas/barras/clique direito → relatório final → índice.
