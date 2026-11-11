# 04. Estrutura de saída e relatórios

## Pastas

```
<pasta-do-projeto>\
├─ scripts\                  # crawlers e helpers deste app (cópia adaptada do kit)
├─ backup\Workspace-<data>\  # configuração do app antes de começar
└─ MAPEAMENTO\
   ├─ LEIA-ME.md             # o que tem, como está organizado, números, o que ficou de fora, ocorrências
   ├─ index.html             # índice navegável (etapa 7)
   ├─ _indice\               # miniaturas e dados do índice (gerado; pode apagar e refazer)
   ├─ 01-inventario\         # inventory.json/.csv (+ definições lidas de arquivos)
   ├─ 02-menus\<contexto>\   # File.png, File > Import.png …  + tela-inteira\
   ├─ 03-telas\<contexto>\   # um print por diálogo + dentro\<tela>\ (abas, páginas, listas)
   ├─ 04-dockers\            # painéis (partes de rolagem) + dentro\
   ├─ 05-ferramentas\        # flyouts + barra de propriedades por ferramenta
   ├─ 06-barras\             # barras de ferramentas ocultas/flutuantes
   ├─ 07-menus-contexto\     # clique direito por objeto/lugar
   └─ 90-relatorios\         # logs JSON de cada crawler + CSVs de cobertura + resumo_final.json
```

Adapte os números e nomes das pastas ao app (ex.: `04-paineis`, `05-ribbon`). Atualize o `SECOES` do
`gera_indice.py`.

## Nomes de arquivo

- O caminho do menu vira o nome: `File > Import.png` → `safe_name()` troca `\/:*?"<>|` por `_` e mantém
  ` > `. Use `▸` se `>` der problema.
- Partes de rolagem: `Nome (parte 2).png`. Estados internos: `Tela - aba X.png`, `Tela - lista Y.png`.
- Print da janela inteira com o mesmo nome, em `tela-inteira\`.
- Contexto na pasta, não no nome (`02-menus\retangulo\Object.png`).

## Logs (um por crawler, em 90-relatorios)

Os scripts do kit gravam (via `projeto.salvar_log`):

| log | quem grava | campos |
|---|---|---|
| `menus_<ctx>.json` | crawl_menus.py | path, status (ok/sem_submenu/erro), image, rects, note, contexto |
| `menus_contexto.json` | crawl_clique_direito.py | mesmos campos |
| `telas_<ctx>.json` | crawl_telas.py | path, status (ok/sem_janela/nao_abriu/nao_aberto/erro; adaptador pode usar painel), image, note, window_title, contexto |
| `dentro_<ctx>.json` | crawl_telas.py --dentro | tela, estado, image |
| `<nome>.json` | alvos_visao.py --log | painel, alvo, tipo, status, prints, nota |

- `nao_aberto` = lista negra ou decisão do usuário; o motivo vai em `note`.
- `nao_abriu` com "desativado" na nota = desativado naquele contexto.
- Script novo que você escrever para um app deve seguir o mesmo esquema. Assim o relatório final sai
  sem depender dos nomes de arquivo.

## Relatório de cobertura (etapa 7)

Cruze o inventário com todos os logs (`kit/relatorio_cobertura.py`; o original do Corel é
`exemplos/corel/relatorio_final.py`). Para cada item:
- em que print de menu ele aparece;
- o print da tela ou do submenu;
- quantos prints por dentro;
- a situação e o motivo.

Situações usadas:

| situação | quando |
|---|---|
| ok | tem print próprio |
| ok (abre no docker) | o comando abre um painel, fotografado em 04-dockers |
| ok (sem janela) | o comando age direto; o print mostra o efeito/painel |
| ok (aparece no print do menu) | comando simples: está visível no print do menu pai |
| não aberto de propósito | lista negra / decisão do usuário (motivo escrito) |
| desativado | não habilitou em nenhum contexto testado |
| oculto | existe no modelo, mas o app não mostra |
| fora do escopo | menu excluído (Purchase, Debug interno…) |

Saídas:
- `cobertura_final.csv` (delimitador `;` e UTF-8 com BOM, para abrir no Excel);
- `cobertura_definicoes_internas.csv`;
- `resumo_final.json` (totais por situação, tipo e pasta).

## LEIA-ME

Use `modelos/LEIA-ME-modelo.md`. Ele precisa ter:
- versão do app e data;
- como navegar (index.html primeiro);
- tabela de pastas com contagem;
- contextos;
- o que ficou de fora e por quê;
- **ocorrências** (quedas, prints apagados, tarjas);
- como refazer (scripts, ordem).

Atualize ao fim de **cada** etapa, não só no final.

## Índice HTML

`kit/gera_indice.py --root <MAPEAMENTO> --titulo "<App> - mapeamento"`:
- árvore à esquerda, com "Visão geral" (cards por seção);
- grade de miniaturas com carregamento preguiçoso;
- visualizador com setas, Esc e "tamanho real";
- busca;
- botão que mostra ou esconde as versões "tela inteira";
- aba **Cobertura** (KPIs, filtros, tabela) se existir `90-relatorios/cobertura_final.csv`;
- tema claro e escuro.

Funciona offline, abrindo o `index.html` com dois cliques. No Corel: 2.844 imagens em 28 s e 31 MB de
miniaturas.
