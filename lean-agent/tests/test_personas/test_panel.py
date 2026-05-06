from pathlib import Path

import pytest

from lean_agent.personas.panel import resolve_panel


def _make_persona(root: Path, pid: str) -> None:
    (root / f"{pid}.md").write_text(f"""---
id: {pid}
name: {pid.title()}
---

## Backstory
x
## Beliefs
- y
## Biases
- z
## How she answers questions
- w
""")


def test_resolve_panel_explicit_ids(tmp_path: Path):
    _make_persona(tmp_path, "sarah")
    _make_persona(tmp_path, "mike")
    _make_persona(tmp_path, "jamie")
    out = resolve_panel(tmp_path, ids="sarah,mike")
    assert [p.id for p in out] == ["sarah", "mike"]


def test_resolve_panel_default_first_n(tmp_path: Path):
    for pid in ["a", "b", "c", "d", "e", "f"]:
        _make_persona(tmp_path, pid)
    out = resolve_panel(tmp_path, n=4)
    assert len(out) == 4
    assert [p.id for p in out] == ["a", "b", "c", "d"]


def test_resolve_panel_named_preset(tmp_path: Path):
    _make_persona(tmp_path, "sarah")
    _make_persona(tmp_path, "mike")
    presets = tmp_path / "_panel-presets"
    presets.mkdir()
    (presets / "smb-saas.md").write_text("- sarah\n- mike\n")
    out = resolve_panel(tmp_path, panel_name="smb-saas")
    assert [p.id for p in out] == ["sarah", "mike"]


def test_resolve_panel_missing_id_raises(tmp_path: Path):
    _make_persona(tmp_path, "sarah")
    with pytest.raises(ValueError, match="missing personas"):
        resolve_panel(tmp_path, ids="sarah,ghost")
