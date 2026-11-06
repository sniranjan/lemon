import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
names = sys.argv[2:]
root = Path("assets/pictures").resolve()
cells = "".join(f'<div><img src="{(root / (n + ".svg")).as_uri()}"><p>{n}</p></div>' for n in names)
html = f'<html><body style="margin:0;display:flex;flex-wrap:wrap;width:1000px;font:20px sans-serif">{cells}<style>div{{width:200px;text-align:center}}img{{width:180px;height:180px}}</style></body></html>'
(Path(sys.argv[1]).with_suffix(".html")).write_text(html)
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1000, "height": 400})
    pg.goto(Path(sys.argv[1]).with_suffix(".html").resolve().as_uri()); pg.screenshot(path=sys.argv[1], full_page=True); b.close()
