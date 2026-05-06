from pathlib import Path

import pytest


PERSONA_OK = """---
id: alice
name: Alice
role: Tester
---

## Backstory
Story.

## Beliefs
- Beliefs.

## Biases
- Biases.

## How she answers questions
Direct.
"""


def _make_personas_root(tmp_path: Path) -> Path:
    root = tmp_path / "personas"
    root.mkdir()
    (root / "alice.md").write_text(PERSONA_OK)
    return root


# --- draft_persona_change ---

def test_draft_persona_change_existing_streams_and_validates_ok(tmp_path: Path):
    from lean_agent.commands.edit_persona import draft_persona_change
    from lean_agent.llm import StubLLMClient

    root = _make_personas_root(tmp_path)

    client = StubLLMClient(streaming_responses=[[PERSONA_OK[:50], PERSONA_OK[50:]]])

    chunks: list[str] = []
    final = None
    for event in draft_persona_change(
        target_id="alice",
        instruction="no change",
        client=client,
        personas_root=root,
    ):
        if event["kind"] == "token":
            chunks.append(event["text"])
        elif event["kind"] == "done":
            final = event

    assert "".join(chunks) == PERSONA_OK
    assert final is not None
    assert final["ok"] is True
    assert final["content"] == PERSONA_OK


def test_draft_persona_change_create_uses_template(tmp_path: Path):
    from lean_agent.commands.edit_persona import draft_persona_change
    from lean_agent.llm import StubLLMClient

    root = _make_personas_root(tmp_path)

    client = StubLLMClient(streaming_responses=[[PERSONA_OK]])

    list(draft_persona_change(
        target_id=None,  # create-mode
        instruction="create alice from scratch",
        client=client,
        personas_root=root,
    ))

    # The user-message that went to the LLM should embed the empty-template
    sent_msg = client.streaming_calls[0].messages[0]["content"]
    assert "<current_file>" in sent_msg
    assert "## Backstory" in sent_msg  # template has the section headings


def test_draft_persona_change_invalid_output_yields_done_not_ok(tmp_path: Path):
    from lean_agent.commands.edit_persona import draft_persona_change
    from lean_agent.llm import StubLLMClient

    root = _make_personas_root(tmp_path)

    client = StubLLMClient(streaming_responses=[["not valid persona content"]])

    events = list(draft_persona_change(
        target_id="alice",
        instruction="x",
        client=client,
        personas_root=root,
    ))

    final = events[-1]
    assert final["kind"] == "done"
    assert final["ok"] is False
    assert "errors" in final
    assert any("frontmatter" in e for e in final["errors"])


def test_draft_persona_change_strips_one_outer_fence(tmp_path: Path):
    """If the LLM disobeys and wraps output in ```markdown ... ```, strip it once."""
    from lean_agent.commands.edit_persona import draft_persona_change
    from lean_agent.llm import StubLLMClient

    root = _make_personas_root(tmp_path)

    fenced = f"```markdown\n{PERSONA_OK}\n```"
    client = StubLLMClient(streaming_responses=[[fenced]])

    events = list(draft_persona_change(
        target_id="alice", instruction="x", client=client,
        personas_root=root,
    ))

    final = events[-1]
    assert final["ok"] is True
    assert "```" not in final["content"]


def test_draft_persona_change_target_not_found(tmp_path: Path):
    from lean_agent.commands.edit_persona import draft_persona_change
    from lean_agent.commands.errors import PersonaNotFound
    from lean_agent.llm import StubLLMClient

    root = _make_personas_root(tmp_path)

    client = StubLLMClient(streaming_responses=[["x"]])

    with pytest.raises(PersonaNotFound):
        list(draft_persona_change(
            target_id="ghost", instruction="x", client=client,
            personas_root=root,
        ))


# --- commit_persona_create ---

def test_commit_persona_create_writes_file(tmp_path: Path):
    from lean_agent.commands.edit_persona import commit_persona_create

    root = tmp_path / "personas"
    root.mkdir()

    persona = commit_persona_create(persona_id="alice", content=PERSONA_OK, personas_root=root)

    assert (root / "alice.md").read_text() == PERSONA_OK
    assert persona.id == "alice"


def test_commit_persona_create_rejects_existing(tmp_path: Path):
    from lean_agent.commands.edit_persona import commit_persona_create
    from lean_agent.commands.errors import PersonaIdConflict

    root = _make_personas_root(tmp_path)

    with pytest.raises(PersonaIdConflict):
        commit_persona_create(persona_id="alice", content=PERSONA_OK, personas_root=root)


def test_commit_persona_create_rejects_invalid_content(tmp_path: Path):
    from lean_agent.commands.edit_persona import commit_persona_create
    from lean_agent.commands.errors import LLMOutputInvalid

    root = tmp_path / "personas"
    root.mkdir()

    with pytest.raises(LLMOutputInvalid):
        commit_persona_create(persona_id="alice", content="garbage", personas_root=root)


def test_commit_persona_create_rejects_id_mismatch(tmp_path: Path):
    """Frontmatter id must match URL id — no covert id substitution via POST."""
    from lean_agent.commands.edit_persona import commit_persona_create
    from lean_agent.commands.errors import LLMOutputInvalid

    root = tmp_path / "personas"
    root.mkdir()
    bad_content = PERSONA_OK.replace("id: alice", "id: bob")

    with pytest.raises(LLMOutputInvalid, match="id mismatch"):
        commit_persona_create(persona_id="alice", content=bad_content, personas_root=root)


# --- commit_persona_edit ---

def test_commit_persona_edit_replaces_file(tmp_path: Path):
    from lean_agent.commands.edit_persona import commit_persona_edit

    root = _make_personas_root(tmp_path)
    new_content = PERSONA_OK.replace("Direct.", "Indirect.")

    persona = commit_persona_edit(persona_id="alice", content=new_content, personas_root=root)

    assert "Indirect." in (root / "alice.md").read_text()
    assert persona.id == "alice"


def test_commit_persona_edit_rejects_id_mismatch(tmp_path: Path):
    """Frontmatter id must match URL id — no covert rename via PUT."""
    from lean_agent.commands.edit_persona import commit_persona_edit
    from lean_agent.commands.errors import LLMOutputInvalid

    root = _make_personas_root(tmp_path)
    bad_content = PERSONA_OK.replace("id: alice", "id: bob")

    with pytest.raises(LLMOutputInvalid, match="id mismatch"):
        commit_persona_edit(persona_id="alice", content=bad_content, personas_root=root)


def test_commit_persona_edit_rejects_missing_target(tmp_path: Path):
    from lean_agent.commands.edit_persona import commit_persona_edit
    from lean_agent.commands.errors import PersonaNotFound

    root = tmp_path / "personas"
    root.mkdir()

    with pytest.raises(PersonaNotFound):
        commit_persona_edit(persona_id="ghost", content=PERSONA_OK, personas_root=root)


# --- delete_persona ---

def test_delete_persona_removes_file(tmp_path: Path):
    from lean_agent.commands.edit_persona import delete_persona

    root = _make_personas_root(tmp_path)
    presets_root = tmp_path / "personas" / "_panel-presets"
    presets_root.mkdir()

    delete_persona(persona_id="alice", personas_root=root, presets_root=presets_root)

    assert not (root / "alice.md").exists()


def test_delete_persona_blocks_when_in_use(tmp_path: Path):
    from lean_agent.commands.edit_persona import delete_persona
    from lean_agent.commands.errors import PersonaInUseByPreset

    root = _make_personas_root(tmp_path)
    presets_root = tmp_path / "personas" / "_panel-presets"
    presets_root.mkdir()
    (presets_root / "smb-saas.md").write_text("- alice\n")
    (presets_root / "creator.md").write_text("- alice\n")

    with pytest.raises(PersonaInUseByPreset) as exc:
        delete_persona(persona_id="alice", personas_root=root, presets_root=presets_root)

    assert sorted(exc.value.referenced_by) == ["creator", "smb-saas"]
    assert (root / "alice.md").exists()  # not deleted


def test_delete_persona_raises_not_found_when_absent(tmp_path: Path):
    from lean_agent.commands.edit_persona import delete_persona
    from lean_agent.commands.errors import PersonaNotFound

    root = tmp_path / "personas"
    root.mkdir()
    presets_root = tmp_path / "personas" / "_panel-presets"
    presets_root.mkdir()

    with pytest.raises(PersonaNotFound):
        delete_persona(persona_id="ghost", personas_root=root, presets_root=presets_root)
