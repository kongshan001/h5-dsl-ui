"""Utilities for capturing and comparing screenshots."""
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from dsl.loader import DSLPage


def capture_pyqt5_screenshot(dsl_path, output_path, width=None, height=None):
    """Load a DSL page and capture its screenshot."""
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    page = DSLPage().load(dsl_path)

    if width and height:
        page.root.setFixedSize(width, height)
    page.root.show()
    app.processEvents()

    pixmap = page.root.grab()
    pixmap.save(output_path)
    page.unload()
    return output_path


def compare_screenshots(img_path_a, img_path_b, threshold=0.95):
    """Compare two screenshots pixel-by-pixel.

    Returns (similarity: float, diff_output_path: str|None)
    """
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError:
        raise ImportError("Pillow required: pip install Pillow")

    img_a = Image.open(img_path_a).convert("RGB")
    img_b = Image.open(img_path_b).convert("RGB")

    if img_a.size != img_b.size:
        # Crop both images to the intersection (min dimensions) instead of stretching
        target_w = min(img_a.width, img_b.width)
        target_h = min(img_a.height, img_b.height)
        img_a = img_a.crop((0, 0, target_w, target_h))
        img_b = img_b.crop((0, 0, target_w, target_h))

    diff = ImageChops.difference(img_a, img_b)

    pixels = list(diff.getdata())
    total_diff = sum(sum(p) for p in pixels)
    max_diff = len(pixels) * 3 * 255
    similarity = 1.0 - (total_diff / max_diff) if max_diff > 0 else 1.0

    diff_path = None
    if similarity < threshold:
        diff_highlight = img_a.copy()
        draw = ImageDraw.Draw(diff_highlight)
        diff_data = diff.load()
        for y in range(diff_highlight.height):
            for x in range(diff_highlight.width):
                r, g, b = diff_data[x, y]
                if r + g + b > 30:
                    draw.point((x, y), fill=(255, 0, 0))
        diff_path = img_path_a.replace(".png", "_diff.png")
        diff_highlight.save(diff_path)

    return similarity, diff_path
