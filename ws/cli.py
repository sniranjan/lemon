"""`ws` command line (CLAUDE.md §9)."""

from __future__ import annotations

from typing import Optional

import typer

from . import registry
from .syllabus import ROOT, load_level, parse_pages, resolve_page, sheet_id

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Generate, verify and print worksheets.")
pictures_app = typer.Typer(no_args_is_help=True, help="Picture helpers.")
vocab_app = typer.Typer(no_args_is_help=True, help="Word bank helpers.")
syllabus_app = typer.Typer(no_args_is_help=True, help="Inspect the syllabus.")
app.add_typer(pictures_app, name="pictures")
app.add_typer(vocab_app, name="vocab")
app.add_typer(syllabus_app, name="syllabus")


def _load(subject: str, level: str):
    try:
        return load_level(subject, level)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)


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
    """Generate sheets: by section (next --count unused pages, or a --part), --pages or --all."""
    from .generate import generate_pages, select_pages

    lvl = _load(subject, level)
    try:
        page_list = select_pages(lvl, section=section, part=part, count=count,
                                 pages=parse_pages(pages) if pages else None, all_pages=all_, variant=variant)
        if section:
            s = lvl.section(section)
            outside = [p for p in page_list if not s.pages[0] <= p <= s.pages[1]]
            if outside:
                raise ValueError(f"pages {outside} are outside {level}-{section} (pages {s.pages[0]}–{s.pages[1]})")
        made = generate_pages(lvl, page_list, variant, seed, sheet_type)
    except (KeyError, ValueError) as e:
        typer.echo(f"cannot generate: {e.args[0]}", err=True)
        raise typer.Exit(1)
    for sheet, path in made:
        typer.echo(f"{sheet.id}  page {sheet.page_number}  {sheet.sheet_type}  {path.relative_to(ROOT)}")


def _print_issues(issues) -> int:
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    for i in errors:
        typer.echo(f"ERROR    {i.sheet_id}: {i.message}")
    for i in warnings:
        typer.echo(f"warning  {i.sheet_id}: {i.message}")
    return len(errors)


@app.command()
def verify(
    subject: Optional[str] = typer.Option(None),
    level: Optional[str] = typer.Option(None),
    layout: bool = typer.Option(True, "--layout/--no-layout", help="Render pages and run layout checks"),
) -> None:
    """Check generated sheets (content, exposure, layout) and write contact sheets."""
    from collections import defaultdict

    from .generate import OUT_DIR, load_manifest
    from .render import contact_sheet
    from .verify import verify_layout, verify_sheets

    sheets = load_manifest(subject, level)
    if not sheets:
        typer.echo("nothing generated yet", err=True)
        raise typer.Exit(1)
    issues = verify_sheets(sheets)
    if layout:
        layout_issues, pngs = verify_layout(sheets)
        issues += layout_issues
        for (subj, lvl), files in pngs.items():
            by_section = defaultdict(list)
            for f in files:
                by_section[f.parent.name].append(f)
            out = contact_sheet(files, OUT_DIR / subj / lvl / "review.png", f"{subj} {lvl}: {len(files)} pages")
            typer.echo(f"contact sheet: {out.relative_to(ROOT)}")
            for code, section_files in sorted(by_section.items()):
                contact_sheet(section_files, OUT_DIR / subj / lvl / f"review-{code}.png",
                              f"{subj} {lvl} section {code}: {len(section_files)} pages")
    n_err = _print_issues(issues)
    n_warn = sum(i.severity == "warning" for i in issues)
    typer.echo(f"{len(sheets)} sheets checked: {n_err} errors, {n_warn} warnings")
    if n_err:
        raise typer.Exit(1)


@app.command()
def render(
    subject: str = typer.Option(...),
    level: str = typer.Option(...),
    pdf: bool = typer.Option(False, "--pdf", help="Also build booklet PDFs"),
    png: bool = typer.Option(False, "--png", help="Page PNGs + contact sheet (layout preview)"),
) -> None:
    """Render generated sheets to PNG (and later PDF)."""
    from .generate import OUT_DIR, load_manifest, sheet_dir
    from .render import contact_sheet, render_pngs

    if pdf:
        from .booklet import build_booklets

        variants = sorted({s.variant for s in load_manifest(subject, level)}) or [1]
        errors = 0
        for v in variants:
            report = build_booklets(subject, level, v)
            for b in report.booklets:
                typer.echo(f"booklet: {b.relative_to(ROOT)}")
            errors += _print_issues(report.issues)
        if errors:
            raise typer.Exit(1)
        if not png:
            return
    if not png:
        typer.echo("give --pdf (booklets) and/or --png (page images + contact sheet)", err=True)
        raise typer.Exit(1)
    sheets = load_manifest(subject, level)
    if not sheets:
        typer.echo(f"nothing generated yet for {subject} {level}", err=True)
        raise typer.Exit(1)
    results = render_pngs([sheet_dir(s) / f"{s.id}.html" for s in sheets])
    failed = False
    for r in results:
        status = "ok" if not r.problems else "; ".join(r.problems)
        failed |= bool(r.problems)
        typer.echo(f"{r.png.relative_to(ROOT)}  {status}")
    out = OUT_DIR / subject / level / "review.png"
    contact_sheet([r.png for r in results], out, f"{subject} {level}: {len(results)} pages",
                  grayscale_sample=results[-1].png)
    typer.echo(f"contact sheet: {out.relative_to(ROOT)}")
    if failed:
        raise typer.Exit(1)


@app.command()
def preview(
    slug: str = typer.Argument(..., help="public level, e.g. chicks (syllabus/ladder.yaml)"),
) -> None:
    """Free preview PDF for the website: out/previews/<slug>.pdf (each strand's `preview_pages`)."""
    from .booklet import build_preview
    from .generate import generate_pages
    from .syllabus import STRAND_ORDER, ladder_level, level_path, load_level

    try:
        rung = ladder_level(slug)
    except KeyError as e:
        typer.echo(e.args[0], err=True)
        raise typer.Exit(1)
    # regenerate (deterministic) so the pages use the current templates and content
    for subject in STRAND_ORDER:
        code = rung.strands.get(subject)
        if code and level_path(subject, code).exists():
            lvl = load_level(subject, code)
            for sheet, _ in generate_pages(lvl, sorted(lvl.preview_pages)):
                typer.echo(f"{subject:<8} page {sheet.page_number:>3}  {sheet.sheet_type}")
    report = build_preview(slug)
    for b in report.booklets:
        typer.echo(f"preview: {b.relative_to(ROOT)}")
    if _print_issues(report.issues):
        raise typer.Exit(1)


@pictures_app.command("missing")
def pictures_missing(subject: str = typer.Option(...), level: str = typer.Option(...)) -> None:
    """List words with no SVG picture or no licence entry."""
    from .content import licenses, picture_path, vocab

    lic = licenses()
    missing = [w for w in vocab(subject) if w.level == level and w.picture is not None
               and (not picture_path(w.picture).exists() or w.picture not in lic)]
    for w in missing:
        what = "no SVG" if not picture_path(w.picture).exists() else "no licence entry"
        typer.echo(f"{w.word:<12} {w.picture}.svg  {what}")
    typer.echo(f"{len(missing)} missing")
    if missing:
        raise typer.Exit(1)


@pictures_app.command("sheet")
def pictures_sheet() -> None:
    """Contact sheet of all pictures (color + grayscale); flags fills outside 50–75% lightness."""
    from .pictures import check_pictures, picture_sheet

    reports = check_pictures()
    out = picture_sheet(reports, ROOT / "out" / "pictures" / "contact.png")
    for r in reports:
        if r.problems:
            typer.echo(f"{r.slug}: " + "; ".join(r.problems))
    flagged = sum(bool(r.problems) for r in reports)
    typer.echo(f"{len(reports)} pictures, {flagged} flagged. contact sheet: {out.relative_to(ROOT)}")
    if flagged:
        raise typer.Exit(1)


@vocab_app.command("stats")
def vocab_stats(level: str = typer.Option(...)) -> None:
    """Words in the bank vs. target, and exposure counts."""
    _not_yet("vocab stats", 4)


@syllabus_app.command("show")
def syllabus_show(subject: str, level: str) -> None:
    """Print a level's sections, page ranges, parts and sheet types."""
    lvl = _load(subject, level)

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
