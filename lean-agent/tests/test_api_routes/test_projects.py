from pathlib import Path

from fastapi.testclient import TestClient

from tests.fixtures.fake_home import make_project


def _client():
    from lean_agent.api import app
    return TestClient(app)


def test_health(tmp_home: Path) -> None:
    client = _client()
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["version"]  # any non-empty string


def test_list_projects_empty(tmp_home: Path) -> None:
    client = _client()
    r = client.get("/api/projects")
    assert r.status_code == 200
    assert r.json() == []


def test_list_projects_returns_summaries(tmp_home: Path) -> None:
    make_project(tmp_home, "alpha", idea="A", backlog=[("H1", "s1")])
    make_project(tmp_home, "beta", idea="B")
    client = _client()
    r = client.get("/api/projects")
    assert r.status_code == 200
    body = r.json()
    slugs = [p["slug"] for p in body]
    assert slugs == ["alpha", "beta"]
    assert body[0]["idea"] == "A"
    assert body[0]["hypothesis_count"] == 1


def test_get_project_404_when_missing(tmp_home: Path) -> None:
    client = _client()
    r = client.get("/api/projects/nope")
    assert r.status_code == 404
    assert "nope" in r.json()["detail"]


def test_get_project_422_on_malformed_slug(tmp_home: Path) -> None:
    client = _client()
    r = client.get("/api/projects/UPPER_AND_UNDERSCORE")
    assert r.status_code == 422


def test_get_project_returns_detail(tmp_home: Path) -> None:
    make_project(
        tmp_home,
        "p1",
        idea="x",
        backlog=[("H1", "stmt1"), ("H2", "stmt2")],
        run_hypotheses=[("H1", "ran-1")],
        synthesised=["H1"],
    )
    client = _client()
    r = client.get("/api/projects/p1")
    assert r.status_code == 200
    body = r.json()
    assert body["slug"] == "p1"
    assert body["idea"] == "x"
    assert len(body["hypotheses"]) == 2
    assert body["hypotheses"][0]["has_synthesis"] is True
    assert body["hypotheses"][1]["has_run"] is False
