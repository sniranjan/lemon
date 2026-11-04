"""`ws` command line (CLAUDE.md §9)."""

from __future__ import annotations

from typing import Optional

import typer

from . import registry
from .syllabus import load_level, resolve_page, sheet_id

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Generate, verify and print worksheets.")
pictures_app = typer.Typer(no_args_is_help=True, help="Picture helpers.")
vocab_app = typer.Typer(no_args_is_help=True, help="Word bank helpers.")
syllabus_app = typer.Typer(no_args_is_help=True, help="Inspect the syllabus.")
app.add_typer(pictures_app, name="pictures")
app.add_typer(vocab_app, name="vocab")
app.add_typer(syllabus_app, name="syllabus")


def _not_yet(command: str, milestone: int) -> None:
    typer.echo(f"ws {command}: not implemented yet (planned for milestone {milestone})", err=True)
    raise typer.Exit(2)


@app.command()
def generate(
    subject: str = typer.Option(..., help="english | math | pencil"),
    level: str = typer.Option(..., help="e.g. 7A, 6A, ZI"),
    section: Optional[str] = typer.Option(None, help="Section letter, e.g. A"),
    part: Optional[int] = typer.Option(None, help="Part number within the section"),
    count: Optional[int] = typer.Option(None, help="Next N unused pages of the section"),
    pages: Optional[str] = typer.Option(None, help="Page range, e.g. 1-50"),
    all_: bool = typer.Option(False, "--all", help="Every page of the level"),
    sheet_type: Optional[str] = typer.Option(None, help="Force one sheet type"),
    seed: Optional[int] = typer.Option(None, help="Override the per-page seed"),
    variant: int = typer.Option(1, help="Alternative version of the same pages"),
) -> None:
    """Generate sheets."""
    _not_yet("generate", 2)


@app.command()
def verify(
    subject: Optional[str] = typer.Option(None),
    level: Optional[str] = typer.Option(None),
) -> None:
    """Run content and layout checks on generated sheets."""
    _not_yet("verify", 3)


@app.command()
def render(
    subject: str = typer.Option(...),
    level: str = typer.Option(...),
    pdf: bool = typer.Option(False, "--pdf", help="Also build booklet PDFs"),
) -> None:
    """Render sheets to HTML/PDF."""
    _not_yet("render", 3)


@pictures_app.command("missing")
def pictures_missing(subject: str = typer.Option(...), level: str = typer.Option(...)) -> None:
    """List words with no SVG picture."""
    _not_yet("pictures missing", 4)


@pictures_app.command("sheet")
def pictures_sheet() -> None:
    """Make a contact sheet PNG of all pictures."""
    _not_yet("pictures sheet", 4)


@vocab_app.command("stats")
def vocab_stats(level: str = typer.Option(...)) -> None:
    """Words in the bank vs. target, and exposure counts."""
    _not_yet("vocab stats", 4)


@syllabus_app.command("show")
def syllabus_show(subject: str, level: str) -> None:
    """Print a level's sections, page ranges, parts and sheet types."""
    try:
        lvl = load_level(subject, level)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    built = set(registry.implemented())
    typer.echo(f"{lvl.subject} {lvl.level}: {lvl.title}  ({lvl.pages} pages, {lvl.daily_pages}/day)")
    if lvl.vocab_target:
        typer.echo(f"  vocab target: {lvl.vocab_target} words")
    for aim in lvl.aims:
        typer.echo(f"  - {aim}")
    for s in lvl.sections:
        lo, hi = s.pages
        first, last = sheet_id(lvl, s, lo), sheet_id(lvl, s, hi)
        src = "  [ours]" if s.source == "ours" else ""
        typer.echo(f"\n  {s.code}  {s.name}  pages {lo}–{hi}  ({first} … {last}){src}")
        for p in s.parts or [None]:
            page = p.pages[0] if p else lo
            spec = resolve_page(lvl, page)
            types = p.sheet_types if p and p.sheet_types else s.sheet_types
            marks = ", ".join(t if t in built else f"{t}*" for t in types)
            label = f"part {p.part} pages {p.pages[0]}–{p.pages[1]}" if p else "all pages"
            rules = ", ".join(f"{k}={v}" for k, v in spec.rules.items()) or "-"
            typer.echo(f"     {label:<24} {marks:<44} {rules}")
    if not built.issuperset(t for s in lvl.sections for t in s.sheet_types):
        typer.echo("\n  * sheet type not implemented yet")


if __name__ == "__main__":
    app()
