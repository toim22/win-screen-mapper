# Scripts reais do mapeamento do CorelDRAW 2026

Cópia da pasta `scripts\` do projeto original (nov/2026). Eles **não rodam
daqui**: dependem de `ROOT = ../MAPEAMENTO` e do Corel aberto. Servem de referência para adaptar.
O acervo produzido está descrito em `LEIA-ME-resultado.md`.

| etapa | script | o que faz |
|---|---|---|
| base | `corelui.py` | COM, pid, janelas, foco, clique, grab (origem do `kit/winui.py`) |
| base | `uia_tool.py`, `close_one.py`, `invoke_one.py` | UIA e InvokeItem em subprocesso |
| base | `restart_corel.py` | fecha descartando o doc, reabre, File > New > OK, imprime "pronto" |
| 1 | `com_probe.py`, `com_typeinfo.py`, `walk_probe.py`, `inventory.py` | explorar o modelo COM e montar o inventário (ao vivo + DrawUI.xml) |
| 2 | `crawl_menus.py`, `relatorio_menus.py` | menus por hover (`Crawler`: `targets`, `hover_open`, `explore`, linhas pela imagem) |
| 3 | `crawl_telas.py`, `relatorio_telas.py`, `probe_tela.py` | abrir cada tela pelo GUID, print, fechar; lista negra (`BLACKLIST`, `BLACK_WORDS`, `WEB`); reconexão `com()` |
| 4 | `crawl_dentro.py`, `crawl_botoes.py`, `crawl_visao.py`, `relatorio_dentro.py`, `dbg_combo.py` | abas, páginas, listas e rolagem via UIA; botões seguros; alvos por visão (`visao_alvos.json`) |
| 5 | `contextos.py`, `matriz_contextos.py`, `menus_contextos.py`, `crawl_contextos.py`, `relatorio_contextos.py` | construir 17 contextos via COM; matriz de habilitação; refazer só o que muda |
| 6 | `crawl_dockers.py`, `crawl_properties.py`, `crawl_ferramentas.py`, `crawl_barras.py`, `crawl_menus_contexto.py` | dockers com rolagem, abas do Properties pela imagem, flyouts e barras de propriedades, barras ocultas, clique direito |
| 6b | `gera_alvos.py` → `docker_alvos.json`, `crawl_dockers_dentro.py`, `folhas.py` | dockers por dentro por visão (origem do `kit/alvos_visao.py` e do `kit/folhas_regua.py`) |
| 7 | `relatorio_final.py`, `gera_indice.py` | cobertura final e index.html |
| util | `fix_log.py` | corrigir log depois de apagar prints errados |
