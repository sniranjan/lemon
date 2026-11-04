import pytest
from typer.testing import CliRunner

from ws import registry
from ws.cli import app
from ws.exposure import ExposureTracker

runner = CliRunner()


def test_syllabus_show():
    r = runner.invoke(app, ["syllabus", "show", "math", "6A"])
    assert r.exit_code == 0, r.output
    assert "Counting up to 5" in r.output
    assert "MA-6A-B-001 … MA-6A-B-070" in r.output


def test_syllabus_show_unknown_level():
    r = runner.invoke(app, ["syllabus", "show", "math", "9Z"])
    assert r.exit_code == 1


@pytest.mark.parametrize("args", [
    ["vocab", "stats", "--level", "7A"],
])
def test_unbuilt_commands_exit_nonzero(args):
    r = runner.invoke(app, args)
    assert r.exit_code == 2
    assert "not implemented yet" in r.output


def test_register_rejects_names_outside_catalogue():
    with pytest.raises(ValueError, match="not in the catalogue"):
        registry.register("made_up_type")


def test_get_unimplemented_type():
    with pytest.raises(KeyError, match="not implemented yet"):
        registry.get("add_facts")


def test_exposure_word_is_new_once():
    ex = ExposureTracker()
    ex.add("apple", "new", page=1)
    ex.add("apple", "strip", page=4)
    ex.add("apple", "grid", page=101)
    assert ex.total("apple") == 3 and ex.new_on("apple") == 1
    with pytest.raises(ValueError, match="already new"):
        ex.add("apple", "new", page=9)


def test_pictures_missing_passes_for_bank():
    r = runner.invoke(app, ["pictures", "missing", "--subject", "english", "--level", "7A"])
    assert r.exit_code == 0, r.output
    assert "0 missing" in r.output
