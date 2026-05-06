def test_cors_methods_include_post_put_delete():
    from lean_agent.api import app

    cors = next(m for m in app.user_middleware if "CORSMiddleware" in str(m.cls))
    methods = cors.kwargs["allow_methods"]
    assert set(methods) >= {"GET", "POST", "PUT", "DELETE"}


def test_get_llm_client_returns_app_state_value():
    from fastapi import FastAPI
    from lean_agent.api import get_llm_client
    from lean_agent.llm import StubLLMClient

    fake = StubLLMClient(responses=["x"])
    fake_app = FastAPI()
    fake_app.state.llm_client = fake

    class FakeRequest:
        app = fake_app

    assert get_llm_client(FakeRequest()) is fake  # type: ignore[arg-type]
