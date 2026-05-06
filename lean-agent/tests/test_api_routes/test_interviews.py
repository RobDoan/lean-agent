from pathlib import Path
from fastapi.testclient import TestClient
from tests.fixtures.fake_home import make_project

def _client():
    from lean_agent.api import app
    return TestClient(app)

def test_get_interview_returns_markdown(tmp_home: Path) -> None:
    make_project(
        tmp_home,
        "p1",
        backlog=[("H1", "s1")],
        run_hypotheses=[("H1", "ran")],
        interviews={"H1": ["alex-2026-05-04"]},
    )
    client = _client()
    r = client.get("/api/projects/p1/hypotheses/H1/interviews/alex-2026-05-04")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "alex-2026-05-04"
    assert "Interview" in body["markdown"]

def test_get_interview_404_when_missing(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")], run_hypotheses=[("H1", "ran")])
    client = _client()
    r = client.get("/api/projects/p1/hypotheses/H1/interviews/nope")
    assert r.status_code == 404

def test_get_interview_validation_on_path_traversal(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")], run_hypotheses=[("H1", "ran")])
    client = _client()
    # Using ..%2F..%2Fetc%2Fpasswd often results in 404 because httpx normalizes the path 
    # before it reaches the FastAPI router regex validation.
    r = client.get("/api/projects/p1/hypotheses/H1/interviews/..%2F..%2Fetc%2Fpasswd")
    assert r.status_code in (404, 422)
