---
name: H5 DSL UI System
description: Declarative DSL intermediate layer for bridging H5 UI development with custom game engine Python UI library
type: project
---

# H5 DSL UI System — Design Spec

**背景：** 自研游戏引擎（C++ + Python API），引擎提供基础 UI 控件，Python 层二次封装为 UI 库。目标利用 AI 在 Web UI 开发上的优势，通过 H5 设计 UI，低成本适配到引擎 Python UI 库。

## 核心架构

```
AI / 开发者 → HTML + CSS → [HTML→DSL 转换器] → DSL JSON → [DSL Loader] → 引擎 Python UI 库
```

三层分离：
1. **设计层（H5）**：用 HTML/CSS 开发 UI 视觉，AI 生产力最大化
2. **中间层（DSL）**：JSON 格式描述控件树、样式、事件绑定
3. **运行层（Loader）**：Python 加载 DSL，调用引擎 UI 库 API 构建界面，业务逻辑纯 Python

## DSL Schema

### 顶层结构

```json
{
  "version": 1,
  "name": "page_name",
  "root": { /* 控件节点 */ }
}
```

### 控件节点

```json
{
  "type": "string",          // 控件类型名
  "id": "string?",           // 可选，用于 get() 查找和事件关联
  "props": {},               // 控件属性（构造参数）
  "style": {},               // 样式属性
  "events": {},              // 事件绑定 { event_type: event_name }
  "children": []             // 子控件列表
}
```

### 标准控件映射

| DSL type | 说明 | props | 核心样式 |
|----------|------|-------|----------|
| `Panel` | 容器 | width, height | bgColor, padding, layout, gap, align, cornerRadius |
| `Text` | 文本 | value | fontSize, color, bold, align |
| `Button` | 按钮 | text | width, height, bgColor, color, fontSize, cornerRadius |
| `Image` | 图片 | src | width, height |
| `Input` | 输入框 | placeholder, value | width, height, bgColor, color, fontSize |
| `Slider` | 滑动条 | min, max, value | width, height |
| `ScrollView` | 滚动容器 | direction(vertical/horizontal) | width, height |
| `ListView` | 列表 | - | gap, layout |
| `GridView` | 网格 | columns, rows | gap |
| 自定义类型 | 透传到 `create_custom()` | 由控件定义 | 由控件定义 |

### 样式属性

| 属性 | 类型 | 说明 |
|------|------|------|
| width/height | int | 固定尺寸 |
| bgColor | string (#RRGGBB / #RRGGBBAA) | 背景色 |
| color | string | 文字颜色 |
| fontSize | int | 字号（像素） |
| bold | bool | 粗体 |
| padding | int | 内边距 |
| margin | int | 外边距 |
| gap | int | 子控件间距 |
| layout | "vertical" / "horizontal" / "grid" / "absolute" | 布局模式 |
| align | "left" / "center" / "right" | 对齐方式 |
| cornerRadius | int | 圆角 |
| opacity | float 0-1 | 不透明度 |

### 事件绑定

DSL 声明 → Python 注册回调：

```json
// DSL 侧
{ "events": { "click": "on_item_click" } }

# Python 侧
page.on("on_item_click", lambda widget_id: player.use_item(widget_id))
```

Loader 的 `_dispatch` 通过 inspect 自动判断回调是否接收 `widget_id` 参数。

## HTML → DSL 转换器

### 元素映射

| HTML | DSL type |
|------|----------|
| `<div>` | Panel |
| `<button>` | Button |
| `<span>`, `<p>`, `<h1>`~`<h6>` | Text |
| `<img>` | Image |
| `<ul>`, `<ol>` | ListView |
| `<input type="text">` | Input |
| `<input type="range">` | Slider |
| `<input type="checkbox">` | Toggle |
| 自定义标签 `<x-*>` | 透传标签名（去掉 x- 前缀） |

### CSS 属性映射（支持的子集）

| CSS | DSL style |
|-----|-----------|
| width/height | width/height |
| min-width/max-width | minWidth/maxWidth |
| min-height/max-height | minHeight/maxHeight |
| width: N% | widthPercent: N |
| background-color | bgColor |
| background: linear-gradient(...) | gradient |
| -webkit-background-clip: text | gradientText |
| -webkit-text-fill-color: transparent | (配合 gradientText) |
| color | color |
| font-size | fontSize |
| font-weight: bold | bold: true |
| font-family | fontFamily |
| letter-spacing | letterSpacing |
| line-height | lineHeight |
| text-align | textAlign |
| padding | padding |
| margin | margin |
| gap | gap |
| display: flex + flex-direction | layout |
| display: grid + grid-template-columns | layout + columns |
| justify-content | justifyContent (center/space-between/space-around) |
| align-items | alignItems (center/start/end) |
| flex: N | flex: N |
| opacity | opacity |
| border-radius | cornerRadius |
| border | border (width/style/color) |
| border-bottom/top/left/right | borderBottom/Top/Left/Right |
| box-shadow | boxShadow (offsetX/offsetY/blurRadius/color) |
| box-sizing | boxSizing |

### CSS 选择器支持

`html_to_dsl.py` 使用特异性排序的级联引擎：
- 类选择器 `.class`、标签选择器 `tag`、标签+类 `tag.class`
- 多类选择器 `.class1.class2`
- 后代选择器 `.parent .child`
- 通用选择器 `*`
- 内联 `style=""` 优先级最高

### 渲染一致性特性（PyQt5 后端）

| 特性 | 实现方式 |
|------|----------|
| 渐变文字 (background-clip:text) | GradientLabel 自定义 QPainter |
| 渐变背景 + 圆角 | GradientLabel set_bg_gradient_clipped |
| 半透明背景 bgColor | StyledPanel/StyledButton 自定义 QPainter alpha compositing |
| 半透明文字颜色 | GradientLabel set_alpha_text_color + QPainter |
| CSS 渐变方向计算 | _css_gradient_endpoints() 匹配 CSS linear-gradient 规范 |
| 8位hex颜色 (#RRGGBBAA) | 自动转换为 rgba() 修正 QSS 字节序 |
| 视觉对比测试 | pixel-level diff, 94.7% 平均相似度 |

### 自定义控件映射配置

转换器需要一个映射配置文件，告诉它哪些 CSS class 或自定义标签对应引擎的自定义控件：

```json
{
  "custom_mappings": {
    "x-itemslot": "ItemSlot",
    "x-skillbar": "SkillBar",
    ".item-slot": "ItemSlot",
    ".skill-icon": "SkillIcon"
  }
}
```

## DSL Loader

### API

```python
class DSLPage:
    def load(dsl_path) -> DSLPage       # 加载 DSL 文件
    def on(event_name, callback) -> DSLPage  # 注册事件回调
    def get(widget_id) -> widget        # 按 id 查找控件
    def unload()                        # 销毁页面
    def show()                          # 显示（demo 用）
```

### 加载流程

1. 解析 JSON
2. 递归 `_build(node)`：
   - `_create(type, props)` → 创建控件实例
   - `_apply_style(widget, style)` → 应用样式
   - `_create_layout(style)` → 创建布局管理器
   - 递归处理 children
   - `_bind_event(widget, event_type, event_name)` → 绑定事件
3. 注册所有带 id 的控件到 `_widgets` 字典

### 后端适配

Loader 通过抽象后端接口支持不同 UI 框架：

```python
class UIBackend(ABC):
    def create(self, type_name, props) -> Widget
    def apply_style(self, widget, style)
    def create_layout(self, style) -> Layout
    def add_child(self, parent, child)
    def bind_event(self, widget, event_type, handler)
```

- PyQt5 后端：验证用 demo
- 引擎后端：替换为 `engine.ui` API 调用

## 项目结构

```
h5-ui-for-game/
├── dsl/
│   ├── schema.py              # DSL JSON schema 定义与校验
│   ├── loader.py              # DSLPage 加载器核心
│   ├── backends/
│   │   ├── base.py            # UIBackend 抽象基类
│   │   └── pyqt5.py           # PyQt5 后端（含 StyledPanel/StyledButton/GradientLabel）
│   ├── converter/
│   │   ├── html_to_dsl.py     # HTML → DSL 转换器（含 CSS 选择器级联引擎）
│   │   └── css_mapper.py      # CSS 属性映射表
│   └── mappings.json          # 自定义控件映射配置
├── demo/
│   ├── html/                  # HTML/CSS 游戏UI源文件（7个页面）
│   ├── pages/                 # DSL JSON 页面文件（7个）
│   ├── html_screenshots/      # HTML 浏览器截图
│   ├── screenshots_pyqt5/     # PyQt5 渲染截图
│   ├── capture_screenshots.py # 批量截图工具
│   ├── visual_report.py       # 视觉对比报告生成
│   ├── convert.py             # HTML → DSL JSON 批量转换
│   └── run.py                 # Demo 入口
├── tests/
│   ├── test_schema.py
│   ├── test_loader.py
│   ├── test_backends.py
│   ├── test_converter.py
│   ├── test_css_mapper.py
│   ├── test_e2e.py
│   ├── test_visual.py         # 视觉回归测试（7页 x 85%阈值）
│   └── screenshot_utils.py    # 截图+对比工具
├── docs/
│   └── superpowers/
│       ├── specs/             # 设计规格
│       └── plans/             # 实施计划
├── CHANGELOG.md               # 版本变更记录
└── CLAUDE.md                  # 项目说明与架构文档
```
