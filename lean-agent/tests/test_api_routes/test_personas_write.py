import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PERSONA_OK = """---
id: alice
name: Alice
role: Tester
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
    (tmp_path / "personas").mkdir()
    (tmp_path / "personas" / "_panel-presets").mkdir()
    (tmp_path / "personas" / "alice.md").write_text(PERSONA_OK)

    stub = StubLLMClient()
    api.app.dependency_overrides[api.get_llm_client] = lambda: stub
    client = TestClient(api.app)
    yield client, stub, tmp_path
    api.app.dependency_overrides.clear()


def test_list_personas(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.get("/api/personas")
    assert r.status_code == 200
    assert any(p["id"] == "alice" for p in r.json())


def test_get_persona_detail(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.get("/api/personas/alice")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "alice"
    assert "raw_content" in body


def test_get_persona_detail_404(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.get("/api/personas/ghost")
    assert r.status_code == 404


def test_post_persona_create(client_with_tmp_home):
    client, _, tmp_path = client_with_tmp_home
    new = PERSONA_OK.replace("alice", "bob")
    r = client.post("/api/personas", json={"id": "bob", "content": new})
    assert r.status_code == 201
    assert (tmp_path / "personas" / "bob.md").exists()


def test_post_persona_create_409_on_existing(client_with_tmp_home):
    client, _, _ = client_with_tmp_home
    r = client.post("/api/personas", json={"id": "alice", "content": PERSONA_OK})
    assert r.status_code == 409


def test_put_persona_edit(client_with_tmp_home):
    client, _, tmp_path = client_with_tmp_home
    new = PERSONA_OK.replace("Tester", "Tested")
    r = client.put("/api/personas/alice", json={"content": new})
    assert r.status_code == 200
    assert "Tested" in (tmp_path / "personas" / "alice.md").read_text()


def test_delete_persona(client_with_tmp_home):
    client, _, tmp_path = client_with_tmp_home
    r = client.delete("/api/personas/alice")
    assert r.status_code == 204
    assert not (tmp_path / "personas" / "alice.md").exists()


def test_delete_persona_409_when_in_preset(client_with_tmp_home):
    client, _, tmp_path = client_with_tmp_home
    (tmp_path / "personas" / "_panel-presets" / "smb.md").write_text("- alice")
    r = client.delete("/api/personas/alice")
    assert r.status_code == 409
    assert r.json()["referenced_by"] == ["smb"]


def test_persona_draft_streams_sse(client_with_tmp_home):
    client, stub, _ = client_with_tmp_home
    stub.streaming_responses.append([PERSONA_OK])

    with client.stream("POST", "/api/personas/draft",
                       json={"target_id": "alice", "instruction": "no change"}) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        body = b"".join(r.iter_bytes()).decode()

    assert "event: token" in body
    assert "event: done" in body
    # Parse the done event's data
    done_line = [line for line in body.split("\n") if line.startswith("data:") and "ok" in line][-1]
    data = json.loads(done_line[len("data: "):])
    assert data["ok"] is True
    assert data["content"] == PERSONA_OK


def test_persona_draft_done_ok_false_on_invalid_output(client_with_tmp_home):
    client, stub, _ = client_with_tmp_home
    stub.streaming_responses.append(["invalid persona content"])

    with client.stream("POST", "/api/personas/draft",
                       json={"target_id": "alice", "instruction": "x"}) as r:
        body = b"".join(r.iter_bytes()).decode()

    done_line = [line for line in body.split("\n") if line.startswith("data:") and "ok" in line][-1]
    data = json.loads(done_line[len("data: "):])
    assert data["ok"] is False
    assert data["errors"]
