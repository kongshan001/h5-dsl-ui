"""Visual regression tests comparing HTML and PyQt5 rendering."""
import os
import pytest
from PyQt5.QtWidgets import QApplication
from tests.screenshot_utils import capture_pyqt5_screenshot, compare_screenshots

PAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "demo", "pages")
HTML_SCREENSHOTS = os.path.join(os.path.dirname(__file__), "..", "demo", "html_screenshots")

PAGES = ["inventory", "settings", "shop", "rpg_status", "scifi_hub", "casual_menu", "arena_result", "dungeon", "guild", "gacha", "battle"]

PAGE_SIZES = {
    "inventory": (820, 620),
    "settings": (500, 400),
    "shop": (700, 520),
    "rpg_status": (600, 500),
    "scifi_hub": (900, 560),
    "casual_menu": (480, 640),
    "arena_result": (720, 480),
    "dungeon": (600, 500),
    "guild": (600, 500),
    "gacha": (600, 500),
    "battle": (600, 500),
}


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("page_name", PAGES)
def test_visual_similarity(app, tmp_path, page_name):
    """Compare PyQt5 rendering against HTML browser rendering."""
    dsl_path = os.path.join(PAGES_DIR, f"{page_name}.json")
    if not os.path.exists(dsl_path):
        pytest.skip(f"DSL file not found: {dsl_path}")

    pyqt5_path = str(tmp_path / f"{page_name}_pyqt5.png")
    w, h = PAGE_SIZES.get(page_name, (720, 480))
    capture_pyqt5_screenshot(dsl_path, pyqt5_path, w, h)

    html_path = os.path.join(HTML_SCREENSHOTS, f"{page_name}.png")
    if not os.path.exists(html_path):
        pytest.skip(f"HTML screenshot not found: {html_path}")

    similarity, diff_path = compare_screenshots(html_path, pyqt5_path)
    assert similarity >= 0.60, (
        f"Visual similarity {similarity:.2%} below threshold for {page_name}"
    )
