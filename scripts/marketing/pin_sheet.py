"""Make a page for posting pins by hand (while the API app waits for approval).

    uv run python scripts/marketing/pin_sheet.py            # → marketing/pinterest/pins/manual.html

Open the page in a browser next to pinterest.com/pin-creation-tool: boards to make first, then each pin in
publish order with its image (drag it into Pinterest) and copy buttons for title, description, link and alt text.
Ticks are remembered in that browser only. Tell Claude which pins went up so they are added to pinned.jsonl and
the API never posts them twice.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "marketing/pinterest"
OUT = PIN / "pins/manual.html"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def field(label: str, value: str) -> str:
    return (
        f'<div class="f"><div class="l">{label}<button onclick="cp(this)">Copy</button></div>'
        f'<div class="v">{esc(value)}</div></div>'
    )


def main() -> None:
    boards = yaml.safe_load((PIN / "boards.yaml").read_text())
    pins = json.loads((PIN / "pins/manifest.json").read_text())["pins"]
    board_html = "".join(
        f'<div class="b">{field("Board name", b["name"])}{field("Board description", b["description"].strip())}</div>'
        for b in boards.values()
    )
    pin_html = []
    for i, p in enumerate(pins, 1):
        img = Path(p["image"]).name
        pin_html.append(
            f'<section class="pin" id="{esc(p["id"])}"><label class="done"><input type="checkbox" data-id="{esc(p["id"])}"> '
            f'<b>{i}. {esc(p["id"])}</b> → board <b>{esc(boards[p["board"]]["name"])}</b></label>'
            f'<div class="row"><a href="batch-01/{esc(img)}" download><img src="batch-01/{esc(img)}" alt=""></a><div class="fs">'
            + field("Title", p["title"])
            + field("Description", p["description"])
            + field("Link", p["link"])
            + field("Alt text", p["alt_text"])
            + "</div></div></section>"
        )
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Pins to post</title>
<style>
body{{font:15px/1.45 system-ui,sans-serif;margin:0 auto;max-width:1000px;padding:16px;background:#fffaf3;color:#222}}
h1{{margin:.2em 0}} h2{{margin-top:1.6em}} .b,.pin{{background:#fff;border:2px solid #222;border-radius:14px;padding:12px;margin:12px 0}}
.row{{display:flex;gap:14px;flex-wrap:wrap}} .row img{{width:200px;border-radius:8px;border:1px solid #ccc}}
.fs{{flex:1;min-width:260px}} .f{{margin:6px 0}} .l{{font-weight:700;font-size:13px;color:#0B7A75}}
.v{{white-space:pre-wrap;word-break:break-word}} button{{margin-left:8px;font-size:12px;cursor:pointer}}
.pin.is-done{{opacity:.45}} .done{{display:block;margin-bottom:8px;font-size:16px}} .tip{{color:#555}}
</style></head><body>
<h1>Pins to post ({len(pins)})</h1>
<p class="tip">Post about 3 a day, top to bottom. On pinterest.com: Create → Pin, drag the image in (or click it
here to save it), paste title, description, link and alt text (under "More options"), pick the board, Publish.
Tick the box when it's up.</p>
<h2>1. Make these boards first</h2>{board_html}
<h2>2. Pins, in order</h2>{''.join(pin_html)}
<script>
function cp(b){{const v=b.parentNode.nextElementSibling.textContent;navigator.clipboard.writeText(v);b.textContent="Copied";setTimeout(()=>b.textContent="Copy",1200)}}
document.querySelectorAll("input[data-id]").forEach(c=>{{const k="pin-done-"+c.dataset.id;
try{{c.checked=localStorage.getItem(k)==="1"}}catch(e){{}}
const sync=()=>c.closest(".pin").classList.toggle("is-done",c.checked);sync();
c.onchange=()=>{{try{{localStorage.setItem(k,c.checked?"1":"0")}}catch(e){{}}sync()}}}});
</script></body></html>"""
    OUT.write_text(page)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(pins)} pins, {len(boards)} boards)")


if __name__ == "__main__":
    main()
