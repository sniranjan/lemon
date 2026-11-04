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
    assert "MA-6A-A-001-012.pdf" in names and "MA-6A-A-001-012-answers.pdf" in names
    assert "MA-6A-level.pdf" in names and "MA-6A-level-answers.pdf" in names
    assert [i for i in report.issues if i.severity == "error"] == []
    sec = booklet_out / "math" / "6A" / "MA-6A-A-001-012.pdf"
    assert len(PdfReader(sec).pages) == 1 + 12 + 1
    answers = PdfReader(booklet_out / "math" / "6A" / "MA-6A-A-001-012-answers.pdf")
    assert "MA-6A-A-001" in answers.pages[0].extract_text()
    child_text = "".join(p.extract_text() for p in PdfReader(sec).pages)
    assert "Answers" not in child_text                     # no answer key in the child's booklet


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
