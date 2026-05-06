"""Persona library routes — list / get / draft (SSE) / create / edit / delete."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse

from lean_agent import paths
from lean_agent.api_deps import get_llm_client
from lean_agent.api_mappers import persona_to_detail_dto, persona_to_summary_dto
from lean_agent.api_routes._sse import sse
from lean_agent.api_schemas import (
    PersonaCreateRequest,
    PersonaDetail,
    PersonaDraftRequest,
    PersonaEditRequest,
    PersonaSummary,
)
from lean_agent.commands.edit_persona import (
    commit_persona_create,
    commit_persona_edit,
    delete_persona,
    draft_persona_change,
)
from lean_agent.commands.errors import PersonaNotFound
from lean_agent.llm import LLMClient
from lean_agent.personas.loader import load_all, load_persona


router = APIRouter(prefix="/api/personas", tags=["personas"])


def _personas_root():
    return paths.lean_agent_home() / "personas"


def _presets_root():
    return _personas_root() / "_panel-presets"


@router.get("", response_model=list[PersonaSummary])
def list_personas() -> list[PersonaSummary]:
    return [persona_to_summary_dto(p) for p in load_all(_personas_root())]


@router.get("/{persona_id}", response_model=PersonaDetail)
def get_persona(persona_id: str) -> PersonaDetail:
    path = _personas_root() / f"{persona_id}.md"
    if not path.exists():
        raise PersonaNotFound(persona_id)
    raw = path.read_text(encoding="utf-8-sig")
    persona = load_persona(path)
    return persona_to_detail_dto(persona, raw_content=raw)


@router.post("/draft")
def persona_draft(
    body: PersonaDraftRequest,
    client: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    def gen():
        try:
            for event in draft_persona_change(
                target_id=body.target_id,
                instruction=body.instruction,
                client=client,
                personas_root=_personas_root(),
            ):
                if event["kind"] == "token":
                    yield sse("token", {"text": event["text"]})
                elif event["kind"] == "done":
                    payload = {"ok": event["ok"], "content": event["content"]}
                    if not event["ok"]:
                        payload["errors"] = event["errors"]
                    yield sse("done", payload)
        except Exception as exc:
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("", response_model=PersonaDetail, status_code=201)
def post_persona_create(body: PersonaCreateRequest) -> PersonaDetail:
    persona = commit_persona_create(
        persona_id=body.id, content=body.content, personas_root=_personas_root()
    )
    return persona_to_detail_dto(persona, raw_content=body.content)


@router.put("/{persona_id}", response_model=PersonaDetail)
def put_persona_edit(persona_id: str, body: PersonaEditRequest) -> PersonaDetail:
    persona = commit_persona_edit(
        persona_id=persona_id, content=body.content, personas_root=_personas_root()
    )
    return persona_to_detail_dto(persona, raw_content=body.content)


@router.delete("/{persona_id}", status_code=204)
def delete_persona_route(persona_id: str) -> Response:
    delete_persona(
        persona_id=persona_id,
        personas_root=_personas_root(),
        presets_root=_presets_root(),
    )
    return Response(status_code=204)
