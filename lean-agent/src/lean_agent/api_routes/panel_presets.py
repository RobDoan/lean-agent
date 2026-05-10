"""Panel-preset routes — list / get / draft (SSE) / create / edit / delete / history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse

from lean_agent import paths
from lean_agent.api_deps import get_llm_client
from lean_agent.api_mappers import preset_to_detail_dto, preset_to_summary_dto
from lean_agent.api_routes._sse import sse
from lean_agent.api_schemas import (
    PresetAutoGenRequest,
    PresetConfirmRequest,
    PresetCreateRequest,
    PresetDetail,
    PresetDraftRequest,
    PresetEditRequest,
    PresetHistoryEntry,
    PresetSummary,
    PresetVersionContent,
)
from lean_agent.commands.edit_preset import (
    analyze_preset_gaps,
    commit_preset_create,
    commit_preset_edit,
    delete_preset,
    draft_preset_change,
    execute_preset_plan,
)
from lean_agent.commands.errors import PresetNotFound
from lean_agent.git_ops import commit_all, file_at_revision, file_history
from lean_agent.llm import LLMClient
from lean_agent.panel_presets.loader import (
    Preset,
    list_preset_paths,
    load_preset,
)
from lean_agent.personas.loader import load_all


router = APIRouter(prefix="/api/panel-presets", tags=["panel-presets"])


def _personas_root():
    return paths.lean_agent_home() / "personas"


def _presets_root():
    return _personas_root() / "_panel-presets"


def _available_ids() -> set[str]:
    return {p.id for p in load_all(_personas_root())}


@router.get("", response_model=list[PresetSummary])
def list_presets() -> list[PresetSummary]:
    available = _available_ids()
    summaries = []
    for path in list_preset_paths(_presets_root()):
        try:
            preset = load_preset(path, available_ids=available)
            summaries.append(preset_to_summary_dto(preset))
        except ValueError:
            # Tolerate partially-broken presets (e.g. one persona was deleted out-of-band);
            # surface them with persona_count=0 rather than 500-ing the whole list.
            summaries.append(preset_to_summary_dto(Preset(name=path.stem, persona_ids=[], raw_path=path)))
    return summaries


@router.get("/{preset_name}", response_model=PresetDetail)
def get_preset(preset_name: str) -> PresetDetail:
    path = _presets_root() / f"{preset_name}.md"
    if not path.exists():
        raise PresetNotFound(preset_name)
    raw = path.read_text(encoding="utf-8-sig")
    preset = load_preset(path, available_ids=_available_ids())
    return preset_to_detail_dto(preset, raw_content=raw)


@router.post("/draft")
def preset_draft(
    body: PresetDraftRequest,
    client: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    def gen():
        try:
            for event in draft_preset_change(
                target_name=body.target_name,
                instruction=body.instruction,
                client=client,
                personas_root=_personas_root(),
                presets_root=_presets_root(),
                current_content=body.current_content,
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


@router.post("", response_model=PresetDetail, status_code=201)
def post_preset_create(body: PresetCreateRequest) -> PresetDetail:
    preset = commit_preset_create(
        preset_name=body.name, content=body.content,
        personas_root=_personas_root(), presets_root=_presets_root(),
    )
    commit_all(paths.lean_agent_home(), f"preset: create {body.name}")
    return preset_to_detail_dto(preset, raw_content=body.content)


@router.put("/{preset_name}", response_model=PresetDetail)
def put_preset_edit(preset_name: str, body: PresetEditRequest) -> PresetDetail:
    preset = commit_preset_edit(
        preset_name=preset_name, content=body.content,
        personas_root=_personas_root(), presets_root=_presets_root(),
    )
    commit_all(paths.lean_agent_home(), f"preset: update {preset_name}")
    return preset_to_detail_dto(preset, raw_content=body.content)


@router.delete("/{preset_name}", status_code=204)
def delete_preset_route(preset_name: str) -> Response:
    delete_preset(preset_name=preset_name, presets_root=_presets_root())
    commit_all(paths.lean_agent_home(), f"preset: delete {preset_name}")
    return Response(status_code=204)


@router.post("/auto-gen")
def post_auto_gen(
    body: PresetAutoGenRequest,
    client: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    def gen():
        try:
            for event in analyze_preset_gaps(
                instruction=body.instruction,
                client=client,
                personas_root=_personas_root(),
            ):
                if event["kind"] == "phase":
                    yield sse("phase", {"phase": event["phase"]})
                elif event["kind"] == "plan_ready":
                    yield sse("plan_ready", {"plan": event["plan"]})
                elif event["kind"] == "done":
                    yield sse("done", {"ok": event["ok"], "errors": event.get("errors", [])})
        except Exception as exc:
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/auto-gen/confirm")
def post_auto_gen_confirm(
    body: PresetConfirmRequest,
    client: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    plan_dict = {
        "description": body.plan.description,
        "reuse": body.plan.reuse,
        "create": [
            {"slug": p.slug, "name": p.name, "description": p.description}
            for p in body.plan.create
        ],
    }

    def gen():
        try:
            for event in execute_preset_plan(
                plan=plan_dict,
                client=client,
                personas_root=_personas_root(),
                presets_root=_presets_root(),
            ):
                if event["kind"] == "phase":
                    yield sse("phase", event)
                elif event["kind"] == "persona_created":
                    yield sse("persona_created", {"slug": event["slug"], "name": event["name"]})
                elif event["kind"] == "done":
                    payload: dict = {"ok": event["ok"]}
                    if event.get("content"):
                        payload["content"] = event["content"]
                    if event.get("errors"):
                        payload["errors"] = event["errors"]
                    yield sse("done", payload)
        except Exception as exc:
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/{preset_name}/history", response_model=list[PresetHistoryEntry])
def get_preset_history(preset_name: str) -> list[PresetHistoryEntry]:
    path = _presets_root() / f"{preset_name}.md"
    if not path.exists():
        raise PresetNotFound(preset_name)
    repo_root = paths.lean_agent_home()
    rel = f"personas/_panel-presets/{preset_name}.md"
    entries = file_history(repo_root, rel)
    return [PresetHistoryEntry(**e) for e in entries]


@router.get("/{preset_name}/history/{sha}", response_model=PresetVersionContent)
def get_preset_version(preset_name: str, sha: str) -> PresetVersionContent:
    path = _presets_root() / f"{preset_name}.md"
    if not path.exists():
        raise PresetNotFound(preset_name)
    repo_root = paths.lean_agent_home()
    rel = f"personas/_panel-presets/{preset_name}.md"
    content = file_at_revision(repo_root, rel, sha)
    if content is None:
        raise PresetNotFound(f"{preset_name}@{sha}")
    return PresetVersionContent(sha=sha, content=content)
