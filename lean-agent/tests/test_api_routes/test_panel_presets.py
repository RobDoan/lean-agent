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
