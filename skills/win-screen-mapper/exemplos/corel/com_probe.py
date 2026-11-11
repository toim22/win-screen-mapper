import win32com.client as w
app = w.Dispatch("CorelDRAW.Application.27")
cbs = app.CommandBars
for j in range(1, cbs.Count+1):
    cb = cbs.Item(j)
    print("BAR", j, repr(cb.Name), cb.Type if hasattr(cb,'Type') else '', cb.Controls.Count)
mb = cbs.Item("Menu Bar")
for i in range(1, mb.Controls.Count + 1):
    c = mb.Controls.Item(i)
    attrs = {}
    for a in ("Caption","ID","Enabled","Visible","IsCustom","DescriptionText","ToolTipText"):
        try: attrs[a] = getattr(c, a)
        except Exception as e: attrs[a] = "ERR"
    print(i, attrs)
