import win32com.client as w, pythoncom
app = w.Dispatch("CorelDRAW.Application.27")
def dump(obj, name):
    ti = obj._oleobj_.GetTypeInfo()
    ta = ti.GetTypeAttr()
    print("==", name, ti.GetDocumentation(-1)[0])
    seen=set()
    for i in range(ta.cFuncs):
        fd = ti.GetFuncDesc(i)
        names = ti.GetNames(fd.memid)
        if names[0] in seen: continue
        seen.add(names[0]); print("  ", names[0], names[1:], fd.invkind)
fw = app.FrameWork
dump(fw, "FrameWork")
dump(fw.Automation, "Automation")
