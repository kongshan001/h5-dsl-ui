# Changelog

## [0.5.0] - 2026-04-22

### Phase 12: Alpha Compositing & Text Color Fix
- **StyledPanel/StyledButton**: New widget classes with custom `paintEvent` for semi-transparent backgrounds via QPainter alpha compositing. QSS `rgba()` backgrounds don't composite with parent gradient — this provides a partial fix.
- **8-digit hex text color**: Fixed QSS `color: #ffffffb2` being parsed as Qt `#AARRGGBB` (wrong byte order) instead of CSS `#RRGGBBAA`. Now converts to `rgba()` and uses custom QPainter text drawing in `GradientLabel` for actual alpha compositing.
- **GradientLabel alpha text**: Added `_alpha_text_color` attribute with custom QPainter rendering. QSS `color: rgba()` ignores alpha for QLabel text — custom painting fixes this.
- **Similarity**: Average 94.7% (no change from Phase 11 due to Qt rendering ceiling).

### Phase 11: Gradient Calculation & Border Color Fix (2026-04-21)
- **CSS gradient endpoints**: `_css_gradient_endpoints()` computes start/end matching CSS `linear-gradient` spec (gradient line through center, half-length = w/2*|sin| + h/2*|cos|).
- **8-digit hex border colors**: Qt QSS parses `#rrggbbaa` as 3-channel RGB. Now converts to `rgba()` format. Fixed arena_result yellow pixel artifacts.
- **widthPercent auto-layout**: Containers with `widthPercent` children auto-create horizontal layout instead of vertical.
- **Similarity**: 94.4% → 94.7% (+0.3%). arena_result +1.5%, rpg_status +0.6%.

## [0.4.0] - 2026-04-21

### Phase 5: Automated Visual Testing
- `tests/test_visual.py`: Parametrized pytest across 7 pages with similarity threshold (85%).
- `tests/screenshot_utils.py`: `capture_pyqt5_screenshot()` + `compare_screenshots()` with pixel diff.
- `demo/capture_screenshots.py`: Batch regenerate all PyQt5 screenshots.
- `demo/visual_report.py`: HTML diff report with side-by-side images + similarity scores.
- Added `Pillow>=10.0` to requirements.txt.

### Phase 4: Layout Precision
- `space-around` fix: stretch factors `1, 2, 2, ..., 2, 1` instead of uniform.
- `textAlign` inheritance from parent to children.
- `min-width`/`max-width`/`min-height`/`max-height` support in css_mapper + pyqt5 backend.
- `add_stretch(layout, factor)` parameter.

### Phase 3: Missing CSS Features
- `font-family` → `fontFamily` → `font.setFamily()`.
- `line-height` → `lineHeight` → vertical padding adjustment on labels.
- `box-shadow` → `QGraphicsDropShadowEffect` in backend.
- `box-sizing: border-box` support.

### Phase 2: Converter Text Processing
- Button with children: `props.text = ""` instead of concatenated text.
- `letterSpacing` pixel-value parsing in css_mapper.

### Phase 1: CSS Selector Resolution Engine
- `_compute_specificity()`: Returns `(ids, classes, tags)` tuple.
- `_matches_selector()`: Handles `.class`, `tag.class`, `.c1.c2`, `.parent .child`, `*`.
- `_compute_style()`: Iterate ALL rules, match each, sort by specificity, merge. Inline style wins.
- **Similarity after Phase 5**: Average ~94.4%.

## [0.3.0] - 2026-04-19

### Added
- Gradient support: `linear-gradient` CSS parsing → DSL gradient → QSS gradient + GradientLabel custom QPainter for `background-clip:text`.
- Pure text `<div>` auto-maps to Text type instead of Panel.

## [0.2.0] - 2026-04-19

### Added
- 4 new game-style HTML pages: arena_result, casual_menu, rpg_status, scifi_hub.
- CSS class selector parsing enhancement.

## [0.1.0] - 2026-04-19

### Added
- Initial project structure: HTML/CSS → JSON DSL → PyQt5 widgets three-layer architecture.
- Core modules: `schema.py`, `loader.py`, `backends/base.py`, `backends/pyqt5.py`, `converter/html_to_dsl.py`, `converter/css_mapper.py`.
- 3 demo pages: inventory, settings, shop.
- Design spec: `docs/superpowers/specs/2026-04-19-h5-dsl-ui-design.md`.
- Implementation plan: `docs/superpowers/plans/2026-04-19-h5-dsl-ui-implementation.md`.
