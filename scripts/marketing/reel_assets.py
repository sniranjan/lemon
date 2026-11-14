"""Copy what the Remotion reels need into apps/reels/public (git-ignored there; rebuild any time).

    uv run python scripts/marketing/reel_assets.py

- fonts/: Fredoka Bold and Gochi Hand (brand fonts)
- logo.png, mascots/<slug>.svg
- levels.json: slug, name, age, grade, color (hex), mascot path
- pictures/<slug>.svg: the word pictures (assets/pictures)
- pages/<slug>-<n>.png: every inner page of the free preview PDFs (out/previews), 1080px wide
- audio/: music beds (Kevin MacLeod, incompetech.com, CC BY 4.0: credit in every caption) and our own
  synthesized tick / tock / ding (apps/reels/src/audio.tsx)
"""

from __future__ import annotations

import json
import math
import random
import re
import struct
import urllib.parse
import urllib.request
import wave
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import instagram_launch as L  # noqa: E402

OUT = L.ROOT / "apps" / "reels" / "public"


MUSIC = ["Easy Lemon", "Carefree", "Thinking Music", "Wallpaper"]
RATE = 44100


def _wav(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x)) * 32767)) for x in samples))


def _tick(f1: float, f2: float, rng: random.Random) -> list[float]:
    out = []
    for i in range(int(RATE * 0.05)):
        t = i / RATE
        e = math.exp(-t * 90)
        out.append(0.6 * e * (0.7 * math.sin(2 * math.pi * f1 * t) + 0.3 * math.sin(2 * math.pi * f2 * t))
                   + 0.08 * e * rng.uniform(-1, 1))
    return out


def _ding() -> list[float]:
    out = []
    for i in range(int(RATE * 1.4)):
        t = i / RATE
        out.append(0.5 * min(1, t / 0.004) * (0.6 * math.sin(2 * math.pi * 1318.5 * t) * math.exp(-t * 3.2)
                                              + 0.3 * math.sin(2 * math.pi * 1975.5 * t) * math.exp(-t * 4.5)
                                              + 0.15 * math.sin(2 * math.pi * 2637 * t) * math.exp(-t * 7)))
    return out


def audio() -> None:
    d = OUT / "audio"
    d.mkdir(exist_ok=True)
    for title in MUSIC:
        dest = d / (title.lower().replace(" ", "-") + ".mp3")
        if not dest.exists():
            url = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + urllib.parse.quote(title) + ".mp3"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            dest.write_bytes(urllib.request.urlopen(req).read())
    rng = random.Random(1)
    _wav(d / "tick.wav", _tick(1500, 2300, rng))
    _wav(d / "tock.wav", _tick(1100, 1700, rng))
    _wav(d / "ding.wav", _ding())


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
    audio()
    (OUT / "levels.json").write_text(json.dumps(levels, indent=1))
    print(f"assets in {OUT.relative_to(L.ROOT)}: {len(levels)} levels, {len(list((OUT / 'pages').glob('*.png')))} pages")


if __name__ == "__main__":
    main()
