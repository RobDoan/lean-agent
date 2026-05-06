from pathlib import Path

import pytest


def test_set_current_raises_when_project_does_not_exist(tmp_home: Path):
    from lean_agent.commands.use import set_current, ProjectNotFound

    with pytest.raises(ProjectNotFound, match="not found"):
        set_current("does-not-exist")


def test_set_current_writes_state_when_project_exists(tmp_home: Path):
    from lean_agent.commands.use import set_current
    from lean_agent.paths import projects_root
    from lean_agent.state import read_current_slug

    (projects_root() / "alpha").mkdir(parents=True)
    set_current("alpha")
    assert read_current_slug() == "alpha"


def test_show_current_passes_through_state(tmp_home: Path):
    from lean_agent.commands.use import show_current
    from lean_agent.state import write_current_slug

    write_current_slug("alpha")
    assert show_current() == "alpha"


def test_show_current_returns_none_when_unset(tmp_home: Path):
    from lean_agent.commands.use import show_current

    assert show_current() is None


def test_list_available_returns_slugs_and_current(tmp_home: Path):
    from lean_agent.commands.use import list_available, set_current
    from lean_agent.paths import projects_root

    for s in ("alpha", "beta", "gamma"):
        (projects_root() / s).mkdir(parents=True)
    set_current("beta")
    slugs, current = list_available()
    assert slugs == ["alpha", "beta", "gamma"]
    assert current == "beta"


def test_list_available_returns_none_current_when_unset(tmp_home: Path):
    from lean_agent.commands.use import list_available
    from lean_agent.paths import projects_root

    (projects_root() / "alpha").mkdir(parents=True)
    slugs, current = list_available()
    assert slugs == ["alpha"]
    assert current is None
