"""§9.1 build-complete witness — full draft+commit cycle for each v0.3 flow.

One test per shape: persona-edit, persona-create, persona-delete (plain),
persona-delete-cascade, preset-edit, preset-create, preset-delete,
invalid-llm-output. Verifies file-on-disk contents after each cycle.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PERSONA_TEMPLATE = """---
id: {pid}
name: {name}
role: Tester
---

## Backstory
{name} backstory.
## Beliefs
- something
## Biases
- something
## How she answers questions
Direct.
"""


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    from lean_agent import api, paths
    from lean_agent.llm import StubLLMClient

    monkeypatch.setattr(paths, "lean_agent_home", lambda: tmp_path)
    personas_root = tmp_path / "personas"
    personas_root.mkdir()
    (personas_root / "_panel-presets").mkdir()
    (personas_root / "alice.md").write_text(PERSONA_TEMPLATE.format(pid="alice", name="Alice"))
    (personas_root / "bob.md").write_text(PERSONA_TEMPLATE.format(pid="bob", name="Bob"))

    stub = StubLLMClient()
    api.app.dependency_overrides[api.get_llm_client] = lambda: stub
    client = TestClient(api.app)
    yield client, stub, tmp_path
    api.app.dependency_overrides.clear()


def _consume_done(stream_response) -> dict:
    """Drain the SSE stream and return the last `done` event's data dict."""
    body = b"".join(stream_response.iter_bytes()).decode()
    lines = [line for line in body.split("\n") if line.startswith("data:")]
    # last data line should be the done event
    last = lines[-1][len("data: "):]
    return json.loads(last)


def test_persona_edit_full_cycle(env):
    client, stub, tmp_path = env
    new_content = PERSONA_TEMPLATE.format(pid="alice", name="Alice").replace("Direct.", "Indirect.")
    stub.streaming_responses.append([new_content])

    with client.stream("POST", "/api/personas/draft",
                       json={"target_id": "alice", "instruction": "make her indirect"}) as r:
        done = _consume_done(r)
    assert done["ok"]

    r2 = client.put("/api/personas/alice", json={"content": done["content"]})
    assert r2.status_code == 200

    on_disk = (tmp_path / "personas" / "alice.md").read_text()
    assert "Indirect." in on_disk


def test_persona_create_full_cycle(env):
    client, stub, tmp_path = env
    new_content = PERSONA_TEMPLATE.format(pid="carol", name="Carol")
    stub.streaming_responses.append([new_content])

    with client.stream("POST", "/api/personas/draft",
                       json={"target_id": None, "instruction": "create carol"}) as r:
        done = _consume_done(r)
    assert done["ok"]

    r2 = client.post("/api/personas", json={"id": "carol", "content": done["content"]})
    assert r2.status_code == 201

    assert (tmp_path / "personas" / "carol.md").exists()


def test_persona_delete_no_cascade(env):
    client, _, tmp_path = env
    r = client.delete("/api/personas/alice")
    assert r.status_code == 204
    assert not (tmp_path / "personas" / "alice.md").exists()


def test_persona_delete_cascade_blocks(env):
    client, _, tmp_path = env
    (tmp_path / "personas" / "_panel-presets" / "smb.md").write_text("- alice\n- bob\n")
    r = client.delete("/api/personas/alice")
    assert r.status_code == 409
    assert r.json()["referenced_by"] == ["smb"]
    assert (tmp_path / "personas" / "alice.md").exists()


def test_preset_edit_full_cycle(env):
    client, stub, tmp_path = env
    (tmp_path / "personas" / "_panel-presets" / "smb-saas.md").write_text("- alice\n")
    stub.streaming_responses.append(["- alice\n- bob\n"])

    with client.stream("POST", "/api/panel-presets/draft",
                       json={"target_name": "smb-saas", "instruction": "add bob"}) as r:
        done = _consume_done(r)
    assert done["ok"]

    r2 = client.put("/api/panel-presets/smb-saas", json={"content": done["content"]})
    assert r2.status_code == 200

    assert (tmp_path / "personas" / "_panel-presets" / "smb-saas.md").read_text() == "- alice\n- bob\n"


def test_preset_create_full_cycle(env):
    client, stub, tmp_path = env
    stub.streaming_responses.append(["- alice\n- bob\n"])

    with client.stream("POST", "/api/panel-presets/draft",
                       json={"target_name": None, "instruction": "panel for smb saas"}) as r:
        done = _consume_done(r)
    assert done["ok"]

    r2 = client.post("/api/panel-presets", json={"name": "smb-saas", "content": done["content"]})
    assert r2.status_code == 201
    assert (tmp_path / "personas" / "_panel-presets" / "smb-saas.md").exists()


def test_preset_delete_full_cycle(env):
    client, _, tmp_path = env
    (tmp_path / "personas" / "_panel-presets" / "x.md").write_text("- alice\n")
    r = client.delete("/api/panel-presets/x")
    assert r.status_code == 204
    assert not (tmp_path / "personas" / "_panel-presets" / "x.md").exists()


def test_invalid_llm_output_done_event_carries_errors(env):
    client, stub, tmp_path = env
    stub.streaming_responses.append(["totally invalid persona content"])

    with client.stream("POST", "/api/personas/draft",
                       json={"target_id": "alice", "instruction": "x"}) as r:
        done = _consume_done(r)

    assert done["ok"] is False
    assert done["errors"]
    # Verify nothing was written
    assert (tmp_path / "personas" / "alice.md").read_text() == PERSONA_TEMPLATE.format(pid="alice", name="Alice")
