"""Etapa 1: inventario completo da UI do CorelDRAW 2026 (nao clica em nada).

Fontes:
  - Arvore real de menus, lida do Corel em execucao via COM (FrameWork.Automation).
  - DrawUI.xml / DrawUI.dialogs.xml / DrawUI.items.xml (somente leitura) para
    dockers, dialogos, toolbars e menus que nao estao pendurados na barra de menus
    (menus de contexto etc.).

Saida: ../inventory/inventory.json e inventory.csv
"""
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from win32com.client import gencache

UICONFIG = Path(r"C:\Program Files\Corel\CorelDRAW Graphics Suite\27\Draw\UIConfig")
OUT = Path(__file__).resolve().parent.parent / "MAPEAMENTO" / "01-inventario"
MENUBAR = "f3016f3c-2847-4557-b61a-a2d05319cf18"
SEPARATOR = "266435b4-6e53-460f-9fa7-f45be187d400"

app = gencache.EnsureDispatch("CorelDRAW.Application.27")
au = app.FrameWork.Automation


CORE = UICONFIG.parent.parent
# Cadeia de nomes (descoberta no mapeamento do DeepSeek Harness):
#   GUID do item -> Resources\caption.csv -> GUID de string -> Languages\EN\Data\strings.xml -> texto
CAP_MAP = {}
for line in (CORE / "Resources" / "caption.csv").read_text(encoding="utf-8-sig").splitlines():
    a, _, b = line.partition(",")
    if b:
        CAP_MAP[a.strip().lower()] = b.strip().lower()
STRINGS = {s.get("guid", "").lower(): (s.text or "")
           for s in ET.parse(CORE / "Languages" / "EN" / "Data" / "strings.xml").getroot().iter("string")}
CT = re.compile(r"([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})", re.I)


def xml_name(attrs):
    """Nome pelo XML: captionRef/caption/title (*CT('guid')) ou o proprio GUID via caption.csv."""
    cands = []
    for k in ("captionRef", "caption", "title", "text"):
        v = attrs.get(k, "")
        m = CT.search(v)
        if m:
            cands.append(m.group(1))
        elif v and not v.startswith("*"):
            return v
    cands.append(attrs.get("guid", ""))
    for g in cands:
        g = g.lower()
        s = STRINGS.get(CAP_MAP.get(g, g), "")
        if s:
            return s
    return ""


def caption(guid):
    try:
        c = au.GetCaptionText(guid) or ""
    except Exception:
        c = ""
    return c or xml_name({"guid": guid})


def clean(cap):
    cap = cap.replace("&&", "\0").replace("&", "").replace("\0", "&")
    return cap.replace("\u2026", "...").strip()


def enabled(guid):
    try:
        return bool(au.IsEnabled(guid))
    except Exception:
        return None


# ---------- XML ----------
items_xml = {}
for el in ET.parse(UICONFIG / "DrawUI.items.xml").getroot().iter("itemData"):
    items_xml[el.get("guid", "").lower()] = el.attrib

ui = ET.parse(UICONFIG / "DrawUI.xml").getroot()
bars_xml = {}
for cb in ui.iter("commandBarData"):
    bars_xml[cb.get("guid", "").lower()] = cb.attrib
dockers_xml = [d.attrib for d in ui.iter("dockerData")]
dialogs_xml = [d.attrib for d in ET.parse(UICONFIG / "DrawUI.dialogs.xml").getroot().findall("dialog")]

rows = []
seen_bars = set()


def add(**kw):
    kw.setdefault("source", "")
    rows.append(kw)


# ---------- 1) Arvore de menus ao vivo ----------
def walk(bar, path, depth):
    seen_bars.add(bar.lower())
    n = au.GetNumItemsOnBar(bar)
    for i in range(n):
        g, has_sub = au.GetItem(bar, i)
        if g.lower() == SEPARATOR:
            continue
        raw = caption(g)
        cap = clean(raw)
        x = items_xml.get(g.lower(), {})
        p = path + [cap or f"<{x.get('type', 'item')} {g[:8]}>"]
        add(kind="menu_item", path=" > ".join(p), caption=cap, raw_caption=raw, guid=g,
            depth=depth, index=i, has_submenu=bool(has_sub), enabled=enabled(g),
            xml_type=x.get("type", ""), opens_dialog_hint=raw.rstrip().endswith(("...", "\u2026")),
            parent_bar=bar, source="live")
        if has_sub:
            ok, sb = au.GetSubBar(g)
            if ok and sb and sb.lower() not in seen_bars:
                walk(sb, p, depth + 1)


mb = app.CommandBars.Item("Menu Bar")
for i in range(1, mb.Controls.Count + 1):
    c = mb.Controls.Item(i)
    g = c.ID
    cap = clean(c.Caption) or clean(caption(g)) or f"<{g[:8]}>"
    ok, sb = au.GetSubBar(g)
    add(kind="menu_root", path=cap, caption=cap, raw_caption=c.Caption, guid=g, depth=0, index=i - 1,
        has_submenu=bool(ok), enabled=enabled(g), xml_type=items_xml.get(g.lower(), {}).get("type", ""),
        opens_dialog_hint=False, parent_bar=MENUBAR, source="live")
    if ok and sb:
        walk(sb, [cap], 1)

# ---------- 2) Menus nao alcancados pela barra (contexto, flyouts de toolbars...) ----------
for g, a in bars_xml.items():
    if a.get("type") != "menu" or g in seen_bars:
        continue
    name = a.get("nonLocalizableName") or clean(caption(g)) or g[:8]
    try:
        n = au.GetNumItemsOnBar(g)
    except Exception:
        n = -1
    add(kind="other_menu", path=f"[Menus] {name}", caption=name, raw_caption="", guid=g, depth=0,
        index=0, has_submenu=n > 0, enabled=None, xml_type="menu", opens_dialog_hint=False,
        parent_bar="", source="xml", items=n)

# ---------- 3) Toolbars ----------
for g, a in bars_xml.items():
    if a.get("type") != "toolbar":
        continue
    name = a.get("nonLocalizableName") or clean(caption(g)) or g[:8]
    add(kind="toolbar", path=f"[Toolbars] {name}", caption=name, raw_caption="", guid=g, depth=0,
        index=0, has_submenu=False, enabled=None, xml_type="toolbar", opens_dialog_hint=False,
        parent_bar="", source="xml")

# ---------- 4) Dockers ----------
for a in dockers_xml:
    g = a.get("guid", "")
    name = clean(caption(g)) or clean(xml_name(a)) or a.get("nonLocalizableName", "") or g[:8]
    add(kind="docker", path=f"[Dockers] {name}", caption=name, raw_caption="", guid=g, depth=0,
        index=0, has_submenu=False, enabled=None, xml_type="docker", opens_dialog_hint=False,
        parent_bar="", source="xml")

# ---------- 5) Dialogos ----------
for a in dialogs_xml:
    g = a.get("guid", "")
    name = clean(caption(g)) or clean(xml_name(a)) or a.get("nonLocalizableName", "") or g[:8]
    add(kind="dialog", path=f"[Dialogs] {name}", caption=name, raw_caption="", guid=g, depth=0,
        index=0, has_submenu=False, enabled=None, xml_type="dialog", opens_dialog_hint=True,
        parent_bar="", source="xml")

OUT.mkdir(exist_ok=True)
(OUT / "inventory.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
fields = ["kind", "path", "caption", "guid", "depth", "has_submenu", "enabled", "opens_dialog_hint",
          "xml_type", "source", "raw_caption", "index", "parent_bar", "items"]
with open(OUT / "inventory.csv", "w", newline="", encoding="utf-8-sig") as f:
    wr = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    wr.writeheader()
    wr.writerows(rows)

from collections import Counter
print("Total:", len(rows))
for k, v in Counter(r["kind"] for r in rows).items():
    print(f"  {k}: {v}")
mi = [r for r in rows if r["kind"] == "menu_item"]
print("menu_item com '...':", sum(r["opens_dialog_hint"] for r in mi),
      "| desativados:", sum(r["enabled"] is False for r in mi),
      "| sem caption:", sum(not r["caption"] for r in mi))
