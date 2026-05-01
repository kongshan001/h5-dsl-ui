"""
HTML → DSL 转换脚本
将 demo/html/ 下的 HTML/CSS 文件转换为 DSL JSON，输出到 demo/pages/
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dsl.converter.html_to_dsl import convert_html_to_dsl_file

HTML_DIR = os.path.join(os.path.dirname(__file__), "html")
PAGES_DIR = os.path.join(os.path.dirname(__file__), "pages")


def convert_all():
    os.makedirs(PAGES_DIR, exist_ok=True)

    pages = {
        "inventory.html": "inventory_page",
        "settings.html": "settings_page",
        "shop.html": "shop_page",
        "rpg_status.html": "rpg_status_page",
        "scifi_hub.html": "scifi_hub_page",
        "casual_menu.html": "casual_menu_page",
        "arena_result.html": "arena_result_page",
        "dungeon.html": "dungeon_page",
        "guild.html": "guild_page",
        "gacha.html": "gacha_page",
        "battle.html": "battle_page",
    }

    for html_file, page_name in pages.items():
        html_path = os.path.join(HTML_DIR, html_file)
        json_name = html_file.replace(".html", ".json")
        json_path = os.path.join(PAGES_DIR, json_name)

        if not os.path.exists(html_path):
            print(f"跳过 {html_file}（文件不存在）")
            continue

        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # 传入完整 HTML（含 <style> 块），转换器会自动提取 CSS 规则
        convert_html_to_dsl_file(html, json_path, page_name=page_name)
        print(f"转换完成: {html_file} → {json_name}")


if __name__ == "__main__":
    convert_all()
