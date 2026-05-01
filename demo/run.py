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


def shop_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "shop.json"))

    shop_items = {
        "item_0": {"name": "生命药水", "price": 50},
        "item_1": {"name": "魔法卷轴", "price": 80},
        "item_2": {"name": "火焰剑", "price": 200},
        "item_3": {"name": "护身符", "price": 150},
        "item_4": {"name": "经验丹", "price": 120},
    }

    def on_close():
        page.unload()
        sys.exit(0)

    page.on("on_close", on_close)
    page.show()


def rpg_status_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "rpg_status.json"))
    page.show()


def scifi_hub_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "scifi_hub.json"))
    page.show()


def casual_menu_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "casual_menu.json"))
    page.show()


def arena_result_demo():
    page = DSLPage().load(os.path.join(PAGES_DIR, "arena_result.json"))
    page.show()


DEMOS = {
    "inventory": inventory_demo,
    "settings": settings_demo,
    "shop": shop_demo,
    "rpg": rpg_status_demo,
    "scifi": scifi_hub_demo,
    "casual": casual_menu_demo,
    "arena": arena_result_demo,
    "dungeon": lambda: DSLPage().load(os.path.join(PAGES_DIR, "dungeon.json")).show(),
    "guild": lambda: DSLPage().load(os.path.join(PAGES_DIR, "guild.json")).show(),
    "gacha": lambda: DSLPage().load(os.path.join(PAGES_DIR, "gacha.json")).show(),
    "battle": lambda: DSLPage().load(os.path.join(PAGES_DIR, "battle.json")).show(),
}

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "inventory"
    demo_fn = DEMOS.get(name)
    if not demo_fn:
        print(f"可用 demo: {', '.join(DEMOS.keys())}")
        sys.exit(1)
    demo_fn()
