"""FastAPI app — second interface alongside the Typer CLI."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lean_agent import __version__, paths
from lean_agent.api_deps import get_llm_client  # noqa: F401 — re-exported for test overrides
from lean_agent.api_errors import register_exception_handlers
from lean_agent.api_routes import hypotheses, interviews, panel_presets, personas, projects
from lean_agent.api_schemas import HealthResponse
from lean_agent.llm import AnthropicLLMClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent template copy on first run.
    paths.ensure_templates()
    # Construct the LLM client once; routes get it via Depends(get_llm_client).
    app.state.llm_client = AnthropicLLMClient()
    yield


app = FastAPI(title="lean-agent API", version=__version__, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(interviews.router)
app.include_router(hypotheses.router)
app.include_router(personas.router)
app.include_router(panel_presets.router)
register_exception_handlers(app)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)
