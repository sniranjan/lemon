"""Gift card PDF fonts: the site's own fonts (fontsource, SIL OFL 1.1) as static TTFs for pdf-lib.

The fontsource woff2 files are per weight and per script subset; pdf-lib embeds TTF/OTF, and the Google Fonts
TTFs of Fredoka and Nunito are variable fonts (pdf-lib would only use the default weight). So: decompress the
static weights we draw with and merge the latin + latin-ext subsets into one font each.

    python3 apps/web/scripts/gift-card/build_fonts.py      # needs fontTools + brotli

Writes apps/web/scripts/gift-card/fonts/*.ttf; then run `node apps/web/scripts/gift-card/bundle.mjs`.
"""

import os
from pathlib import Path

from fontTools.merge import Merger
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
FONTSOURCE = HERE.parents[3] / "node_modules" / "@fontsource"
OUT = HERE / "fonts"

JOBS = {
    "Fredoka-Bold.ttf": ["fredoka/files/fredoka-latin-700-normal.woff2", "fredoka/files/fredoka-latin-ext-700-normal.woff2"],
    "Nunito-Regular.ttf": ["nunito/files/nunito-latin-400-normal.woff2", "nunito/files/nunito-latin-ext-400-normal.woff2"],
    "Nunito-Bold.ttf": ["nunito/files/nunito-latin-700-normal.woff2", "nunito/files/nunito-latin-ext-700-normal.woff2"],
    "GochiHand-Regular.ttf": ["gochi-hand/files/gochi-hand-latin-400-normal.woff2"],
}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name, parts in JOBS.items():
        tmp = []
        for i, p in enumerate(parts):
            f = TTFont(FONTSOURCE / p)
            f.flavor = None
            t = OUT / f"_part{i}.ttf"
            f.save(t)
            tmp.append(str(t))
        dest = OUT / name
        if len(tmp) == 1:
            os.replace(tmp[0], dest)
        else:
            Merger().merge(tmp).save(dest)
            for t in tmp:
                os.remove(t)
        print(name, dest.stat().st_size, "bytes,", len(TTFont(dest).getBestCmap()), "characters")


if __name__ == "__main__":
    main()
