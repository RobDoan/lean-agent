from pathlib import Path

import pytest


def test_state_path_resolves_under_home(tmp_home: Path):
    from lean_agent.state import state_path

    assert state_path() == tmp_home / ".lean-agent" / "state.json"


def test_read_current_slug_returns_none_when_file_missing(tmp_home: Path):
    from lean_agent.state import read_current_slug

    assert read_current_slug() is None


def test_read_current_slug_returns_slug_when_present(tmp_home: Path):
    from lean_agent.state import read_current_slug, state_path

    state_path().parent.mkdir(parents=True)
    state_path().write_text('{"current_slug": "my-project"}', encoding="utf-8")
    assert read_current_slug() == "my-project"


def test_read_current_slug_returns_none_when_key_missing(tmp_home: Path):
    from lean_agent.state import read_current_slug, state_path

    state_path().parent.mkdir(parents=True)
    state_path().write_text("{}", encoding="utf-8")
    assert read_current_slug() is None


def test_read_current_slug_returns_none_when_empty_string(tmp_home: Path):
    from lean_agent.state import read_current_slug, state_path

    state_path().parent.mkdir(parents=True)
    state_path().write_text('{"current_slug": ""}', encoding="utf-8")
    assert read_current_slug() is None


def test_read_current_slug_raises_on_corrupt_json(tmp_home: Path):
    from lean_agent.state import read_current_slug, state_path, StateFileCorrupt

    state_path().parent.mkdir(parents=True)
    state_path().write_text("{not json", encoding="utf-8")
    with pytest.raises(StateFileCorrupt, match="corrupt"):
        read_current_slug()


def test_write_current_slug_creates_dir_and_file(tmp_home: Path):
    from lean_agent.state import write_current_slug, state_path

    write_current_slug("my-project")
    assert state_path().exists()
    assert state_path().parent == tmp_home / ".lean-agent"


def test_write_current_slug_round_trips(tmp_home: Path):
    from lean_agent.state import write_current_slug, read_current_slug

    write_current_slug("my-project")
    assert read_current_slug() == "my-project"


def test_write_current_slug_overwrites(tmp_home: Path):
    from lean_agent.state import write_current_slug, read_current_slug

    write_current_slug("a")
    write_current_slug("b")
    assert read_current_slug() == "b"
