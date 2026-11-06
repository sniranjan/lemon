"""Upload finished levels to R2 so they go on sale (and their free previews), from the rendered PDFs in out/.

    uv run python scripts/publish_levels.py chicks ducklings     # specific levels
    uv run python scripts/publish_levels.py --all                # every level whose books exist

For each level it uploads the whole-level books (`<slug>-<subject>-level.pdf` and `-answers.pdf`) to
`levels/<slug>/` and `out/previews/<slug>.pdf` to `previews/<slug>.pdf`. Render first:
`ws render --subject … --level … --pdf` for every strand and `ws preview <slug>`.
A level is only published when every strand in syllabus/ladder.yaml has its level book; it refuses any PDF
whose text contains an internal level code. The site picks levels up from R2 automatically.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
WEB = ROOT / "apps" / "web"
BUCKET = "paperlessons-files"
SUBJECT_NAME = {"english": "reading", "math": "math", "pencil": "pencil"}


def internal_codes() -> re.Pattern:
    codes = yaml.safe_load((ROOT / "content" / "banned.yaml").read_text())["internal_codes"]
    return re.compile(r"\b(" + "|".join(map(re.escape, codes)) + r"|EN-\w+|MA-\w+)\b")


def files_for(rung: dict) -> list[Path] | None:
    files: list[Path] = []
    for subject, code in rung["strands"].items():
        book = OUT / subject / str(code) / f"{rung['slug']}-{SUBJECT_NAME[subject]}-level.pdf"
        if not book.exists():
            return None
        files.append(book)
        answers = book.with_name(book.stem + "-answers.pdf")
        if answers.exists():
            files.append(answers)
    return files


def upload(key: str, path: Path) -> None:
    subprocess.run(
        ["npx", "wrangler", "r2", "object", "put", f"{BUCKET}/{key}", "--file", str(path),
         "--content-type", "application/pdf", "--remote"],
        cwd=WEB, check=True, capture_output=True,
    )
    print(f"  {key}  ({len(PdfReader(path).pages)} pages)")


def main(argv: list[str]) -> int:
    ladder = yaml.safe_load((ROOT / "syllabus" / "ladder.yaml").read_text())
    wanted = None if "--all" in argv else set(argv)
    bad = internal_codes()
    for rung in ladder:
        if wanted is not None and rung["slug"] not in wanted:
            continue
        files = files_for(rung)
        preview = OUT / "previews" / f"{rung['slug']}.pdf"
        if not files or not preview.exists():
            if wanted is not None:
                print(f"{rung['slug']}: not ready (missing a level book or preview)")
            continue
        for f in [*files, preview]:
            text = " ".join(p.extract_text() or "" for p in PdfReader(f).pages)
            if (m := bad.search(text)) is not None:
                print(f"{rung['slug']}: REFUSED, {f.name} contains internal code {m.group(0)!r}")
                return 1
        print(f"{rung['slug']}:")
        for f in files:
            upload(f"levels/{rung['slug']}/{f.name}", f)
        upload(f"previews/{rung['slug']}.pdf", preview)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
