from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner


def test_resolve_slug_explicit_wins(tmp_home: Path):
    from lean_agent.cli import _resolve_slug
    from lean_agent.paths import projects_root
    from lean_agent.state import write_current_slug

    (projects_root() / "explicit-slug").mkdir(parents=True)
    (projects_root() / "stored-slug").mkdir(parents=True)
    write_current_slug("stored-slug")
    assert _resolve_slug("explicit-slug") == "explicit-slug"


def test_resolve_slug_falls_back_to_stored(tmp_home: Path):
    from lean_agent.cli import _resolve_slug
    from lean_agent.paths import projects_root
    from lean_agent.state import write_current_slug

    (projects_root() / "stored-slug").mkdir(parents=True)
    write_current_slug("stored-slug")
    assert _resolve_slug(None) == "stored-slug"


def test_resolve_slug_raises_when_neither_set(tmp_home: Path):
    from lean_agent.cli import _resolve_slug

    with pytest.raises(typer.BadParameter) as exc:
        _resolve_slug(None)
    assert "no project context" in str(exc.value)
    assert "--slug" in str(exc.value)
    assert "lean use" in str(exc.value)


def test_resolve_slug_raises_when_stored_project_missing(tmp_home: Path):
    from lean_agent.cli import _resolve_slug
    from lean_agent.state import write_current_slug

    write_current_slug("vanished")
    with pytest.raises(typer.BadParameter) as exc:
        _resolve_slug(None)
    msg = str(exc.value)
    assert "current project 'vanished' not found" in msg
    assert "lean use" in msg
    assert "--slug" in msg


def test_resolve_slug_raises_when_explicit_project_missing(tmp_home: Path):
    """Per design §3.1: an explicit --slug <ghost> for a non-existent project
    must produce a friendly typer.BadParameter, not a downstream FileNotFoundError."""
    from lean_agent.cli import _resolve_slug

    with pytest.raises(typer.BadParameter) as exc:
        _resolve_slug("ghost")
    msg = str(exc.value)
    assert "project 'ghost' not found" in msg
    assert "lean use list" in msg


def test_resolve_slug_raises_when_state_corrupt(tmp_home: Path):
    from lean_agent.cli import _resolve_slug
    from lean_agent.state import state_path

    state_path().parent.mkdir(parents=True)
    state_path().write_text("{not json", encoding="utf-8")
    with pytest.raises(typer.BadParameter) as exc:
        _resolve_slug(None)
    assert "corrupt" in str(exc.value)


def test_use_set_writes_state(tmp_home: Path):
    from lean_agent.cli import app
    from lean_agent.paths import projects_root
    from lean_agent.state import read_current_slug

    (projects_root() / "alpha").mkdir(parents=True)
    runner = CliRunner()
    result = runner.invoke(app, ["use", "alpha"])
    assert result.exit_code == 0, result.output
    assert read_current_slug() == "alpha"


def test_use_set_unknown_slug_fails(tmp_home: Path):
    from lean_agent.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["use", "does-not-exist"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_use_no_arg_prints_current(tmp_home: Path):
    from lean_agent.cli import app
    from lean_agent.paths import projects_root

    (projects_root() / "alpha").mkdir(parents=True)
    runner = CliRunner()
    runner.invoke(app, ["use", "alpha"])
    result = runner.invoke(app, ["use"])
    assert result.exit_code == 0
    assert "alpha" in result.output


def test_use_no_arg_prints_no_project_set_when_unset(tmp_home: Path):
    from lean_agent.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["use"])
    assert result.exit_code == 0
    assert "no project set" in result.stderr


def test_use_list_marks_current_with_star(tmp_home: Path):
    from lean_agent.cli import app
    from lean_agent.paths import projects_root

    for s in ("alpha", "beta", "gamma"):
        (projects_root() / s).mkdir(parents=True)
    runner = CliRunner()
    runner.invoke(app, ["use", "beta"])
    result = runner.invoke(app, ["use", "list"])
    assert result.exit_code == 0
    lines = [ln for ln in result.output.splitlines() if ln.strip()]
    assert lines == ["  alpha", "* beta", "  gamma"]


def test_use_list_no_star_when_no_current(tmp_home: Path):
    from lean_agent.cli import app
    from lean_agent.paths import projects_root

    (projects_root() / "alpha").mkdir(parents=True)
    runner = CliRunner()
    result = runner.invoke(app, ["use", "list"])
    assert result.exit_code == 0
    lines = [ln for ln in result.output.splitlines() if ln.strip()]
    assert lines == ["  alpha"]


def test_cli_aborts_when_legacy_personas_path_exists(tmp_home: Path):
    """If ~/.lean-personas/ still exists, the app-level callback aborts the run
    with a typer.BadParameter containing the mv command."""
    from lean_agent.cli import app

    (tmp_home / ".lean-personas").mkdir()
    runner = CliRunner()
    # Use any command that has no other prerequisites.
    result = runner.invoke(app, ["use"])
    assert result.exit_code != 0
    assert "mv ~/.lean-personas ~/.lean-agent/personas" in result.output


def test_cli_aborts_when_legacy_projects_path_exists(tmp_home: Path):
    from lean_agent.cli import app

    (tmp_home / "lean-projects").mkdir()
    runner = CliRunner()
    result = runner.invoke(app, ["use"])
    assert result.exit_code != 0
    assert "mv ~/lean-projects ~/.lean-agent/projects" in result.output


def test_cli_help_works_even_when_legacy_paths_exist(tmp_home: Path):
    """Click handles --help before the app-level callback runs, so --help must
    not be blocked by the legacy-layout check (resolves design Q1)."""
    from lean_agent.cli import app

    (tmp_home / ".lean-personas").mkdir()
    (tmp_home / "lean-projects").mkdir()
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # No migration message in the help output.
    assert "mv ~/.lean-personas" not in result.output
    assert "mv ~/lean-projects" not in result.output
