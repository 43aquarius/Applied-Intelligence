#!/usr/bin/env python3
"""Screenshot diagram HTML -> PNG @2x (300dpi-equivalent) per academic.md Path B."""
import sys
from playwright.sync_api import sync_playwright

html_path = sys.argv[1]
out_png = sys.argv[2]
w = int(sys.argv[3]) if len(sys.argv) > 3 else 1480
h = int(sys.argv[4]) if len(sys.argv) > 4 else 760

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--force-color-profile=srgb"])
    page = browser.new_page(viewport={"width": w, "height": h},
                            device_scale_factor=2)
    page.goto(f"file://{html_path}")
    page.wait_for_timeout(1200)  # font settle
    page.screenshot(path=out_png, full_page=False)
    browser.close()
print(f"saved {out_png} ({w}x{h} @2x)")
