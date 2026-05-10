from pathlib import Path
import json

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


# --- gap-analysis parser (v0.3.2) ---


_AVAILABLE = {"alice", "bob", "carol"}


def _valid_gap_json(**overrides: object) -> str:
    base: dict = {
        "description": "A panel for testing",
        "reuse": ["alice"],
        "create": [{"slug": "dan-dev", "name": "Dan", "description": "A developer"}],
    }
    base.update(overrides)
    return json.dumps(base)


def test_parse_gap_analysis_valid_json():
    from lean_agent.commands.edit_preset import _parse_gap_analysis

    raw = _valid_gap_json()
    result = _parse_gap_analysis(raw, _AVAILABLE)

    assert result["description"] == "A panel for testing"
    assert result["reuse"] == ["alice"]
    assert len(result["create"]) == 1
    assert result["create"][0]["slug"] == "dan-dev"


def test_parse_gap_analysis_code_fence():
    from lean_agent.commands.edit_preset import _parse_gap_analysis

    raw = "```json\n" + _valid_gap_json() + "\n```"
    result = _parse_gap_analysis(raw, _AVAILABLE)

    assert result["reuse"] == ["alice"]
    assert result["create"][0]["slug"] == "dan-dev"


def test_parse_gap_analysis_unknown_reuse_id():
    from lean_agent.commands.edit_preset import _parse_gap_analysis
    from lean_agent.commands.errors import LLMOutputInvalid

    raw = _valid_gap_json(reuse=["ghost"])

    with pytest.raises(LLMOutputInvalid) as exc_info:
        _parse_gap_analysis(raw, _AVAILABLE)

    assert any("ghost" in e for e in exc_info.value.errors)


def test_parse_gap_analysis_invalid_slug():
    from lean_agent.commands.edit_preset import _parse_gap_analysis
    from lean_agent.commands.errors import LLMOutputInvalid

    raw = _valid_gap_json(
        create=[{"slug": "-bad-slug-", "name": "X", "description": "x"}],
    )

    with pytest.raises(LLMOutputInvalid) as exc_info:
        _parse_gap_analysis(raw, _AVAILABLE)

    assert any("slug" in e.lower() for e in exc_info.value.errors)


def test_parse_gap_analysis_total_over_12():
    from lean_agent.commands.edit_preset import _parse_gap_analysis
    from lean_agent.commands.errors import LLMOutputInvalid

    creates = [
        {"slug": f"p{i:02d}", "name": f"P{i}", "description": f"desc {i}"}
        for i in range(13)
    ]
    raw = _valid_gap_json(reuse=[], create=creates)

    with pytest.raises(LLMOutputInvalid) as exc_info:
        _parse_gap_analysis(raw, _AVAILABLE)

    assert any("1-12" in e for e in exc_info.value.errors)


def test_parse_gap_analysis_duplicate_reuse_and_create():
    from lean_agent.commands.edit_preset import _parse_gap_analysis
    from lean_agent.commands.errors import LLMOutputInvalid

    raw = _valid_gap_json(
        reuse=["alice"],
        create=[{"slug": "alice", "name": "Alice Dup", "description": "dup"}],
    )

    with pytest.raises(LLMOutputInvalid) as exc_info:
        _parse_gap_analysis(raw, _AVAILABLE)

    assert any("duplicate" in e.lower() for e in exc_info.value.errors)


# --- analyze_preset_gaps (v0.3.2) ---


def test_analyze_preset_gaps_success(tmp_path: Path):
    from lean_agent.commands.edit_preset import analyze_preset_gaps
    from lean_agent.llm import StubLLMClient

    personas_root, _ = _make_personas(tmp_path, ["alice", "bob"])

    gap_json = json.dumps({
        "description": "Test panel",
        "reuse": ["alice"],
        "create": [{"slug": "dan-dev", "name": "Dan", "description": "A developer"}],
    })
    client = StubLLMClient(responses=[gap_json])

    events = list(analyze_preset_gaps(
        instruction="build a tech panel",
        client=client,
        personas_root=personas_root,
    ))

    assert events[0] == {"kind": "phase", "phase": "analyzing"}
    assert events[1]["kind"] == "plan_ready"
    plan = events[1]["plan"]
    assert plan["description"] == "Test panel"
    assert plan["reuse"] == ["alice"]
    assert plan["create"][0]["slug"] == "dan-dev"


def test_analyze_preset_gaps_invalid_json(tmp_path: Path):
    from lean_agent.commands.edit_preset import analyze_preset_gaps
    from lean_agent.llm import StubLLMClient

    personas_root, _ = _make_personas(tmp_path, ["alice"])

    client = StubLLMClient(responses=["not valid json {{{"])

    events = list(analyze_preset_gaps(
        instruction="anything",
        client=client,
        personas_root=personas_root,
    ))

    assert events[0] == {"kind": "phase", "phase": "analyzing"}
    assert events[1]["kind"] == "done"
    assert events[1]["ok"] is False
    assert len(events[1]["errors"]) >= 1


# --- execute_preset_plan (v0.3.2) ---


def _persona_md(slug: str, name: str) -> str:
    return (
        f"---\nid: {slug}\nname: {name}\n---\n\n"
        "## Backstory\nx\n"
        "## Beliefs\nx\n"
        "## Biases\nx\n"
        "## How she answers questions\nx\n"
    )


def test_execute_preset_plan_creates_personas_and_preset(tmp_path: Path):
    from lean_agent.commands.edit_preset import execute_preset_plan
    from lean_agent.llm import StubLLMClient

    personas_root, presets_root = _make_personas(tmp_path, ["alice"])

    plan = {
        "description": "My test panel",
        "reuse": ["alice"],
        "create": [
            {"slug": "dan-dev", "name": "Dan", "description": "A developer"},
            {"slug": "eve-eng", "name": "Eve", "description": "An engineer"},
        ],
    }

    client = StubLLMClient(responses=[
        _persona_md("dan-dev", "Dan"),
        _persona_md("eve-eng", "Eve"),
    ])

    events = list(execute_preset_plan(
        plan=plan,
        client=client,
        personas_root=personas_root,
        presets_root=presets_root,
    ))

    # Expected event sequence
    kinds = [e["kind"] for e in events]
    assert kinds == [
        "phase",           # generating_persona 1
        "persona_created", # dan-dev
        "phase",           # generating_persona 2
        "persona_created", # eve-eng
        "phase",           # composing
        "done",
    ]

    # Verify persona files written to disk
    assert (personas_root / "dan-dev.md").exists()
    assert (personas_root / "eve-eng.md").exists()

    # Verify persona_created events
    assert events[1] == {"kind": "persona_created", "slug": "dan-dev", "name": "Dan"}
    assert events[3] == {"kind": "persona_created", "slug": "eve-eng", "name": "Eve"}

    # Verify generating_persona phase events
    assert events[0]["persona_index"] == 1
    assert events[0]["persona_total"] == 2
    assert events[2]["persona_index"] == 2

    # Final done
    final = events[-1]
    assert final["ok"] is True
    assert final["content"] is not None


def test_execute_preset_plan_persona_validation_failure(tmp_path: Path):
    from lean_agent.commands.edit_preset import execute_preset_plan
    from lean_agent.llm import StubLLMClient

    personas_root, presets_root = _make_personas(tmp_path, ["alice"])

    plan = {
        "description": "Bad panel",
        "reuse": ["alice"],
        "create": [{"slug": "bad-one", "name": "Bad", "description": "x"}],
    }

    # Return invalid persona content (missing frontmatter)
    client = StubLLMClient(responses=["this is not a valid persona file"])

    events = list(execute_preset_plan(
        plan=plan,
        client=client,
        personas_root=personas_root,
        presets_root=presets_root,
    ))

    # Should emit phase, then done:false
    assert events[0]["kind"] == "phase"
    assert events[0]["phase"] == "generating_persona"
    assert events[1]["kind"] == "done"
    assert events[1]["ok"] is False
    assert len(events[1]["errors"]) >= 1


def test_execute_preset_plan_content_format(tmp_path: Path):
    from lean_agent.commands.edit_preset import execute_preset_plan
    from lean_agent.llm import StubLLMClient

    personas_root, presets_root = _make_personas(tmp_path, ["alice", "bob"])

    plan = {
        "description": "Tech team panel",
        "reuse": ["alice", "bob"],
        "create": [{"slug": "carol-cto", "name": "Carol", "description": "CTO"}],
    }

    client = StubLLMClient(responses=[_persona_md("carol-cto", "Carol")])

    events = list(execute_preset_plan(
        plan=plan,
        client=client,
        personas_root=personas_root,
        presets_root=presets_root,
    ))

    final = events[-1]
    assert final["ok"] is True

    content = final["content"]
    lines = content.strip().split("\n")
    assert lines[0] == "> Tech team panel"
    assert lines[1] == ""
    assert lines[2] == "- alice"
    assert lines[3] == "- bob"
    assert lines[4] == "- carol-cto"


# --- _force_frontmatter_id (v0.3.2 bug fix) ---


def test_force_frontmatter_id_replaces_id_in_frontmatter():
    from lean_agent.commands.edit_preset import _force_frontmatter_id

    content = "---\nid: new-persona\nname: Maria\n---\n\n## Backstory\nx\n"
    result = _force_frontmatter_id(content, "maria-gig-delivery")
    assert "id: maria-gig-delivery" in result
    assert "id: new-persona" not in result
    # Preserves the rest
    assert "name: Maria" in result


def test_force_frontmatter_id_replaces_llm_drifted_id():
    from lean_agent.commands.edit_preset import _force_frontmatter_id

    content = "---\nid: some-other-id\nname: Carlos\n---\n\n## Backstory\nx\n"
    result = _force_frontmatter_id(content, "carlos-rideshare")
    assert "id: carlos-rideshare" in result
    assert "id: some-other-id" not in result
