from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app_with_handlers():
    from lean_agent.api_errors import register_exception_handlers
    from lean_agent.commands.errors import (
        LLMOutputInvalid,
        PersonaIdConflict,
        PersonaInUseByPreset,
        PersonaNotFound,
        PresetNameConflict,
        PresetNotFound,
    )

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise/persona-not-found")
    def r1():
        raise PersonaNotFound("alice")

    @app.get("/raise/persona-conflict")
    def r2():
        raise PersonaIdConflict("alice")

    @app.get("/raise/persona-in-use")
    def r3():
        raise PersonaInUseByPreset("alice", referenced_by=["smb-saas"])

    @app.get("/raise/preset-not-found")
    def r4():
        raise PresetNotFound("x")

    @app.get("/raise/preset-conflict")
    def r5():
        raise PresetNameConflict("x")

    @app.get("/raise/llm-invalid")
    def r6():
        raise LLMOutputInvalid(["frontmatter missing"])

    return app


def test_persona_not_found_returns_404():
    app = _app_with_handlers()
    client = TestClient(app)
    r = client.get("/raise/persona-not-found")
    assert r.status_code == 404
    assert "alice" in r.json()["detail"]


def test_persona_id_conflict_returns_409():
    app = _app_with_handlers()
    client = TestClient(app)
    r = client.get("/raise/persona-conflict")
    assert r.status_code == 409


def test_persona_in_use_returns_409_with_referenced_by():
    app = _app_with_handlers()
    client = TestClient(app)
    r = client.get("/raise/persona-in-use")
    assert r.status_code == 409
    body = r.json()
    assert body["referenced_by"] == ["smb-saas"]


def test_preset_not_found_returns_404():
    app = _app_with_handlers()
    client = TestClient(app)
    r = client.get("/raise/preset-not-found")
    assert r.status_code == 404


def test_preset_name_conflict_returns_409():
    app = _app_with_handlers()
    client = TestClient(app)
    r = client.get("/raise/preset-conflict")
    assert r.status_code == 409


def test_llm_output_invalid_returns_422_with_errors():
    app = _app_with_handlers()
    client = TestClient(app)
    r = client.get("/raise/llm-invalid")
    assert r.status_code == 422
    body = r.json()
    assert body["errors"] == ["frontmatter missing"]
