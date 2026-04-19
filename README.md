# H5 DSL UI System

利用 AI 在 Web UI 开发上的优势，通过 H5 (HTML/CSS) 设计游戏 UI，低成本适配到自研引擎的 Python UI 库。

## 工作原理

```
AI 生成 HTML/CSS → [HTML→DSL 转换器] → DSL JSON → [DSL Loader] → 引擎 Python UI 库
```

三层分离：
- **设计层**：HTML/CSS 开发 UI 视觉，AI 生产力最大化
- **中间层**：JSON DSL 描述控件树、样式、事件绑定
- **运行层**：Python 加载 DSL，调用引擎 UI 库 API 构建界面

## 快速开始

```bash
# 安装依赖
pip3 install -r requirements.txt

# 运行 demo
python3 demo/run.py inventory    # 背包页面
python3 demo/run.py settings     # 设置页面

# 运行测试
python3 -m pytest tests/ -v
```

## 使用示例

### 1. 用 HTML/CSS 设计 UI（AI 辅助）

```html
<div style="display:flex; flex-direction:column; padding:16px; background-color:#1a1a2e;">
  <h1 style="color:white; font-size:24px;">商店</h1>
  <button style="background-color:#238636; color:white; width:120px; height:40px;">
    购买药水
  </button>
</div>
```

### 2. 转换为 DSL

```python
from dsl.converter.html_to_dsl import convert_html_to_dsl_file

html = open("my_ui.html").read()
convert_html_to_dsl_file(html, "ui/shop.json", page_name="shop")
```

输出 DSL JSON：
```json
{
  "version": 1,
  "name": "shop",
  "root": {
    "type": "Panel",
    "style": { "layout": "vertical", "bgColor": "#1a1a2e", "padding": 16 },
    "children": [
      { "type": "Text", "props": { "value": "商店" }, "style": { "color": "#ffffff", "fontSize": 24 } },
      { "type": "Button", "props": { "text": "购买药水" }, "style": { "bgColor": "#238636", "color": "#ffffff", "width": 120, "height": 40 } }
    ]
  }
}
```

### 3. 在引擎中加载并绑定逻辑

```python
from dsl.loader import DSLPage

page = DSLPage().load("ui/shop.json")

# 注册事件回调（纯 Python 业务逻辑）
page.on("on_buy", lambda widget_id: player.buy_item(widget_id))

# 动态更新控件
page.get("title").set_style("value", f"金币: {player.gold}")

page.show()
```

## 项目结构

```
dsl/
├── schema.py              # DSL JSON 校验
├── loader.py              # DSLPage 加载器核心
├── backends/
│   ├── base.py            # UIBackend 抽象基类（对接引擎时实现此接口）
│   └── pyqt5.py           # PyQt5 后端（demo 验证用）
├── converter/
│   ├── html_to_dsl.py     # HTML → DSL 转换器
│   └── css_mapper.py      # CSS 属性映射
└── mappings.json          # 自定义控件映射配置

demo/
├── pages/                 # DSL JSON 页面文件
│   ├── inventory.json
│   └── settings.json
└── run.py                 # Demo 入口

tests/                     # 35 个测试
```

## 对接到你的引擎

只需实现 `UIBackend` 接口（[dsl/backends/base.py](dsl/backends/base.py)），将 PyQt5 调用替换为引擎的 Python UI 库 API：

```python
from dsl.backends.base import UIBackend

class EngineBackend(UIBackend):
    def create(self, type_name, props):
        return engine.ui.create(type_name, **props)

    def apply_style(self, widget, style):
        for key, value in style.items():
            widget.set_style(key, value)

    # ... 实现 create_layout, add_child, bind_event
```

然后加载时传入自定义后端：
```python
page = DSLPage(backend=EngineBackend()).load("ui/shop.json")
```

## DSL 控件类型

| DSL type | HTML 来源 | 说明 |
|----------|-----------|------|
| `Panel` | `<div>` | 容器 |
| `Text` | `<p>`, `<span>`, `<h1>`~`<h6>` | 文本 |
| `Button` | `<button>` | 按钮 |
| `Image` | `<img>` | 图片 |
| `Input` | `<input type="text">` | 输入框 |
| `Slider` | `<input type="range">` | 滑动条 |
| `GridView` | `display:grid` | 网格布局 |
| `ListView` | `<ul>`, `<ol>` | 列表 |
| 自定义 | `<x-*>` 或映射配置 | 透传到 `create_custom()` |

## 支持的 CSS 子集

`background-color`, `color`, `font-size`, `font-weight`, `width`, `height`, `padding`, `margin`, `gap`, `border-radius`, `opacity`, `display:flex/grid`

## License

MIT
