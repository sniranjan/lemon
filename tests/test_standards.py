"""The two-grades-ahead check (ws/standards.py, CLAUDE.md §8/§15), over the whole repo."""

import pytest

import ws.standards as st
from ws.models import Section
from ws.standards import check_ladder, grade_of, parse_content_grade, section_grade
from ws.syllabus import all_levels


@pytest.mark.parametrize("code,grade", [
    ("K.CC.1", 0), ("3.OA.7", 3), ("RL.4.2", 4), ("L.K.5c", 0), ("RL.9-10.5", 9), ("W.9-10.9a", 9),
    ("6.RP.3a", 6), ("8.EE.7b", 8), ("RF.1.3b", 1),
    ("A-REI.4", 9), ("N-RN.A.1", 9), ("F-IF.B.6", 9), ("A-REI.B.4b", 9), ("HSN-RN.A.1", 9), ("HSA-SSE.A.2", 9), ("HSN.RN.A.1", 9),
])
def test_grade_of(code, grade):
    assert grade_of(code) == grade


@pytest.mark.parametrize("bad", ["", "XYZ", "RL.x.2", "Q-REI.4"])
def test_grade_of_rejects_junk(bad):
    with pytest.raises(ValueError):
        grade_of(bad)


@pytest.mark.parametrize("text,rng", [
    ("Pre-K", (-1, -1)), ("K", (0, 0)), ("K–1", (0, 1)), ("1–2", (1, 2)), ("1-2", (1, 2)), ("3", (3, 3)),
    ("9", (9, 9)),
])
def test_parse_content_grade(text, rng):
    assert parse_content_grade(text) == rng


def test_hs_codes_pass_the_syllabus_validator():
    s = Section(code="A", name="x", public_name="X", pages=[1, 10], sheet_types=["add_facts"],
                standards=["HSN-RN.A.1", "HSN.RN.A.1", "A-REI.4"])
    assert section_grade(s) == 9


def test_every_tag_has_a_grade():
    for lvl in all_levels():
        for s in lvl.sections:
            for code in st.section_codes(s):
                grade_of(code)


def test_whole_ladder_is_two_grades_ahead():
    issues, reports = check_ladder()
    errors = [f"{i.sheet_id}: {i.message}" for i in issues if i.severity == "error"]
    assert errors == []
    assert [r.public_name for r in reports if r.exempt] == ["Chicks"]
    for r in reports:
        if r.exempt:
            continue
        lo, hi = parse_content_grade(r.content_grade)
        assert r.highest >= hi, r.public_name
        if lo >= 3:   # Foxes on: every reading strand scores its passages against an fk_grade range
            assert r.fk, f"{r.public_name}: reading passages have no fk_grade range"
    # Cubs Read Aloud (english 2A-C) scores its passages too, so no "no Flesch-Kincaid range" warning remains
    assert next(r for r in reports if r.public_name == "Cubs").fk == {"2A": (2.0, 3.5)}
    assert not [i for i in issues if i.severity == "warning" and "Flesch-Kincaid" in i.message]


def _patched(monkeypatch, change):
    real = st.load_level
    monkeypatch.setattr(st, "load_level", lambda subject, code: change(subject, code, real(subject, code)))


def test_check_flags_a_low_section(monkeypatch):
    def lowered(subject, code, lvl):
        if (subject, code) != ("math", "M3"):
            return lvl
        secs = [s.model_copy(update={"standards": ["1.OA.6"],
                                     "parts": [p.model_copy(update={"standards": []}) for p in s.parts]})
                for s in lvl.sections]
        secs[0] = secs[0].model_copy(update={"on_ramp": True})
        return lvl.model_copy(update={"sections": secs})

    _patched(monkeypatch, lowered)
    issues, reports = check_ladder()
    msgs = [i.message for i in issues if i.severity == "error" and i.sheet_id == "Foxes"]
    assert any('"Times Tables 2, 5, 10" (M3-B)' in m and "more than one grade under" in m for m in msgs)
    assert not any("(M3-A)" in m for m in msgs)       # marked on_ramp
    foxes = next(r for r in reports if r.public_name == "Foxes")
    assert any("M3-A" in t and "on-ramp" in t for t in foxes.tagged)


def test_check_flags_short_reach_and_untagged(monkeypatch):
    def short(subject, code, lvl):
        if (subject, code) not in {("math", "M8"), ("english", "R8")}:
            return lvl
        secs = [s.model_copy(update={"standards": ["7.EE.1"],
                                     "parts": [p.model_copy(update={"standards": []}) for p in s.parts]})
                for s in lvl.sections]
        secs[-1] = secs[-1].model_copy(update={"standards": []})
        return lvl.model_copy(update={"sections": secs})

    _patched(monkeypatch, short)
    msgs = [i.message for i in check_ladder()[0] if i.severity == "error" and i.sheet_id == "Lions"]
    assert any("highest standard reaches grade 7, short of content grade 8" in m for m in msgs)
    assert any("no standards tagged" in m for m in msgs)


def test_fk_range_must_fit_content_grade(monkeypatch):
    def easy(subject, code, lvl):
        if (subject, code) == ("english", "R5"):
            return lvl.model_copy(update={"rules": {**lvl.rules, "fk_grade": [2.0, 4.0]}})
        if (subject, code) == ("english", "R6"):
            return lvl.model_copy(update={"rules": {k: v for k, v in lvl.rules.items() if k != "fk_grade"}})
        return lvl

    _patched(monkeypatch, easy)
    msgs = [f"{i.sheet_id}: {i.message}" for i in check_ladder()[0] if i.severity == "error"]
    assert any(m.startswith("Otters:") and "doesn't fit content grade 5" in m for m in msgs)
    assert any(m.startswith("Pandas:") and "no fk_grade rule" in m for m in msgs)
