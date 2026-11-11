# Perguntas iniciais (etapa 0)

Faça estas perguntas antes de clicar em qualquer coisa. Quando der, use AskUserQuestion, com no máximo
4 perguntas por vez. Para o que tem padrão óbvio, proponha o padrão.

## Bloco 1: o app
1. Qual app e versão? Qual o idioma da interface? (O idioma define os nomes dos arquivos.)
2. É versão de avaliação? Tem login ou conta aberta? (Avisos de trial e login entram na lista negra.)
3. Já existe material sobre o app: documentação de automação, engenharia reversa, mapeamento anterior?

## Bloco 2: escopo
4. O que é para fotografar? Padrão: menus, submenus, telas e abas internas, painéis, ferramentas,
   barras e clique direito, em vários contextos.
5. Algum menu ou recurso fica de fora? Exemplos do Corel: Purchase, recursos online, Help que abre o navegador.
6. Contextos: quais tipos de objeto ou documento importam para o treinamento?

## Bloco 3: segurança (proponha o padrão de `01-regras-e-seguranca.md`)
7. A lista negra está aprovada? Exit, Save, Export, Print, Publish, conta, compra, update, macros,
   reset, programas externos.
8. Seletores de arquivo: só o que é do app, sem navegar pastas pessoais. Ok?
9. Pode reiniciar o app quando travar? Qual é o estado base depois de reiniciar (ex.: documento novo)?
10. Pode clicar por coordenada (passe por visão) onde a automação não enxerga?

## Bloco 4: saída
11. Pasta de saída. Sugestão: `<Documentos>\<app>-screenshots\MAPEAMENTO`.
12. Quer o índice HTML e o relatório de cobertura no final? (Padrão: sim, etapa 7.)

## Antes de começar, confirme
- backup do workspace/configuração do app feito;
- quantos monitores existem e em qual o app vai ficar (de preferência, maximizado num só);
- que o usuário não vai usar o PC durante as rodadas, porque o crawler mexe no mouse;
- as dependências Python verificadas (e as regras de instalação do usuário seguidas, se houver).
