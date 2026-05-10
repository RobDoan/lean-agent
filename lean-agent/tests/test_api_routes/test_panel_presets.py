import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PERSONA_OK = """---
id: {pid}
name: {pid}
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


@pytest.fixture
def client_with_tmp_home(tmp_path: Path, monkeypatch):
    from lean_agent import api, paths
    from lean_agent.llm import StubLLMClient

    monkeypatch.setattr(paths, "lean_agent_home", lambda: tmp_path)
    personas_root = tmp_path / "personas"
    personas_root.mkdir()
    presets_root = personas_root / "_panel-presets"
    presets_root.mkdir()
    for pid in ("alice", "bob", "carol"):
        (personas_root / f"{pid}.md").write_text(PERSONA_OK.format(pid=pid))
    (presets_root / "smb-saas.md").write_text("- alice\n- bob\n")

    stub = StubLLMClient()
    api.app.dependency_overrides[api.get_llm_client] = lambda: stub
    client = TestClient(api.app)
    yield client, stub, tmp_path
    api.app.dependency_overrides.clear()


def test_list_presets(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.get("/api/panel-presets")
    assert r.status_code == 200
    assert any(p["name"] == "smb-saas" for p in r.json())


def test_get_preset_detail(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.get("/api/panel-presets/smb-saas")
    assert r.status_code == 200
    body = r.json()
    assert body["persona_ids"] == ["alice", "bob"]


def test_get_preset_404(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.get("/api/panel-presets/ghost")
    assert r.status_code == 404


def test_post_preset_create(client_with_tmp_home):
    client, _, tmp_path = client_with_tmp_home
    r = client.post("/api/panel-presets", json={"name": "creator", "content": "- carol\n"})
    assert r.status_code == 201
    assert (tmp_path / "personas" / "_panel-presets" / "creator.md").exists()


def test_post_preset_409_on_existing(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.post("/api/panel-presets", json={"name": "smb-saas", "content": "- alice\n"})
    assert r.status_code == 409


def test_put_preset_edit(client_with_tmp_home):
    client, _, tmp_path = client_with_tmp_home
    r = client.put("/api/panel-presets/smb-saas", json={"content": "- alice\n- carol\n"})
    assert r.status_code == 200
    assert (tmp_path / "personas" / "_panel-presets" / "smb-saas.md").read_text() == "- alice\n- carol\n"


def test_delete_preset(client_with_tmp_home):
    client, _, tmp_path = client_with_tmp_home
    r = client.delete("/api/panel-presets/smb-saas")
    assert r.status_code == 204
    assert not (tmp_path / "personas" / "_panel-presets" / "smb-saas.md").exists()


def test_preset_draft_streams_sse(client_with_tmp_home):
    client, stub, _ = client_with_tmp_home
    stub.streaming_responses.append(["- alice\n- carol\n"])

    with client.stream("POST", "/api/panel-presets/draft",
                       json={"target_name": "smb-saas", "instruction": "swap bob for carol"}) as r:
        body = b"".join(r.iter_bytes()).decode()

    done_line = [line for line in body.split("\n") if line.startswith("data:") and "ok" in line][-1]
    data = json.loads(done_line[len("data: "):])
    assert data["ok"] is True
    assert "carol" in data["content"]


# ----- v0.3.2 auto-gen tests -----


def _parse_sse_events(raw: str) -> list[tuple[str, dict]]:
    """Parse raw SSE text into a list of (event_name, data_dict) tuples."""
    events = []
    event_name = None
    for line in raw.split("\n"):
        if line.startswith("event: "):
            event_name = line[len("event: "):]
        elif line.startswith("data: ") and event_name is not None:
            events.append((event_name, json.loads(line[len("data: "):])))
            event_name = None
    return events


def test_auto_gen_returns_plan_ready(client_with_tmp_home):
    client, stub, _ = client_with_tmp_home
    plan = {
        "description": "SMB SaaS founders panel",
        "reuse": ["alice"],
        "create": [{"slug": "dave", "name": "Dave", "description": "A CTO persona"}],
    }
    stub.responses.append(json.dumps(plan))

    with client.stream("POST", "/api/panel-presets/auto-gen",
                       json={"instruction": "build a SMB SaaS panel"}) as r:
        assert r.status_code == 200
        body = b"".join(r.iter_bytes()).decode()

    events = _parse_sse_events(body)
    event_names = [e[0] for e in events]
    assert "phase" in event_names
    assert "plan_ready" in event_names
    plan_data = next(d for n, d in events if n == "plan_ready")
    assert plan_data["plan"]["reuse"] == ["alice"]
    assert plan_data["plan"]["create"][0]["slug"] == "dave"


def test_auto_gen_llm_failure_returns_done_ok_false(client_with_tmp_home):
    client, stub, _ = client_with_tmp_home
    stub.responses.append("not valid json {{{")

    with client.stream("POST", "/api/panel-presets/auto-gen",
                       json={"instruction": "whatever"}) as r:
        body = b"".join(r.iter_bytes()).decode()

    events = _parse_sse_events(body)
    done_events = [(n, d) for n, d in events if n == "done"]
    assert len(done_events) == 1
    assert done_events[0][1]["ok"] is False
    assert done_events[0][1]["errors"]


def test_auto_gen_confirm_streams_persona_created_and_done(client_with_tmp_home):
    client, stub, tmp_path = client_with_tmp_home
    # Stub the LLM response for persona generation (one persona to create)
    stub.responses.append(PERSONA_OK.format(pid="dave"))

    plan = {
        "description": "Test panel",
        "reuse": ["alice"],
        "create": [{"slug": "dave", "name": "Dave", "description": "A CTO persona"}],
    }

    with client.stream("POST", "/api/panel-presets/auto-gen/confirm",
                       json={"plan": plan}) as r:
        assert r.status_code == 200
        body = b"".join(r.iter_bytes()).decode()

    events = _parse_sse_events(body)
    event_names = [e[0] for e in events]
    assert "persona_created" in event_names
    assert "done" in event_names
    created = next(d for n, d in events if n == "persona_created")
    assert created["slug"] == "dave"
    done = next(d for n, d in events if n == "done")
    assert done["ok"] is True
    assert "content" in done
    # Verify persona file was written to disk
    assert (tmp_path / "personas" / "dave.md").exists()
