"""Etapa 5: monta cada contexto de teste no documento descartavel.

build(app, nome) descarta o documento atual (Dirty=False + Close, nunca salva), cria um
documento novo e desenha/seleciona os objetos do contexto. Assim cada tela parte do mesmo
estado, mesmo que a anterior tenha entrado num modo de edicao (simbolo, PowerClip etc.).

Uso direto (teste): python contextos.py retangulo
"""
import sys
import time

# ordem = ordem da varredura (a primeira tela habilitada fica no primeiro contexto que a liga)
CONTEXTOS = {
    "retangulo": "um retangulo selecionado",
    "elipse": "uma elipse selecionada",
    "curva": "uma curva (retangulo convertido em curvas) selecionada",
    "texto-artistico": "um texto artistico selecionado",
    "texto-paragrafo": "um texto de paragrafo selecionado",
    "bitmap": "um bitmap RGB selecionado (desenho convertido em bitmap)",
    "grupo": "um grupo de dois objetos selecionado",
    "selecao-multipla": "dois objetos selecionados (sem agrupar)",
    "tabela": "uma tabela 3x3 selecionada",
    "tabela-celulas": "tabela 3x3 com a ferramenta Table e 4 celulas selecionadas (arrastando o mouse)",
    "simbolo": "um simbolo (instancia) selecionado",
    "powerclip": "um PowerClip (retangulo dentro de elipse) selecionado",
    "linha-de-cota": "uma linha de cota horizontal selecionada",
    "conector": "um conector entre dois objetos selecionado",
    "varias-paginas": "documento com 3 paginas e um retangulo selecionado",
    "rollover": "um retangulo convertido em rollover (Object > Rollover > Create Rollover) selecionado",
    "com-efeitos": "objetos com envelope, perspectiva e distorcao na pagina + um retangulo simples selecionado",
}
TABLE_TOOL = "5507c778-4c9f-4933-b35f-9b6a15e084ec"   # ferramenta Table (flyout Text/Table)


# Object > PowerClip/Symmetry/Symbol/Rollover > Finish Editing: fechar o documento dentro de um
# desses modos de edicao trava a automacao, entao sai do modo antes.
FINISH = ["22eabb92-56f4-422d-bae7-16a7341c66b7", "755c36ec-f97f-4fc0-94fb-9445677d6ada",
          "f9d79c11-d3ea-418d-9535-e148da4a170c", "7b203f56-22d1-49fd-b942-3d626219c438"]


def finish_editing(app):
    au = app.FrameWork.Automation
    for _ in range(3):
        on = [g for g in FINISH if au.IsEnabled(g)]
        if not on:
            return
        for g in on:
            au.InvokeItem(g)
            time.sleep(0.7)


SOFT = False  # True: limpa o documento em vez de fechar (usado depois de percorrer menus)


def soft_reset(app):
    """Apaga tudo do documento aberto, sem fechar. Fechar o documento logo depois de percorrer
    menus derrubou/corrompeu o Corel 3 vezes; limpar a pagina nao."""
    d = app.ActiveDocument
    while d.Pages.Count > 1:
        d.Pages.Item(d.Pages.Count).Delete()
    for i in range(1, d.Pages.Count + 1):
        pg = d.Pages.Item(i)
        if pg.Shapes.Count:
            pg.Shapes.All().Delete()
    d.ClearSelection()
    try:
        app.ActiveTool = 1
    except Exception:
        pass
    d.Dirty = False
    return d


def reset_doc(app):
    finish_editing(app)
    if SOFT and app.Documents.Count:
        time.sleep(1)
        return soft_reset(app)
    while app.Documents.Count:
        d = app.Documents.Item(1)
        d.Dirty = False
        try:
            d.Close()
        except Exception:  # visto 1x: "server threw an exception" mas o documento fechou
            time.sleep(2)
        time.sleep(0.5)
    d = app.CreateDocument()
    time.sleep(1)
    try:
        app.ActiveTool = 1  # ferramenta Pick (o contexto tabela-celulas troca de ferramenta)
    except Exception:
        pass
    return d


def _rgb(shape, r, g, b):
    shape.Fill.UniformColor.RGBAssign(r, g, b)


def build(app, nome):
    d = reset_doc(app)
    lay = d.ActiveLayer
    if nome == "retangulo":
        s = lay.CreateRectangle2(2, 5, 3, 2)
        _rgb(s, 70, 130, 200)
        s.Selected = True
    elif nome == "elipse":
        s = lay.CreateEllipse2(4, 6, 1.5, 1)
        _rgb(s, 220, 120, 60)
        s.Selected = True
    elif nome == "curva":
        s = lay.CreateRectangle2(2, 5, 3, 2)
        s.ConvertToCurves()
        _rgb(s, 90, 170, 90)
        s.Selected = True
    elif nome == "texto-artistico":
        s = lay.CreateArtisticText(2, 6, "Texto artistico")
        s.Selected = True
    elif nome == "texto-paragrafo":
        s = lay.CreateParagraphText(1.5, 3, 7, 7, "Texto de paragrafo para teste. " * 6)
        s.Selected = True
    elif nome == "bitmap":
        a = lay.CreateRectangle2(2, 5, 3, 2)
        _rgb(a, 70, 130, 200)
        b = lay.CreateEllipse2(3.5, 6, 1, 0.7)
        _rgb(b, 240, 200, 40)
        g = d.CreateShapeRangeFromArray(a, b).Group()
        s = g.ConvertToBitmapEx(4, False, False, 150, 1, True)  # 4 = RGB
        d.ClearSelection()
        s.Selected = True
    elif nome in ("grupo", "selecao-multipla"):
        a = lay.CreateRectangle2(2, 5, 2, 1.5)
        _rgb(a, 70, 130, 200)
        b = lay.CreateEllipse2(5.5, 5.75, 1, 0.75)
        _rgb(b, 220, 120, 60)
        sr = d.CreateShapeRangeFromArray(a, b)
        d.ClearSelection()
        if nome == "grupo":
            sr.Group().Selected = True
        else:
            sr.AddToSelection()
    elif nome in ("tabela", "tabela-celulas"):
        s = lay.CreateCustomShape("Table", 1.5, 4, 6.5, 7, 3, 3)
        s.Selected = True
        if nome == "tabela-celulas":
            _drag_cells(app)
    elif nome == "simbolo":
        s = lay.CreateRectangle2(2, 5, 3, 2)
        _rgb(s, 70, 130, 200)
        inst = s.ConvertToSymbol("simbolo-teste")
        d.ClearSelection()
        inst.Selected = True
    elif nome == "powerclip":
        frame = lay.CreateEllipse2(4, 6, 2, 1.5)
        inner = lay.CreateRectangle2(2.5, 5, 3, 2)
        _rgb(inner, 70, 130, 200)
        inner.AddToPowerClip(frame)
        d.ClearSelection()
        frame.Selected = True
    elif nome == "linha-de-cota":
        lay.CreateRectangle2(2, 5, 3, 2)
        p1, p2 = d.CreateFreeSnapPoint(2, 7), d.CreateFreeSnapPoint(5, 7)
        blk = app.CreateRGBColor(0, 0, 0)
        # pywin32 nao passa os opcionais "Nothing": todos os argumentos explicitos
        s = lay.CreateLinearDimension(0, p1, p2, True, 3.5, 7.8, 0, 2, True, 3, 0, True, False, True,
                                      "", "", 0.003, app.ArrowHeads.Item(1), blk, "Arial", 10, blk)
        d.ClearSelection()
        s.Selected = True
    elif nome == "conector":
        a = lay.CreateRectangle2(1.5, 5, 1.5, 1)
        b = lay.CreateEllipse2(6, 5.5, 0.8, 0.5)
        s = lay.CreateConnector(a.SnapPoints.BBox(6), b.SnapPoints.BBox(5))
        d.ClearSelection()
        s.Selected = True
    elif nome == "varias-paginas":
        d.AddPages(2)
        d.Pages.Item(1).Activate()
        s = d.Pages.Item(1).ActiveLayer.CreateRectangle2(2, 5, 3, 2)
        s.Selected = True
    elif nome == "rollover":
        s = lay.CreateRectangle2(2, 5, 3, 2)
        _rgb(s, 70, 130, 200)
        d.ClearSelection()
        s.Selected = True
        app.FrameWork.Automation.InvokeItem(_guid("Object > Rollover > Create Rollover"))
        time.sleep(1)
    elif nome == "com-efeitos":
        lay.CreateRectangle2(0.5, 8, 1.5, 1.5).CreateEnvelope(1)
        lay.CreateRectangle2(3, 8, 1.5, 1.5).CreatePerspective(0, 0, 0, 0)
        lay.CreateRectangle2(5.5, 8, 1.5, 1.5).CreatePushPullDistortion(0, 0, 20)
        s = lay.CreateRectangle2(2, 3, 3, 2)
        _rgb(s, 70, 130, 200)
        d.ClearSelection()
        s.Selected = True
    else:
        raise ValueError(nome)
    d.Dirty = False
    time.sleep(0.5)
    return d


def _guid(path):
    import json
    from pathlib import Path
    inv = json.loads((Path(__file__).resolve().parent.parent / "MAPEAMENTO" / "01-inventario" / "inventory.json")
                     .read_text(encoding="utf-8"))
    return next(x["guid"] for x in inv if x["kind"] == "menu_item" and x["path"] == path)


def _drag_cells(app):
    """Ferramenta Table + arrasto da celula (1,1) ate a (2,2). Selecionar celula pela automacao
    (Cell.Select) nao liga os comandos de linha/coluna; o arrasto do mouse liga."""
    import win32api
    import win32con
    from corelui import corel_pid, force_foreground, main_window, move
    force_foreground(main_window(corel_pid()))
    app.FrameWork.Automation.InvokeItem(TABLE_TOOL)
    time.sleep(0.7)
    w = app.ActiveWindow
    a, b = w.DocumentToScreen(2.33, 6.5), w.DocumentToScreen(4.0, 5.5)
    move(*a)
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    time.sleep(0.2)
    for i in range(1, 11):
        move(a[0] + (b[0] - a[0]) * i / 10, a[1] + (b[1] - a[1]) * i / 10)
        time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    time.sleep(0.7)


def describe(app):
    d = app.ActiveDocument
    sel = d.SelectionRange
    return f"{d.Title} paginas={d.Pages.Count} selecao={sel.Count} " + \
        ",".join(str(sel.Item(i).Type) for i in range(1, sel.Count + 1))


if __name__ == "__main__":
    from corelui import connect
    app, _ = connect()
    for n in sys.argv[1:] or CONTEXTOS:
        try:
            build(app, n)
            print(f"{n:18s} ok   {describe(app)}")
        except Exception as e:
            print(f"{n:18s} ERRO {e}")
