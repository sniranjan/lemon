import os
import shutil
from pathlib import Path

import pytest

from ws import content
from ws import generate as gen
from ws.syllabus import ROOT

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = Path(__file__).parent / "golden"


def _clear_content_caches():
    for f in (content.vocab, content.tips, content.licenses):
        f.cache_clear()


@pytest.fixture
def fixture_content(monkeypatch):
    """Use the fixed test word bank and tips instead of the real (growing) ones."""
    monkeypatch.setattr(content, "CONTENT_DIR", FIXTURES / "content")
    _clear_content_caches()
    yield
    _clear_content_caches()


@pytest.fixture
def out_dir(monkeypatch):
    """A scratch output tree inside the repo's out/ (git-ignored), like real output."""
    d = ROOT / "out" / "_pytest"
    shutil.rmtree(d, ignore_errors=True)
    monkeypatch.setattr(gen, "OUT_DIR", d)
    monkeypatch.setattr(gen, "MANIFEST", d / "manifest.jsonl")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def golden():
    """golden(name, text): compare with tests/golden/<name>; UPDATE_GOLDEN=1 rewrites it."""
    def check(name: str, text: str) -> None:
        path = GOLDEN / name
        if os.environ.get("UPDATE_GOLDEN") or not path.exists():
            path.write_text(text)
            if not os.environ.get("UPDATE_GOLDEN"):
                pytest.fail(f"golden file {name} did not exist; wrote it. Review it and re-run.")
        assert text == path.read_text(), f"{name} changed (UPDATE_GOLDEN=1 to accept)"
    return check
