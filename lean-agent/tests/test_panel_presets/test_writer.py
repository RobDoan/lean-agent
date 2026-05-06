from pathlib import Path

import pytest


def test_atomic_write_creates_new_preset(tmp_path: Path):
    from lean_agent.panel_presets.writer import atomic_write_text

    target = tmp_path / "smb-saas.md"
    atomic_write_text(target, "- alice\n- bob\n")

    assert target.read_text() == "- alice\n- bob\n"


def test_atomic_write_overwrites_existing(tmp_path: Path):
    from lean_agent.panel_presets.writer import atomic_write_text

    target = tmp_path / "x.md"
    target.write_text("old")
    atomic_write_text(target, "new")

    assert target.read_text() == "new"


def test_atomic_write_cleans_temp_on_failure(tmp_path: Path, monkeypatch):
    from lean_agent.panel_presets import writer

    target = tmp_path / "x.md"
    target.write_text("original")

    monkeypatch.setattr(writer.os, "replace", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError, match="boom"):
        writer.atomic_write_text(target, "new")

    assert target.read_text() == "original"
    assert list(tmp_path.glob(".tmp_*")) == []


def test_delete_preset_removes_file(tmp_path: Path):
    from lean_agent.panel_presets.writer import delete_preset_file

    target = tmp_path / "x.md"
    target.write_text("x")

    delete_preset_file(target)

    assert not target.exists()


def test_delete_preset_raises_when_missing(tmp_path: Path):
    from lean_agent.panel_presets.writer import delete_preset_file

    with pytest.raises(FileNotFoundError):
        delete_preset_file(tmp_path / "missing.md")
