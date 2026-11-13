"""Copy what the Remotion reels need into apps/reels/public (git-ignored there; rebuild any time).

    uv run python scripts/marketing/reel_assets.py

- fonts/: Fredoka Bold and Gochi Hand (brand fonts)
- logo.png, mascots/<slug>.svg
- levels.json: slug, name, age, grade, color (hex), mascot path
- pictures/<slug>.svg: the word pictures (assets/pictures)
- pages/<slug>-<n>.png: every inner page of the free preview PDFs (out/previews), 1080px wide
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instagram_launch as L  # noqa: E402

OUT = L.ROOT / "apps" / "reels" / "public"


def main() -> None:
    (OUT / "fonts").mkdir(parents=True, exist_ok=True)
    (OUT / "mascots").mkdir(exist_ok=True)
    (OUT / "pages").mkdir(exist_ok=True)
    for f in ("Fredoka-Bold.woff2", "GochiHand-Regular.woff2"):
        shutil.copy(L.BRAND_FONTS / f, OUT / "fonts" / f)
    shutil.copy(L.BRAND / "logo-horizontal.png", OUT / "logo.png")
    levels = []
    for row in L.LADDER:
        mascot, color = L.LOOKS[row["slug"]]
        shutil.copy(L.WEB / "public" / mascot.lstrip("/"), OUT / "mascots" / f"{row['slug']}.svg")
        grade = str(row["grade"])
        levels.append({
            "slug": row["slug"], "name": row["name"], "age": row["age"],
            "grade": f"Grade {grade}" if grade[0].isdigit() else grade,
            "color": L.COLORS[color], "mascot": f"mascots/{row['slug']}.svg",
        })
        pdf = L.PREVIEWS / f"{row['slug']}.pdf"
        n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout)[1])
        for p in range(2, n):  # skip the preview cover and closing page
            dest = OUT / "pages" / f"{row['slug']}-{p}"
            if not dest.with_suffix(".png").exists():
                subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-scale-to-x", "1080", "-scale-to-y", "-1",
                                "-png", "-singlefile", pdf, dest], check=True)
    (OUT / "pictures").mkdir(exist_ok=True)
    for svg in L.PICTURES.glob("*.svg"):
        shutil.copy(svg, OUT / "pictures" / svg.name)
    (OUT / "levels.json").write_text(json.dumps(levels, indent=1))
    print(f"assets in {OUT.relative_to(L.ROOT)}: {len(levels)} levels, {len(list((OUT / 'pages').glob('*.png')))} pages")


if __name__ == "__main__":
    main()
