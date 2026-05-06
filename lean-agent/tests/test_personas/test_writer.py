from pathlib import Path

import pytest


def test_atomic_write_creates_new_file(tmp_path: Path):
    from lean_agent.personas.writer import atomic_write_text

    target = tmp_path / "alice.md"
    atomic_write_text(target, "hello")

    assert target.read_text() == "hello"


def test_atomic_write_overwrites_existing_file(tmp_path: Path):
    from lean_agent.personas.writer import atomic_write_text

    target = tmp_path / "alice.md"
    target.write_text("old content")
    atomic_write_text(target, "new content")

    assert target.read_text() == "new content"


def test_atomic_write_leaves_no_temp_files_on_success(tmp_path: Path):
    from lean_agent.personas.writer import atomic_write_text

    target = tmp_path / "alice.md"
    atomic_write_text(target, "hello")

    leftover = list(tmp_path.glob(".tmp_*"))
    assert leftover == []


def test_atomic_write_cleans_up_temp_on_failure(tmp_path: Path, monkeypatch):
    from lean_agent.personas import writer

    target = tmp_path / "alice.md"
    target.write_text("original")

    def boom(*args, **kwargs):
        raise RuntimeError("simulated mid-write failure")

    monkeypatch.setattr(writer.os, "replace", boom)

    with pytest.raises(RuntimeError, match="simulated"):
        writer.atomic_write_text(target, "new content")

    assert target.read_text() == "original"  # original preserved
    leftover = list(tmp_path.glob(".tmp_*"))
    assert leftover == []                     # temp cleaned up


def test_delete_persona_removes_file(tmp_path: Path):
    from lean_agent.personas.writer import delete_persona_file

    target = tmp_path / "alice.md"
    target.write_text("x")

    delete_persona_file(target)

    assert not target.exists()


def test_delete_persona_raises_when_missing(tmp_path: Path):
    from lean_agent.personas.writer import delete_persona_file

    target = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError):
        delete_persona_file(target)
