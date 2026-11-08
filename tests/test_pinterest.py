"""Pinterest tooling: spec loading, text limits, links and the dry-run payload. No network, no rendering."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "marketing"))

# pin_make imports instagram_launch, which reads the site's synced ladder.json and pictures at import time.
if not (ROOT / "apps" / "web" / "src" / "data" / "ladder.json").exists():
    pytest.skip("run `npm run sync` in apps/web first (ladder.json missing)", allow_module_level=True)

import pin_make as M  # noqa: E402
import pin_publish as P  # noqa: E402

BATCH = ROOT / "marketing" / "pinterest" / "pins" / "batch-01.yaml"


def good_pin(**over) -> dict:
    pin = {
        "id": "test-pin", "board": "grade23", "level": "foxes", "strand": "math",
        "headline": "Times tables", "subline": "count by 2s",
        "pages": [{"level": "foxes", "page": 7}],
        "title": "Times Tables Worksheets | Grade 3 Math Printable",
        "description": "Printable times tables practice for grade 3 math. A few pages a day. Homeschool friendly.",
        "alt": "A times tables worksheet.",
    }
    pin.update(over)
    return pin


@pytest.fixture(scope="module")
def ctx():
    import yaml
    return yaml.safe_load(M.BOARDS.read_text()), M.L.banned_patterns()


def test_batch_loads_and_covers_every_level_and_strand():
    pins = M.load_batch(BATCH)
    assert 26 <= len(pins) <= 40
    have = {(p.get("level"), p.get("strand")) for p in pins}
    for slug in M.L.BY_SLUG:
        assert (slug, "reading") in have and (slug, "math") in have, slug
    assert sum(p["board"] == "gifts" for p in pins) >= 2
    for p in pins:
        assert len(p["title"]) <= 100 and len(p["description"]) <= 500 and len(p["alt"]) <= 500
        assert p["link"].startswith("https://paperlessons.com/")
        assert "utm_source=pinterest&utm_medium=pin" in p["link"]


def test_links(ctx):
    boards, pats = ctx
    lib = M.validate(good_pin(), boards, pats)["link"]
    assert lib == ("https://paperlessons.com/?utm_source=pinterest&utm_medium=pin&utm_campaign=foxes"
                   "&utm_content=test-pin#library")
    gift = M.validate(good_pin(link="gift", campaign="gift"), boards, pats)["link"]
    assert gift.startswith("https://paperlessons.com/gift?utm_source=pinterest") and "utm_campaign=gift" in gift
    with pytest.raises(M.SpecError):
        M.validate(good_pin(link="https://example.com/x"), boards, pats)


@pytest.mark.parametrize("over, message", [
    ({"title": "x" * 101}, "title"),
    ({"description": "y " * 260}, "description"),
    ({"alt": "z" * 501}, "alt"),
    ({"board": "nope"}, "unknown board"),
    ({"pages": [{"level": "foxes", "page": 1}]}, "preview cover"),
    ({"pages": [{"level": "foxes", "page": 10}]}, "closing page"),
    ({"title": "Grade 3 math from level M3"}, "banned"),
    ({"description": "Like Kumon, but printable."}, "banned"),
    ({"headline": "Favourite colours"}, "banned"),
    ({"description": "Only $19 a level."}, "banned"),
    ({"id": "Bad Id"}, "bad pin id"),
])
def test_rejects(ctx, over, message):
    boards, pats = ctx
    with pytest.raises(M.SpecError, match=message):
        M.validate(good_pin(**over), boards, pats)


def test_payload_is_pinterest_v5_pin_create():
    pin = {"id": "p", "title": "T", "description": "D", "link": "https://paperlessons.com/?a=b#library",
           "alt_text": "A", "board": "gifts"}
    body = P.pin_payload(pin, "123", "https://paperlessons.com/media/social/abc.jpg")
    assert body == {
        "board_id": "123", "title": "T", "description": "D", "link": "https://paperlessons.com/?a=b#library",
        "alt_text": "A", "media_source": {"source_type": "image_url", "url": "https://paperlessons.com/media/social/abc.jpg"},
    }
    with pytest.raises(ValueError):
        P.pin_payload({**pin, "title": "t" * 101}, "1", "https://x/y.jpg")


def test_dry_run_sends_nothing(monkeypatch, tmp_path, capsys):
    def no_network(*a, **k):
        raise AssertionError("dry run touched the network")

    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    monkeypatch.setattr(P.P, "host", lambda src, tmp, dry: "https://paperlessons.com/media/social/0123456789abcdef.jpg")
    monkeypatch.setattr(P, "LOG", tmp_path / "pinned.jsonl")
    monkeypatch.setattr(P, "BOARD_IDS", tmp_path / "boards.json")
    monkeypatch.delenv("PINTEREST_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("PINTEREST_SANDBOX", raising=False)
    monkeypatch.setattr(P, "read_env_file", lambda: {})
    manifest = json.loads(P.MANIFEST.read_text())["pins"] if P.MANIFEST.exists() else [{
        "id": "x", "board": "gifts", "image": "x.png", "title": "T", "description": "D",
        "link": "https://paperlessons.com/gift", "alt_text": "A"}]
    sent = P.publish(manifest, "production", dry_run=True, limit=2, only=None, force=False)
    out = capsys.readouterr().out
    assert sent == 0
    assert "POST https://api.pinterest.com/v5/pins" in out and "Bearer <redacted>" in out
    assert '"source_type": "image_url"' in out and "<id of board" in out
    assert out.count("POST https://") == 2
    assert not (tmp_path / "pinned.jsonl").exists()


def test_already_pinned_is_skipped_per_environment(monkeypatch, tmp_path, capsys):
    log = tmp_path / "pinned.jsonl"
    log.write_text(json.dumps({"id": "a", "env": "sandbox"}) + "\n")
    monkeypatch.setattr(P, "LOG", log)
    assert P.pinned_ids("sandbox") == {"a"} and P.pinned_ids("production") == set()
    pins = [{"id": "a"}]
    assert P.publish(pins, "sandbox", dry_run=True, limit=3, only=None, force=False) == 0
    assert "nothing to pin" in capsys.readouterr().out


def test_no_token_means_no_request(monkeypatch):
    monkeypatch.delenv("PINTEREST_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(P, "read_env_file", lambda: {})
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: pytest.fail("network"))
    with pytest.raises(SystemExit, match="no Pinterest token"):
        P.main(["--check"])
    monkeypatch.setenv("PINTEREST_SANDBOX", "1")
    assert P.environment() == "sandbox"
