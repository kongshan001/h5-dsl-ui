# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

H5 DSL UI 系统 — 声明式 DSL，将 HTML/CSS UI 开发与自研游戏引擎 Python UI 库桥接。目标：利用 AI 擅长 Web UI 开发的优势，将 H5 产出低成本适配为引擎原生 UI。

三层架构：
1. **设计层** — HTML/CSS（AI 生产力最大化）
2. **中间层** — JSON DSL 描述控件树、样式、事件
3. **运行层** — `DSLPage` 加载器调用引擎 UI API 构建界面

## 常用命令

```bash
# 运行全部测试
python3 -m pytest tests/ -v

# 运行单个测试文件
python3 -m pytest tests/test_loader.py -v

# 按名称运行单个测试
python3 -m pytest tests/test_loader.py::test_event_dispatch -v

# 按关键字匹配测试
python3 -m pytest tests/ -k "converter" -v

# 安装依赖
pip3 install -r requirements.txt

# 运行 demo（7 个页面）
python3 demo/run.py inventory    # 背包
python3 demo/run.py settings     # 设置
python3 demo/run.py arena        # 对局结果
python3 demo/run.py casual       # 休闲菜单
python3 demo/run.py rpg          # RPG 角色
python3 demo/run.py scifi        # 科幻主题
python3 demo/run.py shop         # 商店

# 重新生成 DSL JSON
python3 demo/convert.py

# 重新生成 PyQt5 截图
python3 demo/capture_screenshots.py

# 生成视觉对比报告
python3 demo/visual_report.py

# 运行视觉回归测试
python3 -m pytest tests/test_visual.py -v

# 截图对比
# HTML 原图: demo/html_screenshots/
# PyQt5 渲染: demo/screenshots_pyqt5/
```

## 架构

数据流：`HTML 字符串 → html_to_dsl.py（配合 css_mapper.py）→ DSL JSON → schema.py 校验 → loader.py（DSLPage）→ backends/pyqt5.py 创建控件`

**核心模块：**
- `dsl/schema.py` — `validate_node()` / `validate_dsl()` 在加载前校验 DSL 结构
- `dsl/loader.py` — `DSLPage` 是主类。`load(path)` 解析 JSON、校验、通过后端递归构建控件树。`on(event, callback)` 注册事件回调。`get(id)` 按 id 查找控件做动态更新
- `dsl/backends/base.py` — `UIBackend` 抽象基类，抽象方法：`create`、`apply_style`、`create_layout`、`add_child`、`bind_event`、`add_child_with_stretch`。对接引擎时只需实现此接口
- `dsl/backends/pyqt5.py` — PyQt5 验证后端。`GradientLabel` 子类用 QPainter 实现渐变文字（CSS `background-clip:text` 等价）
- `dsl/converter/html_to_dsl.py` — `convert_html(html, mappings)` 返回 DSL 节点树。使用 BeautifulSoup 解析 HTML
- `dsl/converter/css_mapper.py` — `map_css_to_style(css_props)` 将 CSS 键值对翻译为 DSL 样式字典

## PyQt5 渲染关键细节

这些是调试 PyQt5 高保真渲染时积累的经验，修改后端代码时必须注意：

- **必须用 Fusion 样式** — `loader.py` 中 `app.setStyle('Fusion')`。macOS 默认 `macintosh` 样式会忽略 QPushButton/QWidget 的 QSS（渐变、背景色、边框全部不渲染）
- **QLabel 最小高度** — QLabel 在 QBoxLayout 中没有明确 height 时会被压缩到 0px，文字完全不可见。`apply_style` 中对 is_label 且无 height 的控件设 `setMinimumHeight(fontMetrics().height() + 2)`
- **WA_StyledBackground** — QWidget 必须设 `setAttribute(Qt.WA_StyledBackground, True)` 才能渲染 QSS 背景和边框
- **子组件透明** — 没有 bgColor/gradient 的子组件必须加 `background-color: transparent;` + `setAutoFillBackground(False)`，否则子组件会用调色板背景色覆盖父级渐变
- **渐变文字 vs 渐变背景** — CSS `background-clip:text` + `-webkit-text-fill-color:transparent` 转为 DSL `gradientText`（GradientLabel 自定义绘制），普通 CSS `background: linear-gradient(...)` 转为 DSL `gradient`（QSS 背景）

## CSS 选择器支持

`html_to_dsl.py` 的 `_compute_style()` 使用特异性排序的级联引擎：
- 类选择器 `.class`、标签选择器 `tag`、标签+类 `tag.class`
- 多类选择器 `.class1.class2`（tag 必须同时匹配所有 class）
- 后代选择器 `.parent .child`（沿祖先链匹配）
- 通用选择器 `*`（特异性最低）
- 内联 `style=""` 属性优先级最高

## CSS → DSL 映射要点

`css_mapper.py` 支持的 CSS 特性（不在这列表里的 CSS 属性会被忽略）：

- 布局：`display:flex/grid`、`flex-direction`、`justify-content`、`align-items`、`flex`、`gap`
- 盒模型：`width`、`height`、`min-width`/`max-width`、`min-height`/`max-height`、`padding`、`border-radius`、`border`/`border-bottom`/`border-top`/`border-left`/`border-right`、`box-sizing`
- 文字：`color`、`font-size`、`font-weight`、`font-family`、`letter-spacing`、`line-height`、`text-align`
- 背景：`background-color`、`background`（linear-gradient 解析）、`-webkit-background-clip`、`-webkit-text-fill-color`
- 效果：`box-shadow`（通过 QGraphicsDropShadowEffect 实现）、`opacity`
- 百分比宽度：CSS `width: 78%` → DSL `widthPercent: 78`（用于进度条，PyQt5 中用 stretch 因子实现）

**仍不支持的关键 CSS 特性**：`position:absolute`、`transform`、`transition`、伪类（`:hover`）、后代选择器中的子选择器（`>`）、`overflow`

## 事件系统

事件在 DSL 中声明（`"events": {"click": "on_slot_click"}`），在 Python 中注册（`page.on("on_slot_click", handler)`）。`_dispatch` 通过 `inspect.signature` 自动检测回调是否接收 `widget_id` 参数。

## 布局系统

- **Flex 布局**：`layout: "vertical"/"horizontal"`，`justifyContent`（center/space-between/space-around 用 stretch 实现），`alignItems`（center/start/end 通过 `addWidget(widget, stretch, alignment)` 实现）
- **Grid 布局**：通过 style 中 `layout: "grid"` 检测（不限 GridView 类型），`columns` 指定列数，`divmod(idx, columns)` 放置
- **百分比宽度**：`widthPercent` 通过 `add_child_with_stretch(layout, child, fill, empty)` 实现
- **flex: 1**：通过 stretch 因子让控件填满剩余空间
- **自动布局**：有 children 但没有显式 layout 的容器，自动创建 vertical layout

## 设计文档

- 设计规格：`docs/superpowers/specs/2026-04-19-h5-dsl-ui-design.md`
- 实施计划：`docs/superpowers/plans/2026-04-19-h5-dsl-ui-implementation.md`（全部已完成）

## 约定

- Python 3.9+，不强要求类型注解，保持函数签名清晰
- DSL JSON 样式键使用 camelCase（`bgColor`、`fontSize`、`cornerRadius`），与 CSS 命名习惯一致
- 测试使用 `tmp_path` fixture 创建临时 DSL 文件，使用 `scope="module"` 的 QApplication fixture
- 7 个 demo 页面在 `demo/html/`（HTML 源文件）和 `demo/pages/`（DSL JSON）
