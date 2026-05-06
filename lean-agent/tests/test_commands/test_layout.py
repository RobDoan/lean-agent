from pathlib import Path

import pytest

from lean_agent.commands._layout import LegacyHomeLayoutError, check_legacy_layout


def test_check_passes_when_no_legacy_paths(tmp_home: Path):
    """Fresh-install case: neither legacy path exists, function returns silently."""
    check_legacy_layout()  # no raise == pass


def test_check_raises_when_legacy_personas_exists(tmp_home: Path):
    (tmp_home / ".lean-personas").mkdir()
    with pytest.raises(LegacyHomeLayoutError) as exc:
        check_legacy_layout()
    msg = str(exc.value)
    assert "mv ~/.lean-personas ~/.lean-agent/personas" in msg
    # Only the relevant mv command appears when only personas is legacy.
    assert "mv ~/lean-projects" not in msg


def test_check_raises_when_legacy_projects_exists(tmp_home: Path):
    (tmp_home / "lean-projects").mkdir()
    with pytest.raises(LegacyHomeLayoutError) as exc:
        check_legacy_layout()
    msg = str(exc.value)
    assert "mv ~/lean-projects ~/.lean-agent/projects" in msg
    assert "mv ~/.lean-personas" not in msg


def test_check_raises_with_both_mv_commands_when_both_legacy_paths_exist(tmp_home: Path):
    (tmp_home / ".lean-personas").mkdir()
    (tmp_home / "lean-projects").mkdir()
    with pytest.raises(LegacyHomeLayoutError) as exc:
        check_legacy_layout()
    msg = str(exc.value)
    assert "mv ~/.lean-personas ~/.lean-agent/personas" in msg
    assert "mv ~/lean-projects ~/.lean-agent/projects" in msg


def test_check_message_uses_tilde_notation_not_resolved_path(tmp_home: Path):
    """Per design §5.3: mv source paths use literal ~/ for shell-pasteability."""
    (tmp_home / ".lean-personas").mkdir()
    with pytest.raises(LegacyHomeLayoutError) as exc:
        check_legacy_layout()
    msg = str(exc.value)
    # The mv source uses ~/ literally — not the resolved tmp_home path.
    assert "mv ~/.lean-personas" in msg
    # The "Detected" line MAY render full paths (gives user concrete confirmation),
    # but the mv command line MUST NOT include the resolved tmp_home prefix in the source.
    # (We test this indirectly: a tmp-home-prefixed mv source would not match the literal substring above.)
