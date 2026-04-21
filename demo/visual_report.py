"""Generate an HTML report comparing HTML and PyQt5 screenshots."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.screenshot_utils import compare_screenshots

HTML_DIR = os.path.join(os.path.dirname(__file__), "html_screenshots")
PYQT5_DIR = os.path.join(os.path.dirname(__file__), "screenshots_pyqt5")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "visual_reports")

PAGES = ["inventory", "settings", "shop", "rpg_status", "scifi_hub", "casual_menu", "arena_result"]


def generate_report():
    os.makedirs(REPORT_DIR, exist_ok=True)
    rows = []
    for name in PAGES:
        html_img = os.path.join(HTML_DIR, f"{name}.png")
        pyqt5_img = os.path.join(PYQT5_DIR, f"{name}.png")
        if not os.path.exists(html_img) or not os.path.exists(pyqt5_img):
            continue
        similarity, diff_path = compare_screenshots(html_img, pyqt5_img)
        status = "PASS" if similarity >= 0.90 else "FAIL"
        color = "#4caf50" if status == "PASS" else "#f44336"
        rows.append(f'''
        <tr>
            <td>{name}</td>
            <td><img src="../{os.path.relpath(html_img, REPORT_DIR)}" width="200"></td>
            <td><img src="../{os.path.relpath(pyqt5_img, REPORT_DIR)}" width="200"></td>
            <td style="color:{color};font-weight:bold">{similarity:.1%}</td>
            <td>{status}</td>
        </tr>''')

    html = f'''<html><head><title>Visual Comparison Report</title>
    <style>body{{font-family:sans-serif}}table{{border-collapse:collapse}}td,th{{padding:8px;border:1px solid #ddd}}img{{border:1px solid #ccc}}</style>
    </head><body><h1>H5 DSL Visual Comparison Report</h1>
    <table>
        <tr><th>Page</th><th>HTML</th><th>PyQt5</th><th>Similarity</th><th>Status</th></tr>
        {"".join(rows)}
    </table></body></html>'''

    report_path = os.path.join(REPORT_DIR, "report.html")
    with open(report_path, "w") as f:
        f.write(html)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    generate_report()
