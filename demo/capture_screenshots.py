"""Capture PyQt5 screenshots for all demo pages."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt5.QtWidgets import QApplication
from dsl.loader import DSLPage

PAGES_DIR = os.path.join(os.path.dirname(__file__), "pages")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "screenshots_pyqt5")

PAGES = {
    "inventory.json": (820, 620),
    "settings.json": (500, 400),
    "shop.json": (700, 520),
    "rpg_status.json": (600, 500),
    "scifi_hub.json": (900, 560),
    "casual_menu.json": (480, 640),
    "arena_result.json": (720, 480),
    "dungeon.json": (600, 500),
    "guild.json": (600, 500),
    "gacha.json": (600, 500),
    "battle.json": (600, 500),
}


def capture_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')

    for json_file, (w, h) in PAGES.items():
        dsl_path = os.path.join(PAGES_DIR, json_file)
        if not os.path.exists(dsl_path):
            print(f"Skipping {json_file} (not found)")
            continue
        page = DSLPage().load(dsl_path)
        page.root.setFixedSize(w, h)
        page.root.show()
        app.processEvents()

        output_path = os.path.join(OUTPUT_DIR, json_file.replace(".json", ".png"))
        page.root.grab().save(output_path)
        print(f"Captured: {output_path}")
        page.unload()


if __name__ == "__main__":
    capture_all()
