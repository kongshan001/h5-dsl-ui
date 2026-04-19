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

# 运行 demo
python3 demo/run.py inventory
python3 demo/run.py settings
```

## 架构

数据流：`HTML 字符串 → html_to_dsl.py（配合 css_mapper.py）→ DSL JSON → schema.py 校验 → loader.py（DSLPage）→ backends/pyqt5.py 创建控件`

**核心模块：**
- `dsl/schema.py` — `validate_node()` / `validate_dsl()` 在加载前校验 DSL 结构
- `dsl/loader.py` — `DSLPage` 是主类。`load(path)` 解析 JSON、校验、通过后端递归构建控件树。`on(event, callback)` 注册事件回调。`get(id)` 按 id 查找控件做动态更新
- `dsl/backends/base.py` — `UIBackend` 抽象基类，5 个抽象方法：`create`、`apply_style`、`create_layout`、`add_child`、`bind_event`。对接引擎时只需实现此接口，调用引擎 Python UI API
- `dsl/backends/pyqt5.py` — PyQt5 验证后端。额外提供 `add_grid_child()` 用于 GridView 单元格放置
- `dsl/converter/html_to_dsl.py` — `convert_html(html, mappings)` 返回 DSL 节点树。`convert_html_to_dsl_file()` 写入磁盘。使用 BeautifulSoup 解析 HTML
- `dsl/converter/css_mapper.py` — `map_css_to_style(css_props)` 将 CSS 键值对翻译为 DSL 样式字典。仅支持定义好的 CSS 子集

**事件系统：** 事件在 DSL 中声明（`"events": {"click": "on_slot_click"}`），在 Python 中注册（`page.on("on_slot_click", handler)`）。`_dispatch` 通过 `inspect.signature` 自动检测回调是否接收 `widget_id` 参数。

**GridView 布局：** 子控件通过 `divmod(idx, columns)` 放入网格单元格，在 loader 的 `_build()` 中特殊处理。

**自定义控件：** 未知 `type` 值会透传到 `backend.create()` 作为通用控件。转换器通过 `mappings` 字典映射 `<x-*>` 标签和自定义 CSS 类。

## 设计文档

- 设计规格：`docs/superpowers/specs/2026-04-19-h5-dsl-ui-design.md` — 完整 DSL schema、控件映射、事件系统
- 实施计划：`docs/superpowers/plans/2026-04-19-h5-dsl-ui-implementation.md` — 逐步实现任务（全部已完成）

## 约定

- Python 3.9+，不强要求类型注解，保持函数签名清晰
- DSL JSON 样式键使用 camelCase（`bgColor`、`fontSize`、`cornerRadius`），与 CSS 命名习惯一致
- 测试使用 `tmp_path` fixture 创建临时 DSL 文件，使用 `scope="module"` 的 QApplication fixture
- TDD：先写测试，验证红灯，实现，验证绿灯
