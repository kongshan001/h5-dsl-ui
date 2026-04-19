# demo/run.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dsl.loader import DSLPage

PAGES_DIR = os.path.join(os.path.dirname(__file__), "pages")


def inventory_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "inventory.json"))

    items = {
        "slot_0": {"name": "木剑", "desc": "普通木剑，攻击+5", "count": 1},
        "slot_1": {"name": "药水", "desc": "恢复50HP", "count": 3},
    }

    def on_slot_click(widget_id):
        if widget_id not in items:
            return
        item = items[widget_id]
        detail = page.get("detail_text")
        if detail:
            detail.setText(f"【{item['name']}】{item['desc']}  x{item['count']}")
        title = page.get("title")
        if title:
            title.setText(f"背包 — 已选中: {item['name']}")

    def on_close():
        page.unload()
        sys.exit(0)

    page.on("on_slot_click", on_slot_click)
    page.on("on_close", on_close)
    page.show()


def settings_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "settings.json"))

    def on_save():
        name = page.get("name_input").text()
        volume = page.get("volume_slider").value()
        print(f"Saved: name={name}, volume={volume}")

    page.on("on_save", on_save)
    page.show()


if __name__ == "__main__":
    demo = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    if demo == "settings":
        settings_demo()
    else:
        inventory_demo()
