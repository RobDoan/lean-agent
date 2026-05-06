"""Shared FastAPI dependency functions.

Extracted from api.py so that route modules can import `get_llm_client`
without creating a circular dependency:

    api.py → personas.py → api.py   (circular, breaks at module-init time)

Instead both api.py and route modules import from this module, which has no
upward dependency on either.
"""
from __future__ import annotations

from fastapi import Request

from lean_agent.llm import LLMClient


def get_llm_client(request: Request) -> LLMClient:
    """Dependency function — returns the app-scoped LLM client.

    Tests override via `app.dependency_overrides[get_llm_client] = lambda: StubLLMClient(...)`.
    """
    return request.app.state.llm_client
