# win-screen-mapper

A [Claude Code](https://claude.com/claude-code) skill that maps an entire Windows desktop application
into an organized screenshot atlas: every menu and submenu, every dialog with its tabs, pages and
dropdowns, panels, toolboxes, toolbars and right-click menus, across selection contexts. It ends with a
coverage report (what has a screenshot, and why anything is missing) and an offline, searchable
`index.html`.

It was built for teams that produce training material or documentation and need *every* screen of an
app, not a tutorial. The method was first used to map CorelDRAW 2026 (2,844 screenshots in 7 stages).
The kit itself is app-agnostic.

> The skill's instructions and references are written in **Portuguese**. Claude reads them fine and
> talks to you in your own language.

## What it does

| stage | output |
|---|---|
| 0. Discovery | asks what to map, where to save it and what is off limits; picks an automation route |
| 1. Inventory | master list of every menu item (`inventory.json` / `.csv`) |
| 2. Menus | every menu and submenu, opened by hover only |
| 3. Dialogs | every command that opens a window: opened, captured, closed with Cancel |
| 4. Inside dialogs | tabs, tree pages, dropdowns, child windows; vision pass for custom-drawn controls |
| 5. Contexts | the same screens again with different selections (empty document, text, image…) |
| 6. Panels and bars | panels, toolboxes, property bars, hidden toolbars, right-click menus |
| 7. Coverage and index | `cobertura_final.csv`, `resumo_final.json` and an offline `index.html` |

The skill moves one stage at a time and asks for your go-ahead before the next.

### Automation routes

| route | when |
|---|---|
| `uia` | Windows UI Automation can see the menu bar (standard Win32, WPF, WinForms, most Qt apps) |
| `win32` | the app uses a native Windows menu (commands are opened by `WM_COMMAND`) |
| `adaptador` | the app has its own automation (COM, scripting, SDK), wired through a small adapter module |
| `visao` | nothing else works: targets are marked on ruler sheets and clicked by coordinate |

Everything that varies per app goes into one `app.json` file, plus an optional adapter. The scripts in
`kit/` stay unchanged.

### Safety rules built in

- Never clicks OK, Apply, Save, Delete, Reset, Export, Print, Publish, Send, Buy, "I agree", sign-in
  or update controls, or links that open a browser.
- Windows are closed with Cancel or X; app-drawn menus with Esc. An unexpected question ("Save
  changes?") is answered with Cancel and the run stops.
- Crash reports are never sent.
- Only captures inside the app's own window. File pickers have their folder and file areas redacted.
- Works in a throwaway document and restores every option it changes.

## Install

### As a Claude Code plugin

```
/plugin marketplace add toim22/win-screen-mapper
/plugin install win-screen-mapper@win-screen-mapper
```

### As a personal skill

Copy `skills/win-screen-mapper` into `%USERPROFILE%\.claude\skills\`.

## Requirements

- Windows 10 or 11.
- Python 3 with `pywin32`, `Pillow` and `pywinauto`. `pywinauto` only runs in helper subprocesses,
  because mixing it with COM in one process crashed Python.
- The app to map, open on the same PC. The crawlers move the mouse, so don't use the PC during a run.

## Usage

Ask Claude Code something like *"map every screen and menu of <app> for our training team"*, or run
`/win-screen-mapper`. Claude will:
- ask the setup questions;
- copy the kit into a project folder and fill in `app.json`;
- work through the stages, showing you the results of each one.

## Layout

```
skills/win-screen-mapper/
├─ SKILL.md            workflow, routes and non-negotiable rules
├─ referencias/        safety rules, app discovery, techniques, output format, CorelDRAW case study
├─ modelos/            setup questions, README template for the screenshot atlas, original plan
├─ kit/                generic Python scripts (inventory, crawlers, vision engine, report, HTML index)
└─ exemplos/corel/     the original CorelDRAW 2026 scripts, kept as a reference implementation
```

## Status

- The generic kit was derived from the CorelDRAW scripts and checked against that project's data:
  - menu-row detection from images matched 60 of 73 CorelDRAW menus;
  - the coverage report reproduced the original numbers.
- The generic crawlers have not yet run against a second application.
- Validate each one with a short run (`--only` with one menu) on your first app, and please open an
  issue with what you find.

## License

[MIT](LICENSE)
