# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

H5 DSL UI System — a declarative DSL that bridges HTML/CSS UI development with a custom game engine's Python UI library. The goal: use AI's strength in web UI development, then convert H5 output to engine-native UI at low cost.

Three-layer architecture:
1. **Design Layer** — HTML/CSS (AI productivity)
2. **Intermediate Layer** — JSON DSL describing widget tree, styles, events
3. **Runtime Layer** — `DSLPage` loader calls engine UI API to build interface

## Commands

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_loader.py -v

# Run a single test by name
python3 -m pytest tests/test_loader.py::test_event_dispatch -v

# Run tests matching keyword
python3 -m pytest tests/ -k "converter" -v

# Install dependencies
pip3 install -r requirements.txt

# Run demo
python3 demo/run.py inventory
python3 demo/run.py settings
```

## Architecture

Data flow: `HTML string → html_to_dsl.py (with css_mapper.py) → DSL JSON → schema.py validates → loader.py (DSLPage) → backends/pyqt5.py creates widgets`

**Key modules:**
- `dsl/schema.py` — `validate_node()` / `validate_dsl()` validate DSL structure before loading
- `dsl/loader.py` — `DSLPage` is the main class. `load(path)` parses JSON, validates, recursively builds widget tree via backend. `on(event, callback)` registers handlers. `get(id)` retrieves widgets for dynamic updates
- `dsl/backends/base.py` — `UIBackend` ABC with 5 abstract methods: `create`, `apply_style`, `create_layout`, `add_child`, `bind_event`. To adapt to the game engine, implement this interface calling engine Python UI API
- `dsl/backends/pyqt5.py` — PyQt5 demo backend. Also has `add_grid_child()` for GridView cell placement
- `dsl/converter/html_to_dsl.py` — `convert_html(html, mappings)` returns DSL node tree. `convert_html_to_dsl_file()` writes to disk. Uses BeautifulSoup for HTML parsing
- `dsl/converter/css_mapper.py` — `map_css_to_style(css_props)` translates CSS key-value pairs to DSL style dict. Only supports a defined subset of CSS

**Event system:** Events declared in DSL (`"events": {"click": "on_slot_click"}`), registered in Python (`page.on("on_slot_click", handler)`). `_dispatch` uses `inspect.signature` to auto-detect whether callback accepts `widget_id` parameter.

**GridView layout:** Children placed by `divmod(idx, columns)` into grid cells, handled specially in loader's `_build()`.

**Custom widgets:** Unknown `type` values fall through to `backend.create()` as generic widgets. Converter maps `<x-*>` tags and custom CSS classes via the `mappings` dict.

## Design Docs

- Spec: `docs/superpowers/specs/2026-04-19-h5-dsl-ui-design.md` — full DSL schema, widget mappings, event system
- Plan: `docs/superpowers/plans/2026-04-19-h5-dsl-ui-implementation.md` — implementation tasks (all completed)

## Conventions

- Python 3.9+, no type hints required but keep signatures clear
- DSL JSON uses camelCase for style keys (`bgColor`, `fontSize`, `cornerRadius`) matching CSS conventions
- Tests use `tmp_path` fixture for temporary DSL files and `scope="module"` QApplication fixture
- TDD: write test first, verify red, implement, verify green
