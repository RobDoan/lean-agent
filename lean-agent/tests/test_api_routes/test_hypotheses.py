from pathlib import Path
from fastapi.testclient import TestClient
from tests.fixtures.fake_home import make_project

def _client():
    from lean_agent.api import app
    return TestClient(app)

def test_get_hypothesis_with_synthesis(tmp_home: Path) -> None:
    make_project(
        tmp_home,
        "p1",
        backlog=[("H1", "stmt1")],
        run_hypotheses=[("H1", "ran-1")],
        synthesised=["H1"],
        interviews={"H1": ["a", "b", "c"]},
    )
    client = _client()
    r = client.get("/api/projects/p1/hypotheses/H1")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "H1"
    assert body["title"] == "stmt1"
    assert body["synthesis_markdown"] is not None
    assert body["sprint_markdown"] is not None
    assert len(body["interviews"]) == 3
    names = sorted(i["name"] for i in body["interviews"])
    assert names == ["a", "b", "c"]

def test_get_hypothesis_run_without_synthesis(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")], run_hypotheses=[("H1", "ran")], synthesised=[])
    client = _client()
    r = client.get("/api/projects/p1/hypotheses/H1")
    assert r.status_code == 200
    body = r.json()
    assert body["synthesis_markdown"] is None
    assert body["sprint_markdown"] is not None

def test_get_hypothesis_backlog_only(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")])
    client = _client()
    r = client.get("/api/projects/p1/hypotheses/H1")
    assert r.status_code == 200
    body = r.json()
    assert body["synthesis_markdown"] is None
    assert body["sprint_markdown"] is None
    assert body["interviews"] == []

def test_get_hypothesis_404_when_not_in_backlog(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")])
    client = _client()
    r = client.get("/api/projects/p1/hypotheses/H99")
    assert r.status_code == 404

def test_get_hypothesis_422_on_malformed_hid(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")])
    client = _client()
    r = client.get("/api/projects/p1/hypotheses/notH")
    assert r.status_code == 422
