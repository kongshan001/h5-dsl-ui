"""
Demo: 验证 DSL 方案可行性
模拟游戏业务层加载 DSL 并绑定交互逻辑
"""
import sys
from dsl_loader import DSLPage


def main():
    # === 模拟游戏数据 ===
    items = {
        "slot_0": {"name": "木剑", "desc": "普通木剑，攻击+5", "count": 1},
        "slot_1": {"name": "药水", "desc": "恢复50HP", "count": 3},
    }

    # === 加载 DSL 页面 ===
    page = DSLPage().load("inventory.json")

    # === 绑定业务逻辑 ===
    def on_slot_click(widget_id):
        if widget_id not in items:
            return
        item = items[widget_id]

        # 动态更新详情面板
        detail = page.get("detail_text")
        if detail:
            detail.setText(f"【{item['name']}】{item['desc']}  x{item['count']}")

        # 动态更新标题
        title = page.get("title")
        if title:
            title.setText(f"背包 — 已选中: {item['name']}")

    def on_close():
        print("关闭背包")
        page.unload()
        sys.exit(0)

    page.on("on_slot_click", on_slot_click)
    page.on("on_close", on_close)

    # === 显示页面 ===
    page.show()


if __name__ == "__main__":
    main()
