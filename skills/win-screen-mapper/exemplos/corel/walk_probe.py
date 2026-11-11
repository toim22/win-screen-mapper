from win32com.client import gencache
app = gencache.EnsureDispatch("CorelDRAW.Application.27")
au = app.FrameWork.Automation
MENUBAR = "f3016f3c-2847-4557-b61a-a2d05319cf18"
FILE = "7aa80134-8e64-42d1-be0a-c7ec7f6c441f"
sub = au.GetSubBar(FILE)[1]; print("File subbar", sub)
def walk(bar, depth, maxd=3):
    n = au.GetNumItemsOnBar(bar)
    for i in range(n):
        g, has = au.GetItem(bar, i)
        cap = au.GetCaptionText(g)
        try: en = au.IsEnabled(g)
        except Exception: en = "?"
        print("  "*depth + f"[{i}] {cap!r} {g} sub={has} en={en}")
        if has and depth < maxd:
            ok, sb = au.GetSubBar(g)
            if ok: walk(sb, depth+1, maxd)
walk(sub, 0)
