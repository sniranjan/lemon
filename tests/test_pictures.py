import pytest

from ws.pictures import FILL_LIGHTNESS, check_pictures, check_svg_source


def test_all_pictures_pass_checks():
    pytest.importorskip("playwright")
    reports = check_pictures()
    assert reports, "no pictures found"
    assert {r.slug: r.problems for r in reports if r.problems} == {}


def test_pastel_fill_is_flagged(tmp_path, monkeypatch):
    pytest.importorskip("playwright")
    from ws import pictures

    (tmp_path / "pale.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<circle cx="50" cy="50" r="40" fill="#FBE38E" stroke="#222" stroke-width="3"/></svg>')
    monkeypatch.setattr(pictures, "PICTURES_DIR", tmp_path)
    monkeypatch.setattr(pictures, "licenses", lambda: {"pale": {}})
    (r,) = check_pictures(["pale"])
    assert r.main_fill == "#FBE38E" and r.lightness > FILL_LIGHTNESS[1]
    assert any("grayscale" in p for p in r.problems)


def test_svg_source_rules(tmp_path):
    bad = tmp_path / "bad.svg"
    bad.write_text('<svg viewBox="0 0 10 10"><style>x{}</style><text>hi</text></svg>')
    problems = check_svg_source(bad)
    assert len(problems) == 3


def test_color_swatches_skip_the_lightness_rule(tmp_path, monkeypatch):
    pytest.importorskip("playwright")
    from ws import pictures

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
           '<rect x="20" y="20" width="60" height="60" fill="#8E24AA" stroke="#222" stroke-width="3"/></svg>')
    (tmp_path / "dark.svg").write_text(svg)
    monkeypatch.setattr(pictures, "PICTURES_DIR", tmp_path)
    monkeypatch.setattr(pictures, "licenses", lambda: {"dark": {"kind": "color_swatch"}})
    (r,) = check_pictures(["dark"])
    assert r.main_fill == "#8E24AA" and r.problems == []
    monkeypatch.setattr(pictures, "licenses", lambda: {"dark": {}})
    (r,) = check_pictures(["dark"])
    assert any("darker than 30%" in p for p in r.problems)   # 27%: too dark for an ordinary picture
