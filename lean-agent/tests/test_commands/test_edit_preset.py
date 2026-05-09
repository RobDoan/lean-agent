from pathlib import Path

import pytest


PERSONA_OK = """---
id: alice
name: Alice
---

## Backstory
x
## Beliefs
x
## Biases
x
## How she answers questions
x
"""


def _make_personas(tmp_path: Path, ids: list[str]) -> tuple[Path, Path]:
    root = tmp_path / "personas"
    root.mkdir()
    for pid in ids:
        (root / f"{pid}.md").write_text(PERSONA_OK.replace("alice", pid))
    presets_root = root / "_panel-presets"
    presets_root.mkdir()
    return root, presets_root


def test_draft_preset_change_existing_streams_and_validates_ok(tmp_path: Path):
    from lean_agent.commands.edit_preset import draft_preset_change
    from lean_agent.llm import StubLLMClient

    personas_root, presets_root = _make_personas(tmp_path, ["alice", "bob"])
    (presets_root / "smb-saas.md").write_text("- alice\n")

    client = StubLLMClient(streaming_responses=[["- alice\n", "- bob\n"]])

    events = list(draft_preset_change(
        target_name="smb-saas", instruction="add bob",
        client=client, personas_root=personas_root, presets_root=presets_root,
    ))

    final = events[-1]
    assert final["kind"] == "done"
    assert final["ok"] is True
    assert "alice" in final["content"]
    assert "bob" in final["content"]


def test_draft_preset_change_invalid_persona_id(tmp_path: Path):
    from lean_agent.commands.edit_preset import draft_preset_change
    from lean_agent.llm import StubLLMClient

    personas_root, presets_root = _make_personas(tmp_path, ["alice"])
    (presets_root / "x.md").write_text("- alice")

    client = StubLLMClient(streaming_responses=[["- ghost\n"]])

    events = list(draft_preset_change(
        target_name="x", instruction="x",
        client=client, personas_root=personas_root, presets_root=presets_root,
    ))

    final = events[-1]
    assert final["ok"] is False
    assert any("ghost" in e for e in final["errors"])


def test_commit_preset_create_writes_file(tmp_path: Path):
    from lean_agent.commands.edit_preset import commit_preset_create

    personas_root, presets_root = _make_personas(tmp_path, ["alice", "bob"])

    preset = commit_preset_create(
        preset_name="smb-saas", content="- alice\n- bob\n",
        personas_root=personas_root, presets_root=presets_root,
    )

    assert (presets_root / "smb-saas.md").read_text() == "- alice\n- bob\n"
    assert preset.persona_ids == ["alice", "bob"]


def test_commit_preset_create_rejects_existing(tmp_path: Path):
    from lean_agent.commands.edit_preset import commit_preset_create
    from lean_agent.commands.errors import PresetNameConflict

    personas_root, presets_root = _make_personas(tmp_path, ["alice"])
    (presets_root / "smb-saas.md").write_text("- alice")

    with pytest.raises(PresetNameConflict):
        commit_preset_create(
            preset_name="smb-saas", content="- alice",
            personas_root=personas_root, presets_root=presets_root,
        )


def test_commit_preset_edit_replaces_file(tmp_path: Path):
    from lean_agent.commands.edit_preset import commit_preset_edit

    personas_root, presets_root = _make_personas(tmp_path, ["alice", "bob"])
    (presets_root / "x.md").write_text("- alice")

    commit_preset_edit(
        preset_name="x", content="- alice\n- bob\n",
        personas_root=personas_root, presets_root=presets_root,
    )

    assert (presets_root / "x.md").read_text() == "- alice\n- bob\n"


def test_commit_preset_edit_missing_target(tmp_path: Path):
    from lean_agent.commands.edit_preset import commit_preset_edit
    from lean_agent.commands.errors import PresetNotFound

    personas_root, presets_root = _make_personas(tmp_path, ["alice"])

    with pytest.raises(PresetNotFound):
        commit_preset_edit(
            preset_name="ghost", content="- alice",
            personas_root=personas_root, presets_root=presets_root,
        )


def test_delete_preset(tmp_path: Path):
    from lean_agent.commands.edit_preset import delete_preset

    personas_root, presets_root = _make_personas(tmp_path, ["alice"])
    (presets_root / "x.md").write_text("- alice")

    delete_preset(preset_name="x", presets_root=presets_root)

    assert not (presets_root / "x.md").exists()


def test_delete_preset_missing(tmp_path: Path):
    from lean_agent.commands.edit_preset import delete_preset
    from lean_agent.commands.errors import PresetNotFound

    _, presets_root = _make_personas(tmp_path, [])

    with pytest.raises(PresetNotFound):
        delete_preset(preset_name="ghost", presets_root=presets_root)


# --- iterative refinement (v0.3.1) ---

def test_draft_preset_change_current_content_overrides_disk(tmp_path: Path):
    """When current_content is provided, LLM receives it instead of the file on disk."""
    from lean_agent.commands.edit_preset import draft_preset_change
    from lean_agent.llm import StubLLMClient

    personas_root, presets_root = _make_personas(tmp_path, ["alice", "bob"])
    (presets_root / "smb-saas.md").write_text("- alice\n")

    custom_content = "- alice\n- bob\n"
    client = StubLLMClient(streaming_responses=[["- alice\n- bob\n"]])

    list(draft_preset_change(
        target_name="smb-saas",
        instruction="keep as is",
        client=client,
        personas_root=personas_root,
        presets_root=presets_root,
        current_content=custom_content,
    ))

    sent_msg = client.streaming_calls[0].messages[0]["content"]
    assert "- bob" in sent_msg  # custom content used (has bob)
