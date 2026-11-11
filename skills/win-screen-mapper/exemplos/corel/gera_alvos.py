"""Gera docker_alvos.json (alvos marcados a olho nos prints com regua; x, y relativos ao painel).

Tipos: aba (clica e fotografa), lista/menu (fotografa o que abrir e fecha), expandir (abre, fotografa,
recolhe). "voltar" = onde clicar depois para devolver a opcao padrao. "antes" = cliques previos.
Nunca: Apply, Add, Create, Generate, I agree, Save, Export, Print, Load, Browse, zoom, History.
"""
import json
from pathlib import Path

A = []


def t(docker, nome, tipo, x, y, **kw):
    A.append({"docker": docker, "nome": nome, "tipo": tipo, "x": x, "y": y, **kw})


def tabs(docker, xs_nomes, y=44, voltar=None):
    for x, n in xs_nomes:
        if voltar and (voltar["x"], voltar["y"]) == (x, y):
            continue  # aba padrao: ja esta no print inicial
        t(docker, f"aba {n}", "aba", x, y, **({"voltar": voltar} if voltar else {}))


# 1 Properties (retangulo) - abas ja fotografadas em properties-abas; aqui os controles de cada aba
P = "Properties"
ab = lambda x: [{"x": x, "y": 44}]
t(P, "Resumo ▸ lista Wrap paragraph text", "lista", 92, 326, antes=ab(205))
t(P, "botao de exibicao 1", "expandir", 243, 44)
t(P, "botao de exibicao 2", "expandir", 275, 44)
t(P, "Contorno ▸ lista cor", "lista", 81, 103, antes=ab(13))
t(P, "Contorno ▸ lista largura", "lista", 82, 135, antes=ab(13))
t(P, "Contorno ▸ lista unidades", "lista", 187, 135, antes=ab(13))
t(P, "Contorno ▸ lista estilo de linha", "lista", 190, 167, antes=ab(13))
t(P, "Contorno ▸ editar estilo de linha (...)", "menu", 220, 167, antes=ab(13))
t(P, "Contorno ▸ recolher secao (^)", "expandir", 137, 242, antes=ab(13))
t(P, "Contorno ▸ lista ponta de seta inicial", "lista", 76, 457, antes=ab(13))
t(P, "Contorno ▸ lista ponta de seta final", "lista", 76, 489, antes=ab(13))
t(P, "Contorno ▸ opcoes da ponta inicial (...)", "menu", 105, 457, antes=ab(13))
t(P, "Contorno ▸ opcoes da ponta final (...)", "menu", 105, 489, antes=ab(13))
for x, n in [(14, "sem preenchimento"), (78, "gradiente"), (110, "padrao vetorial"), (142, "padrao bitmap")]:
    t(P, f"Preenchimento ▸ tipo {n}", "aba", x, 102, antes=ab(46))
t(P, "Preenchimento ▸ mais tipos (seta)", "menu", 174, 102, antes=ab(46))
t(P, "Preenchimento ▸ visualizador 2", "aba", 46, 143, antes=ab(46))
t(P, "Preenchimento ▸ visualizador 3", "aba", 78, 143, antes=ab(46))
t(P, "Preenchimento ▸ lista modelo de cor", "lista", 215, 175, antes=ab(46))
t(P, "Preenchimento ▸ menu engrenagem", "menu", 274, 175, antes=ab(46))
t(P, "Preenchimento ▸ menu (...)", "menu", 276, 414, antes=ab(46))
t(P, "Preenchimento ▸ recolher secao (^)", "expandir", 146, 453, antes=ab(46))
t(P, "Transparencia ▸ lista modo de mesclagem", "lista", 240, 103, antes=ab(77))
for x, n in [(46, "uniforme"), (78, "gradiente"), (110, "padrao vetorial"), (142, "padrao bitmap")]:
    t(P, f"Transparencia ▸ tipo {n}", "aba", x, 143, antes=ab(77))
t(P, "Transparencia ▸ mais tipos (seta)", "menu", 174, 143, antes=ab(77))
t(P, "Efeitos ▸ lista Presets", "lista", 240, 103, antes=ab(109))
t(P, "Efeitos ▸ menu adicionar (+)", "menu", 16, 306, antes=ab(109))
t(P, "Pincel ▸ lista Select a brush", "lista", 140, 125, antes=ab(173))
t(P, "Pincel ▸ lista cor do contorno", "lista", 115, 201, antes=ab(173))

# 2 Objects
O = "Objects"
t(O, "visualizacao 2 (camadas)", "aba", 45, 74, voltar={"x": 15, "y": 74})
t(O, "menu engrenagem", "menu", 274, 74, reiniciar_depois=True)  # derrubou o Corel 3x no passo seguinte

# 3 Pages
G = "Pages"
t(G, "botao 1 (exibicao)", "aba", 14, 74)
t(G, "botao 2 (exibicao)", "aba", 44, 74, voltar={"x": 14, "y": 74})
t(G, "menu de visualizacao", "menu", 243, 74)
t(G, "menu engrenagem", "menu", 275, 74)

# 4 Comments
t("Comments", "menu engrenagem", "menu", 275, 44)

# 5 Object Data
t("Object Data", "botao 1", "menu", 14, 44)
t("Object Data", "botao 2", "menu", 46, 44)

# 6 Object Styles
S = "Object Styles"
t(S, "item Styles", "aba", 56, 44)
t(S, "item Style Sets", "aba", 56, 70)
t(S, "expandir Default Object Properties", "expandir", 14, 93)
t(S, "menu novo estilo", "menu", 16, 127)

# 7 Symbols
Y = "Symbols"
t(Y, "menu engrenagem", "menu", 275, 44)
t(Y, "item Linked Symbols", "aba", 72, 167, voltar={"x": 72, "y": 143})
t(Y, "expandir Local Symbols", "expandir", 15, 191)
t(Y, "item Network Symbols", "aba", 90, 215, voltar={"x": 72, "y": 143})

# 8 Find and Replace
F = "Find and Replace"
t(F, "lista Find Objects", "lista", 144, 45)
t(F, "lista Custom (consultas salvas)", "lista", 114, 78)
t(F, "opcao Names or Styles", "aba", 25, 140, voltar={"x": 25, "y": 117})
for y, n in [(247, "contorno do objeto"), (281, "preenchimento"), (315, "contorno"), (349, "efeitos")]:
    t(F, f"consulta {n}", "menu", 18, y)
t(F, "expandir Search range", "expandir", 12, 503)

# 11 Transform / 12 Coordinates
tabs("Transform", [(12, "Position"), (45, "Rotate"), (78, "Scale and Mirror"), (110, "Size"), (143, "Skew")],
     voltar={"x": 12, "y": 44})
tabs("Coordinates", [(12, "Rectangle"), (45, "Ellipse"), (78, "Polygon"), (110, "Star"), (143, "Spiral"),
                     (175, "Line"), (208, "Curve")], voltar={"x": 12, "y": 44})

# 13 Live Guides
L = "Live Guides"
t(L, "botao 1", "expandir", 14, 44)
t(L, "botao 2", "expandir", 42, 44)
t(L, "recolher Alignment guides", "expandir", 12, 71)
t(L, "Alignment ▸ lista estilo de linha", "lista", 203, 99)
t(L, "Alignment ▸ lista cor", "lista", 260, 99)
t(L, "recolher Dynamic guides", "expandir", 12, 323)
t(L, "Dynamic ▸ lista estilo de linha", "lista", 203, 351)
t(L, "Dynamic ▸ lista cor", "lista", 260, 351)

# 14 Guidelines
U = "Guidelines"
t(U, "botao 1", "expandir", 16, 44)
t(U, "botao 2", "expandir", 48, 44)
t(U, "menu engrenagem", "menu", 273, 44)
t(U, "lista estilo de linha", "lista", 220, 78)
t(U, "lista cor", "lista", 276, 78)
t(U, "lista Horizontal", "lista", 276, 119)

# 15 Align and Distribute (so os modos; os botoes de alinhar sao acao)
D = "Align and Distribute"
for x, n in [(116, "2"), (147, "3"), (179, "4"), (211, "5")]:
    t(D, f"Align to ▸ opcao {n}", "aba", x, 126, voltar={"x": 83, "y": 126})
for x, n in [(138, "2"), (170, "3")]:
    t(D, f"Distribute to ▸ opcao {n}", "aba", x, 346, voltar={"x": 107, "y": 346})

# 16 Fit Objects to Path
for y, n in [(269, "Order"), (301, "Distribution"), (333, "Reference"), (525, "Style")]:
    t("Fit Objects to Path", f"lista {n}", "lista", 204, y)
t("Fit Objects to Path", "info (i)", "menu", 278, 138)
for y, n in [(574, "Uniform"), (598, "Progressive"), (622, "Jitter"), (647, "Progressive jitter")]:
    t("Fit Objects to Path", f"rotacao {n}", "aba", 240, y, antes=[{"x": 204, "y": 525, "manter": True}],
      voltar=[{"x": 204, "y": 525}, {"x": 240, "y": 549}])

# 17 Step and Repeat
R = "Step and Repeat"
t(R, "Horizontal ▸ lista modo", "lista", 142, 72)
t(R, "Vertical ▸ lista modo", "lista", 142, 197)
hs = [{"x": 142, "y": 72, "manter": True}, {"x": 60, "y": 147}]
vs = [{"x": 142, "y": 197, "manter": True}, {"x": 60, "y": 272}]
t(R, "Horizontal ▸ Spacing between objects ▸ lista Direction", "lista", 200, 136, antes=hs)
t(R, "Horizontal ▸ modo Spacing between objects", "aba", 60, 147, antes=[dict(hs[0], manter=True)],
  voltar=[{"x": 142, "y": 72}, {"x": 60, "y": 122}])
t(R, "Vertical ▸ Spacing between objects ▸ lista Direction", "lista", 200, 260, antes=vs)
t(R, "Vertical ▸ modo Spacing between objects", "aba", 60, 272, antes=[dict(vs[0], manter=True)],
  voltar=[{"x": 142, "y": 197}, {"x": 60, "y": 247}])
t(R, "recolher Horizontal Settings", "expandir", 12, 46)
t(R, "recolher Vertical Settings", "expandir", 12, 171)

# 18 Shape: a lista e cada operacao (o painel muda a figura e as opcoes)
t("Shape", "lista operacao (Weld)", "lista", 146, 46)
for y, n in [(95, "Trim"), (120, "Intersect"), (145, "Simplify"), (170, "Front minus back"),
             (195, "Back minus front"), (220, "Boundary")]:
    t("Shape", f"operacao {n}", "aba", 60, y, antes=[{"x": 146, "y": 46, "manter": True}],
      voltar=[{"x": 146, "y": 46}, {"x": 60, "y": 70}])

# 19 Corners / 20 Join Curves
t("Corners", "opcao Scallop", "aba", 9, 79, voltar={"x": 9, "y": 46})
t("Corners", "opcao Chamfer", "aba", 9, 112, voltar={"x": 9, "y": 46})
for y, n in [(65, "Chamfer"), (88, "Fillet"), (111, "Bezier Curve")]:
    t("Join Curves", f"opcao {n}", "aba", 10, y, voltar={"x": 10, "y": 42})

# 21 Text (texto-artistico)
T = "Text"
t(T, "aba Paragraph", "aba", 46, 44, voltar={"x": 14, "y": 44})
t(T, "aba Frame", "aba", 78, 44, voltar={"x": 14, "y": 44})
t(T, "botao de exibicao 1", "expandir", 243, 44)
t(T, "botao de exibicao 2", "expandir", 275, 44)
t(T, "lista fonte", "lista", 150, 103)
t(T, "lista estilo da fonte", "lista", 150, 135)
t(T, "lista tamanho", "lista", 248, 103)
t(T, "lista maiusculas (AA)", "lista", 238, 135)
t(T, "lista sublinhado", "lista", 268, 178)
for y, n in [(210, "preenchimento do texto"), (242, "fundo"), (274, "contorno")]:
    t(T, f"lista tipo de {n}", "lista", 150, y)
    t(T, f"lista cor de {n}", "lista", 211, y)
    t(T, f"configuracoes de {n} (...)", "menu", 239, y)
t(T, "mais opcoes de caractere (v)", "expandir", 136, 315)
t(T, "Paragraph ▸ menu engrenagem", "menu", 240, 346)
t(T, "Paragraph ▸ lista unidade do espacamento", "lista", 222, 419)

# 22 Font Sampler / 23 Glyphs / 24 Artistic Media
t("Font Sampler", "lista fonte", "lista", 146, 46)
t("Font Sampler", "visualizacao 2", "aba", 48, 86, voltar={"x": 16, "y": 86})
t("Font Sampler", "visualizacao 3", "aba", 78, 86, voltar={"x": 16, "y": 86})
t("Glyphs", "lista fonte", "lista", 145, 159)
t("Glyphs", "lista Entire Font", "lista", 145, 191)
t("Effects > Artistic Media", "lista Stroke type", "lista", 124, 254)
t("Effects > Artistic Media", "menu engrenagem", "menu", 274, 254)

# 25 Bevel
B = "Effects > Bevel"
t(B, "opcao Emboss", "aba", 11, 88, voltar={"x": 11, "y": 65})
t(B, "opcao To center", "aba", 11, 145, voltar={"x": 11, "y": 172})
t(B, "lista Shadow color", "lista", 150, 215)
t(B, "lista Light color", "lista", 150, 302)

# 26 Bitmap Mask
t("Effects > Bitmap Mask", "abrir mascara (pasta)", "menu", 46, 267)

# 27 Blend
N = "Effects > Blend"
t(N, "modo espacamento", "aba", 117, 44, voltar={"x": 85, "y": 44})
t(N, "lista passos", "lista", 197, 83)
t(N, "Color Blend ▸ opcao 2", "aba", 117, 437, voltar={"x": 85, "y": 437})
t(N, "Color Blend ▸ opcao 3", "aba", 149, 437, voltar={"x": 85, "y": 437})
t(N, "mais opcoes (v)", "expandir", 145, 507)

# 28 Contour
C = "Effects > Contour"
t(C, "alinhamento ▸ opcao 1", "aba", 14, 68, voltar={"x": 46, "y": 68})
t(C, "alinhamento ▸ opcao 3", "aba", 78, 68, voltar={"x": 46, "y": 68})
for x in (46, 78):
    t(C, f"Corner ▸ opcao {x // 32 + 1}", "aba", x, 210, voltar={"x": 14, "y": 210})
    t(C, f"Color blend ▸ opcao {x // 32 + 1}", "aba", x, 307, voltar={"x": 14, "y": 307})
t(C, "lista cor do contorno", "lista", 207, 350)
t(C, "lista cor do preenchimento", "lista", 207, 382)

# 29 Envelope
E = "Effects > Envelope"
for x, n in [(44, "2"), (78, "3"), (110, "4")]:
    t(E, f"modo {n}", "aba", x, 330, voltar={"x": 14, "y": 330})
t(E, "lista mapeamento (Putty)", "lista", 248, 330)

# 30 Extrude
tabs("Effects > Extrude", [(48, "2"), (80, "3"), (112, "4"), (144, "5")], voltar={"x": 16, "y": 44})

# 31 Lens
t("Effects > Lens", "lista tipo de lente", "lista", 145, 46)
for k, n in enumerate(["Brighten", "Color Add", "Color Limit", "Custom Color Map", "Fish Eye", "Heat Map", "Invert",
                       "Magnify", "Tinted Grayscale", "Transparency", "Wireframe", "Bitmap Effect"]):
    t("Effects > Lens", f"lente {n}", "aba", 60, 97 + 25 * k, antes=[{"x": 145, "y": 46, "manter": True}])

# 33 Pointillizer
t("Effects > Pointillizer", "lista Method", "lista", 198, 291)
t("Effects > Pointillizer", "lista Shape", "lista", 150, 400)

# 34 Color
K = "Color"
tabs(K, [(48, "Sliders"), (80, "Palettes")], voltar={"x": 16, "y": 44})
t(K, "lista modelo de cor", "lista", 126, 78)
t(K, "menu engrenagem", "menu", 273, 78)
t(K, "menu (...)", "menu", 274, 316)

# 35 Palettes
t("Palettes", "menu engrenagem", "menu", 275, 46)
t("Palettes", "recolher Palette Libraries", "expandir", 18, 150)
t("Palettes", "expandir Process", "expandir", 36, 174)
t("Palettes", "expandir Spot", "expandir", 36, 198)

# 36 Color Styles
t("Color Styles", "botao exibicao (olho)", "expandir", 244, 46)
t("Color Styles", "menu canto superior", "menu", 276, 46)
t("Color Styles", "menu novo estilo de cor", "menu", 16, 250)
t("Color Styles", "menu nova harmonia", "menu", 48, 250)
t("Color Styles", "lista Custom", "lista", 144, 282)

# 37 Color Proofing
Q = "Color Proofing"
t(Q, "lista cor do aviso de gama", "lista", 32, 115)
t(Q, "lista Proof preset", "lista", 60, 170)
t(Q, "lista Simulate environment", "lista", 150, 226)
t(Q, "lista Rendering intent", "lista", 150, 302)

# 38 Assets
W = "Assets"
t(W, "fonte 2 (nuvem)", "aba", 44, 74, voltar={"x": 12, "y": 74})
t(W, "fonte 3 (links)", "aba", 76, 74, voltar={"x": 12, "y": 74})
t(W, "menu engrenagem", "menu", 273, 44)
t(W, "lista ordenar (Name)", "lista", 277, 103)
t(W, "lista categorias", "lista", 179, 132)
t(W, "visualizacao 2", "aba", 241, 132, voltar={"x": 209, "y": 132})

# 39 Tray / 40 Links and Rollovers
t("Tray", "lista bandeja", "lista", 243, 45)
t("Tray", "menu engrenagem", "menu", 273, 45)
K2 = "Links and Rollovers"
t(K2, "lista Behavior", "lista", 275, 69)
t(K2, "lista URL", "lista", 275, 124)
t(K2, "lista cor Cross-hatch", "lista", 129, 330)
t(K2, "lista cor Background", "lista", 129, 362)
t(K2, "lista estado do rollover", "lista", 193, 521)

# 42 Views / 44 Scripts / 45 Learn
t("Views", "menu engrenagem", "menu", 273, 44)
for y, n in [(98, "VSTAGlobal"), (146, "GlobalMacros"), (266, "VBAProject (Untitled-1)")]:
    t("Scripts", f"expandir {n}", "expandir", 33, y)
t("Learn", "aba 2", "aba", 46, 44, voltar={"x": 14, "y": 44})

out = Path(__file__).with_name("docker_alvos.json")
out.write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(A), "alvos ->", out)
