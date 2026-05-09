from pathlib import Path

import pytest


def test_load_preset_parses_bullet_list(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "smb-saas.md"
    preset_path.write_text("- alice\n- bob\n- carol\n")

    preset = load_preset(preset_path, available_ids={"alice", "bob", "carol"})

    assert preset.name == "smb-saas"
    assert preset.persona_ids == ["alice", "bob", "carol"]
    assert preset.raw_path == preset_path


def test_load_preset_from_str_skips_disk_io():
    from lean_agent.panel_presets.loader import load_preset_from_str

    preset = load_preset_from_str("- alice\n- bob\n", name="x", available_ids={"alice", "bob"})

    assert preset.persona_ids == ["alice", "bob"]
    assert preset.raw_path is None


def test_load_preset_raises_on_unknown_persona_id(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "x.md"
    preset_path.write_text("- alice\n- ghost\n")

    with pytest.raises(ValueError, match="unknown persona ids: \\['ghost'\\]"):
        load_preset(preset_path, available_ids={"alice"})


def test_load_preset_raises_on_empty_list(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "x.md"
    preset_path.write_text("\n\n")

    with pytest.raises(ValueError, match="must contain 1 to 12"):
        load_preset(preset_path, available_ids={"alice"})


def test_load_preset_raises_on_too_many(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "x.md"
    preset_path.write_text("\n".join(f"- p{i}" for i in range(13)))

    available = {f"p{i}" for i in range(13)}
    with pytest.raises(ValueError, match="must contain 1 to 12"):
        load_preset(preset_path, available_ids=available)


def test_load_preset_raises_on_duplicates(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "x.md"
    preset_path.write_text("- alice\n- alice\n")

    with pytest.raises(ValueError, match="duplicate persona ids"):
        load_preset(preset_path, available_ids={"alice"})


def test_list_presets_excludes_underscore_files(tmp_path: Path):
    from lean_agent.panel_presets.loader import list_preset_paths

    (tmp_path / "smb-saas.md").write_text("- alice")
    (tmp_path / "_template_preset.md").write_text("- placeholder")
    (tmp_path / "creator.md").write_text("- bob")

    paths = list_preset_paths(tmp_path)
    names = sorted(p.name for p in paths)

    assert names == ["creator.md", "smb-saas.md"]


# --- description field (v0.3.1) ---


def test_load_preset_parses_description_blockquote(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "gig-workers.md"
    preset_path.write_text("> Low-income gig workers in US\n\n- alice\n- bob\n")

    preset = load_preset(preset_path, available_ids={"alice", "bob"})

    assert preset.description == "Low-income gig workers in US"
    assert preset.persona_ids == ["alice", "bob"]


def test_load_preset_no_description_backwards_compat(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "plain.md"
    preset_path.write_text("- alice\n- bob\n")

    preset = load_preset(preset_path, available_ids={"alice", "bob"})

    assert preset.description is None
    assert preset.persona_ids == ["alice", "bob"]


def test_load_preset_from_str_parses_description():
    from lean_agent.panel_presets.loader import load_preset_from_str

    text = "> SaaS founders panel\n\n- alice\n- bob\n"
    preset = load_preset_from_str(text, name="saas", available_ids={"alice", "bob"})

    assert preset.description == "SaaS founders panel"
    assert preset.persona_ids == ["alice", "bob"]


def test_load_preset_multiline_description(tmp_path: Path):
    from lean_agent.panel_presets.loader import load_preset

    preset_path = tmp_path / "multi.md"
    preset_path.write_text("> Line one\n> Line two\n\n- alice\n")

    preset = load_preset(preset_path, available_ids={"alice"})

    assert preset.description == "Line one\nLine two"
    assert preset.persona_ids == ["alice"]
