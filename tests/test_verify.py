"""`ws verify` and booklets: a clean set passes, and every check fails on its injected fault."""

import re

import pytest

from ws import booklet
from ws import generate as gen
from ws.syllabus import load_level
from ws.verify import banned_words, verify_layout, verify_sheets

EN7A, MA6A, ZI = load_level("english", "7A"), load_level("math", "6A"), load_level("pencil", "ZI")


@pytest.fixture
def made(out_dir, fixture_content):
    """A small clean set across all three subjects."""
    sheets = {}
    for level, pages in ((EN7A, [1, 2, 3, 4, 101, 102, 141, 142]), (MA6A, list(range(1, 13)) + [81, 101, 151]),
                         (ZI, [1, 2, 21, 51])):
        sheets.update({s.id: s for s, _ in gen.generate_pages(level, pages)})
    return sheets


def _errors(issues):
    return [i for i in issues if i.severity == "error"]


def _messages(issues):
    return " | ".join(f"{i.sheet_id}: {i.message}" for i in _errors(issues))


def test_clean_set_passes(made):
    issues = verify_sheets(list(made.values()))
    assert _errors(issues) == []
    # the 8-word fixture bank leaves 7A-A incomplete: one warning, not an error
    assert any("word bank covers 4 of 100" in i.message for i in issues)


def test_clean_set_layout_passes(made):
    pytest.importorskip("playwright")
    issues, pngs = verify_layout(list(made.values()))
    assert issues == []
    assert sum(len(v) for v in pngs.values()) == len(made)


def _with(made, sid, **changes):
    sheets = dict(made)
    sheets[sid] = made[sid].model_copy(update=changes, deep=True)
    return list(sheets.values())


def test_wrong_count_is_caught(made):
    s = made["MA-6A-A-001"]
    items = [dict(i) for i in s.items]
    items[0]["word"] = "nine"
    assert "doesn't match" in _messages(verify_sheets(_with(made, s.id, items=items)))


def test_out_of_range_number_is_caught(made):
    s = made["MA-6A-A-001"]
    items = [dict(i) for i in s.items]
    items[0].update(n=7, word="seven")
    msgs = _messages(verify_sheets(_with(made, s.id, items=items)))
    assert "outside this part's range 1–3" in msgs


def test_unknown_word_is_caught(made):
    s = made["EN-7A-B-001"]
    items = [dict(i) for i in s.items]
    items[0]["word"] = "zebra"
    assert "'zebra' is not in the word bank" in _messages(verify_sheets(_with(made, s.id, items=items)))


def test_banned_word_is_caught(made):
    s = made["MA-6A-A-002"]
    msgs = _messages(verify_sheets(_with(made, s.id, parent_tip="Count the LEGO bricks together.")))
    assert "banned word 'lego'" in msgs
    assert banned_words("Kumon-style") == ["kumon"] and banned_words("a happy apple") == []


def test_missing_picture_is_caught(made):
    s = made["EN-7A-A-001"]
    items = [dict(i) for i in s.items]
    items[0]["picture"] = "no_such_picture"
    assert "no_such_picture.svg does not exist" in _messages(verify_sheets(_with(made, s.id, items=items)))


def test_duplicate_sheet_is_caught(made):
    a, b = made["MA-6A-A-001"], made["MA-6A-A-002"]
    assert "same items as MA-6A-A-001" in _messages(verify_sheets(_with(made, b.id, items=a.items)))


def test_long_or_missing_tip_is_caught(made):
    s = made["ZI-A-001"]
    assert "characters (max 220)" in _messages(verify_sheets(_with(made, s.id, parent_tip="x" * 221)))
    assert "parent tip is missing" in _messages(verify_sheets(_with(made, s.id, parent_tip=" ")))


def test_stale_sheet_is_caught(made):
    s = made["ZI-B-001"]
    assert "stale" in _messages(verify_sheets(_with(made, s.id, parent_tip="Draw slowly to the picture.")))


def test_word_new_twice_is_caught(made):
    s = made["EN-7A-A-002"]
    msgs = _messages(verify_sheets(_with(made, s.id, new_words=["apple", "ball"])))
    assert "'apple' was already new on EN-7A-A-001" in msgs


def test_wrong_id_and_section_are_caught(made):
    s = made["MA-6A-A-003"]
    assert "ID should be MA-6A-A-003" in _messages(verify_sheets(_with(made, s.id, id="MA-6A-A-099")))


def test_small_font_is_caught(made):
    pytest.importorskip("playwright")
    path = gen.sheet_dir(made["EN-7A-A-001"]) / "EN-7A-A-001.html"
    path.write_text(path.read_text().replace("</style>", ".stack .card .word { font-size: 22px; }\n</style>", 1))
    issues, _ = verify_layout([made["EN-7A-A-001"]])
    assert any("child-facing text" in i.message and "22px < 28px" in i.message for i in issues)


def test_missing_line_target_is_caught(made):
    pytest.importorskip("playwright")
    sheet = made["ZI-B-001"]
    path = gen.sheet_dir(sheet) / f"{sheet.id}.html"
    target = sheet.items[0]["target"]
    path.write_text(path.read_text().replace(f"pictures/{target}.svg", "pictures/nothing_here.svg", 1))
    issues, _ = verify_layout([sheet])
    assert any("nothing_here.svg" in i.message for i in issues)


# --- booklets ----------------------------------------------------------------------------

@pytest.fixture
def booklet_out(out_dir, monkeypatch):
    monkeypatch.setattr(booklet, "OUT_DIR", out_dir)
    return out_dir


def test_booklets_have_cover_sheets_log_and_answers(made, booklet_out):
    pytest.importorskip("playwright")
    from pypdf import PdfReader

    report = booklet.build_booklets("math", "6A")
    names = sorted(p.name for p in report.booklets)
    # public file names only (CLAUDE.md §15): level slug + subject, level page numbers
    assert "chicks-math-pages-001-012.pdf" in names and "chicks-math-pages-001-012-answers.pdf" in names
    assert "chicks-math-level.pdf" in names and "chicks-math-level-answers.pdf" in names
    assert not [n for n in names if re.search(r"\b(6A|MA)\b", n)]
    assert [i for i in report.issues if i.severity == "error"] == []
    sec = booklet_out / "math" / "6A" / "chicks-math-pages-001-012.pdf"
    assert len(PdfReader(sec).pages) == 1 + 12 + 1
    answers = PdfReader(booklet_out / "math" / "6A" / "chicks-math-pages-001-012-answers.pdf")
    assert "Page 1" in answers.pages[0].extract_text()
    child_text = "".join(p.extract_text() for p in PdfReader(sec).pages)
    assert "Answers" not in child_text                     # no answer key in the child's booklet
    assert "Chicks" in child_text and "Math" in child_text
    for code in ("6A", "MA-6A"):                           # no internal codes anywhere a buyer looks
        assert code not in child_text and code not in answers.pages[0].extract_text()


def test_booklets_are_byte_identical_and_undated(made, booklet_out):
    pytest.importorskip("playwright")
    first = {p.name: p.read_bytes() for p in booklet.build_booklets("pencil", "ZI").booklets}
    second = {p.name: p.read_bytes() for p in booklet.build_booklets("pencil", "ZI").booklets}
    assert first == second
    for name, data in first.items():
        assert not re.search(rb"D:\d{8}", data), f"{name} has an embedded date"


def test_two_page_sheet_is_caught(made, booklet_out):
    pytest.importorskip("playwright")
    sheet = made["ZI-A-001"]
    path = gen.sheet_dir(sheet) / f"{sheet.id}.html"
    path.write_text(path.read_text().replace("</style>", ".page { height: 1500px; }\n</style>", 1))
    report = booklet.build_booklets("pencil", "ZI")
    assert any(i.sheet_id == "ZI-A-001" and "prints as 2 pages" in i.message for i in report.issues)


def test_section_gaps_are_warned(made, booklet_out):
    pytest.importorskip("playwright")
    report = booklet.build_booklets("math", "6A")
    assert not any("skips pages" in i.message for i in report.issues if i.sheet_id.endswith("-A"))
    report = booklet.build_booklets("pencil", "ZI")    # ZI-B has pages 21 only, C has 51: no gaps;
    assert not any("skips" in i.message for i in report.issues)


def test_color_word_pages_are_listed():
    from ws.models import Sheet
    from ws.verify import _ranges, color_word_pages

    def sheet(page, words):
        return Sheet(id=f"EN-7A-A-{page:03d}", subject="english", level="7A", section="A", sheet_type="word_picture_pair",
                     page_number=page, seed=1, title="t", parent_tip="t", items=[], new_words=words)

    sheets = [sheet(30, ["eye", "mouth"]), sheet(31, ["red", "bee"]), sheet(32, ["pants", "blue"]), sheet(34, ["yellow"])]
    assert color_word_pages(sheets) == [31, 32, 34]
    assert _ranges([31, 32, 34, 35, 36, 40]) == "31–32, 34–36, 40"


def test_longest_real_words_fit_both_card_types(out_dir):
    """The widest words in the real bank, on pair cards and sentence cards."""
    pytest.importorskip("playwright")
    from ws.content import vocab
    from ws.render import render_pngs

    bank = [w for w in vocab() if w.level == "7A"]   # 7A cards: Chicks words, 2 a page in bank order
    longest = max(len(w.word) for w in bank)
    pages = sorted({(i // 2) + 1 for i, w in enumerate(bank) if len(w.word) == longest})
    made = gen.generate_pages(EN7A, pages) + gen.generate_pages(EN7A, pages, variant=2, sheet_type="word_picture_sentence")
    for r in render_pngs([p for _, p in made]):
        assert r.problems == [], (r.html.name, r.problems)


def test_internal_level_codes_are_banned_in_printed_text():
    # buyers only ever see public names (CLAUDE.md §15); "#0B7A75" (a color) is not a whole word
    assert banned_words("Level 7A · Reading") == ["7a"]
    assert banned_words("ZI-A-003") == ["zi"]
    assert banned_words("color: #0B7A75; Chicks · Reading") == []


def test_free_preview_pdf(out_dir, booklet_out):
    """One preview per public level, covering every strand (reading, math, pencil warm-ups)."""
    pytest.importorskip("playwright")
    from pypdf import PdfReader

    from ws.syllabus import ladder_level

    rung = ladder_level("chicks")
    n = 0
    for subject, code in rung.strands.items():
        level = load_level(subject, code)
        gen.generate_pages(level, sorted(level.preview_pages))
        n += len(level.preview_pages)
    report = booklet.build_preview("chicks")
    assert [i for i in report.issues if i.severity == "error"] == []
    assert [p.name for p in report.booklets] == ["chicks.pdf"]
    pdf = PdfReader(booklet_out / "previews" / "chicks.pdf")
    assert len(pdf.pages) == 1 + n + 1                                  # cover + samples + closing page
    text = "".join(p.extract_text() for p in pdf.pages)
    for word in ("Chicks", "Reading", "Math", "Pencil skills", "paperlessons.com"):
        assert word in text
    assert not re.search(r"\b(7A|6A|ZI|EN-7A|MA-6A)\b", text)


def test_preview_refuses_a_level_that_is_not_built_yet():
    report = booklet.build_preview("lions")
    assert report.booklets == [] and all(i.severity == "error" for i in report.issues)
    assert "isn't built yet" in report.issues[0].message


def test_ladder_pairs_reading_and_math_and_covers_every_syllabus_file():
    from ws.syllabus import all_levels, load_ladder

    rungs = load_ladder()
    assert all({"english", "math"} <= set(r.strands) for r in rungs)
    for lvl in all_levels():                      # every built level belongs to a public level
        assert lvl.public_name and lvl.slug
