"""Ferramenta de UI Automation isolada em processo proprio (pywinauto/comtypes no
Python 3.15 pode derrubar o processo; aqui, se cair, so este processo cai).

Uso:
  python uia_tool.py dump <hwnd>                 -> JSON com os elementos da janela
  python uia_tool.py do <hwnd> <acao> <chave>    -> executa a acao no elemento
     acoes: select | expand | collapse | invoke | scroll_down | scroll_top | focus
     chave: "<control_type>|<nome>|<n-esima ocorrencia>"
Imprime JSON {"ok": bool, ...}.
"""
import json
import sys
import warnings

warnings.filterwarnings("ignore")
from pywinauto import Desktop

TYPES = {"TabItem", "ListItem", "TreeItem", "ComboBox", "Button", "List", "Tree", "Tab", "Pane",
         "ScrollBar", "Hyperlink", "MenuItem", "SplitButton", "RadioButton", "CheckBox", "Edit",
         "Text", "DataItem", "Group", "Window", "Document", "Custom", "Spinner", "Slider"}


def patterns(el):
    out = []
    for name, attr in (("select", "selection_item"), ("expand", "expand_collapse"), ("invoke", "invoke"),
                       ("scroll", "scroll"), ("toggle", "toggle"), ("value", "value")):
        try:
            getattr(el.iface_selection_item if name == "select" else
                    el.iface_expand_collapse if name == "expand" else
                    el.iface_invoke if name == "invoke" else
                    el.iface_scroll if name == "scroll" else
                    el.iface_toggle if name == "toggle" else el.iface_value, "__class__")
            out.append(name)
        except Exception:
            pass
    return out


def elements(win):
    res, count = [], {}
    for el in win.descendants():
        info = el.element_info
        ct = info.control_type
        if ct not in TYPES:
            continue
        name = (info.name or "").strip()
        k = (ct, name)
        count[k] = count.get(k, 0) + 1
        try:
            r = el.rectangle()
            rect = [r.left, r.top, r.right, r.bottom]
        except Exception:
            rect = [0, 0, 0, 0]
        try:
            enabled = el.is_enabled()
        except Exception:
            enabled = None
        try:
            parent = el.parent()
            pinfo = f"{parent.element_info.control_type}|{(parent.element_info.name or '').strip()}"
        except Exception:
            pinfo = ""
        value = ""
        if ct == "ComboBox":
            try:
                value = (el.iface_value.CurrentValue or "").strip()
            except Exception:
                value = ""
        res.append({"key": f"{ct}|{name}|{count[k]}", "type": ct, "name": name, "rect": rect, "value": value,
                    "enabled": enabled, "auto_id": info.automation_id or "", "class": info.class_name or "",
                    "parent": pinfo, "patterns": patterns(el), "el": el})
    return res


def find(win, key):
    for e in elements(win):
        if e["key"] == key:
            return e["el"]
    return None


def run(cmd, hwnd, action=None, key=None):
    win = Desktop(backend="uia").window(handle=hwnd)
    if cmd == "dump":
        return [{k: v for k, v in e.items() if k != "el"} for e in elements(win)]
    el = find(win, key)
    if el is None:
        return {"ok": False, "erro": "elemento nao encontrado"}
    try:
        if action == "select":
            el.iface_selection_item.Select()
        elif action == "expand":
            el.iface_expand_collapse.Expand()
        elif action == "collapse":
            el.iface_expand_collapse.Collapse()
        elif action == "invoke":
            el.iface_invoke.Invoke()
        elif action == "scroll_down":
            sp = el.iface_scroll
            if not sp.CurrentVerticallyScrollable or sp.CurrentVerticalScrollPercent >= 99.9:
                return {"ok": False, "fim": True}
            sp.Scroll(0, 3)  # LargeIncrement vertical
        elif action == "scroll_top":
            sp = el.iface_scroll
            if not sp.CurrentVerticallyScrollable:
                return {"ok": False, "fim": True}
            sp.SetScrollPercent(-1, 0)
        elif action == "focus":
            el.set_focus()
        elif action == "rect":
            r = el.rectangle()
            return {"ok": True, "rect": [r.left, r.top, r.right, r.bottom]}
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "erro": str(e)[:200]}


def serve():
    """Le comandos JSON por linha no stdin e responde uma linha JSON por comando."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            c = json.loads(line)
            out = run(c["cmd"], int(c["hwnd"]), c.get("action"), c.get("key"))
        except Exception as e:
            out = {"ok": False, "erro": str(e)[:200]}
        sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def main():
    if sys.argv[1] == "serve":
        serve()
        return
    cmd, hwnd = sys.argv[1], int(sys.argv[2])
    win = Desktop(backend="uia").window(handle=hwnd)
    if cmd == "dump":
        out = [{k: v for k, v in e.items() if k != "el"} for e in elements(win)]
        print(json.dumps(out, ensure_ascii=False))
        return
    action, key = sys.argv[3], sys.argv[4]
    el = find(win, key)
    if el is None:
        print(json.dumps({"ok": False, "erro": "elemento nao encontrado"}))
        return
    try:
        if action == "select":
            el.iface_selection_item.Select()
        elif action == "expand":
            el.iface_expand_collapse.Expand()
        elif action == "collapse":
            el.iface_expand_collapse.Collapse()
        elif action == "invoke":
            el.iface_invoke.Invoke()
        elif action == "scroll_down":
            sp = el.iface_scroll
            if not sp.CurrentVerticallyScrollable or sp.CurrentVerticalScrollPercent >= 99.9:
                print(json.dumps({"ok": False, "fim": True}))
                return
            sp.Scroll(0, 3)  # ScrollAmount_LargeIncrement na vertical
        elif action == "scroll_top":
            el.iface_scroll.SetScrollPercent(-1, 0)
        elif action == "focus":
            el.set_focus()
        print(json.dumps({"ok": True}))
    except Exception as e:
        print(json.dumps({"ok": False, "erro": str(e)[:200]}))


if __name__ == "__main__":
    main()
