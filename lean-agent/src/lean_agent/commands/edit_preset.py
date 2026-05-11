"""Orchestration: prompt-driven panel-preset edits. Mirrors edit_persona.py."""
from __future__ import annotations

import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Iterator

from lean_agent.commands.errors import (
    LLMOutputInvalid,
    PresetNameConflict,
    PresetNotFound,
)
from lean_agent.llm import LLMClient, LLMRequest
from lean_agent.panel_presets.loader import Preset, load_preset_from_str
from lean_agent.panel_presets.writer import atomic_write_text, delete_preset_file
from lean_agent.personas.loader import load_all, load_persona_from_str
from lean_agent.personas.writer import atomic_write_text as atomic_write_persona
from lean_agent.prompts.persona_edit import SYSTEM_PROMPT as PERSONA_SYSTEM_PROMPT
from lean_agent.prompts.persona_edit import build_user_message as build_persona_user_message
from lean_agent.prompts.preset_edit import build_system_prompt, build_user_message
from lean_agent.prompts.preset_gap_analysis import (
    build_system_prompt as build_gap_system_prompt,
    build_user_message as build_gap_user_message,
)


_FENCE_OUTER = re.compile(r"^```[a-z]*\n(.*)\n```\s*$", re.DOTALL)


def _strip_outer_fence(text: str) -> str:
    m = _FENCE_OUTER.match(text.strip())
    return m.group(1) if m else text


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


def _parse_gap_analysis(raw: str, available_ids: set[str]) -> dict:
    """Parse and validate the LLM's gap-analysis JSON response.

    Returns the validated dict with keys ``description``, ``reuse``, ``create``.
    Raises ``LLMOutputInvalid`` on any parse or validation failure.
    """
    cleaned = _strip_outer_fence(raw).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMOutputInvalid([f"invalid JSON: {exc}"])

    errors: list[str] = []

    if not isinstance(data, dict):
        raise LLMOutputInvalid(["expected a JSON object"])

    # --- description ---
    if "description" not in data or not isinstance(data["description"], str):
        errors.append("missing or invalid 'description'")

    # --- reuse ---
    reuse = data.get("reuse", [])
    if not isinstance(reuse, list):
        errors.append("'reuse' must be a list")
        reuse = []
    for rid in reuse:
        if not isinstance(rid, str):
            errors.append(f"reuse id must be a string, got {type(rid).__name__}")
        elif rid not in available_ids:
            errors.append(f"reuse id not in available personas: {rid}")

    # --- create ---
    create = data.get("create", [])
    if not isinstance(create, list):
        errors.append("'create' must be a list")
        create = []
    for entry in create:
        if not isinstance(entry, dict):
            errors.append(f"create entry must be an object, got {type(entry).__name__}")
            continue
        slug = entry.get("slug", "")
        if not isinstance(slug, str) or not _SLUG_RE.match(slug):
            errors.append(f"invalid slug format: {slug!r}")
        for key in ("name", "description"):
            if key not in entry or not isinstance(entry[key], str):
                errors.append(f"create entry missing or invalid '{key}'")

    # --- cross-checks ---
    reuse_set = {r for r in reuse if isinstance(r, str)}
    create_slugs = [e.get("slug", "") for e in create if isinstance(e, dict)]
    create_set = set(create_slugs)

    overlap = reuse_set & create_set
    if overlap:
        errors.append(f"duplicate ids between reuse and create: {sorted(overlap)}")

    total = len(reuse) + len(create)
    if total < 1 or total > 12:
        errors.append(f"total persona count must be 1-12, got {total}")

    if errors:
        raise LLMOutputInvalid(errors)

    return {"description": data["description"], "reuse": reuse, "create": create}


def _preset_path(presets_root: Path, name: str) -> Path:
    return presets_root / f"{name}.md"


def _available_ids(personas_root: Path) -> set[str]:
    return {p.id for p in load_all(personas_root)}


def _read_template() -> str:
    return (files("lean_agent.personas") / "_template_preset.md").read_text(encoding="utf-8")


def _validate_content(content: str, name: str, available_ids: set[str]) -> Preset:
    try:
        return load_preset_from_str(content, name=name, available_ids=available_ids)
    except ValueError as e:
        raise LLMOutputInvalid([str(e)])


def draft_preset_change(
    *,
    target_name: str | None,
    instruction: str,
    client: LLMClient,
    personas_root: Path,
    presets_root: Path,
    current_content: str | None = None,
) -> Iterator[dict]:
    """Stream tokens from the LLM; yield {kind:"token",text} per chunk and a final {kind:"done",...}.

    target_name=None means create-mode (use empty template).
    current_content override: if provided, used as the baseline instead of disk/template
    (enables iterative refinement on unsaved drafts).
    """
    available = _available_ids(personas_root)

    if current_content is None:
        if target_name is not None:
            path = _preset_path(presets_root, target_name)
            if not path.exists():
                raise PresetNotFound(target_name)
            current_content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        else:
            current_content = _read_template()

    sys = build_system_prompt(available_ids=sorted(available))
    user_message = build_user_message(current_content=current_content, instruction=instruction)
    req = LLMRequest(system=sys, messages=[{"role": "user", "content": user_message}])

    buf: list[str] = []
    for chunk in client.complete_streaming(req):
        buf.append(chunk)
        yield {"kind": "token", "text": chunk}

    full = _strip_outer_fence("".join(buf))
    try:
        _validate_content(full, name=target_name or "new", available_ids=available)
        yield {"kind": "done", "ok": True, "content": full}
    except LLMOutputInvalid as e:
        yield {"kind": "done", "ok": False, "content": full, "errors": e.errors}


def commit_preset_create(
    *, preset_name: str, content: str, personas_root: Path, presets_root: Path,
) -> Preset:
    """Validate content and atomically write a new preset file.

    Raises PresetNameConflict if the name already exists.
    """
    path = _preset_path(presets_root, preset_name)
    if path.exists():
        raise PresetNameConflict(preset_name)
    preset = _validate_content(content, name=preset_name, available_ids=_available_ids(personas_root))
    atomic_write_text(path, content)
    return preset


def commit_preset_edit(
    *, preset_name: str, content: str, personas_root: Path, presets_root: Path,
) -> Preset:
    """Validate content and atomically overwrite an existing preset file.

    Raises PresetNotFound if the name does not exist.
    """
    path = _preset_path(presets_root, preset_name)
    if not path.exists():
        raise PresetNotFound(preset_name)
    preset = _validate_content(content, name=preset_name, available_ids=_available_ids(personas_root))
    atomic_write_text(path, content)
    return preset


def delete_preset(*, preset_name: str, presets_root: Path) -> None:
    """Delete the preset file. No cascade-check — presets are not referenced anywhere.

    Raises PresetNotFound if the file does not exist.
    """
    path = _preset_path(presets_root, preset_name)
    if not path.exists():
        raise PresetNotFound(preset_name)
    delete_preset_file(path)


# ---------------------------------------------------------------------------
# Multi-step orchestration (v0.3.2)
# ---------------------------------------------------------------------------


def analyze_preset_gaps(
    *,
    instruction: str,
    client: LLMClient,
    personas_root: Path,
) -> Iterator[dict]:
    """Step 1: ask the LLM to decide which personas to reuse / create.

    Yields events: ``phase:analyzing`` -> ``plan_ready`` | ``done:false``.
    """
    yield {"kind": "phase", "phase": "analyzing"}

    personas = load_all(personas_root)
    summaries = [
        {
            k: v
            for k, v in [
                ("id", p.id),
                ("name", p.name),
                ("role", p.metadata.get("role")),
                ("income", p.metadata.get("income")),
                ("location", p.metadata.get("location")),
            ]
            if v
        }
        for p in personas
    ]
    available_ids = {p.id for p in personas}

    sys = build_gap_system_prompt(summaries)
    user_msg = build_gap_user_message(instruction)
    req = LLMRequest(system=sys, messages=[{"role": "user", "content": user_msg}])

    try:
        resp = client.complete(req)
        plan = _parse_gap_analysis(resp.text, available_ids)
    except (LLMOutputInvalid, Exception) as exc:
        errors = exc.errors if isinstance(exc, LLMOutputInvalid) else [str(exc)]
        yield {"kind": "done", "ok": False, "errors": errors}
        return

    yield {"kind": "plan_ready", "plan": plan}


def execute_preset_plan(
    *,
    plan: dict,
    client: LLMClient,
    personas_root: Path,
    presets_root: Path,
) -> Iterator[dict]:
    """Steps 2+3: generate missing personas then compose the preset deterministically.

    Yields events: ``phase:generating_persona`` / ``persona_created`` per new
    persona, ``phase:composing``, and a final ``done``.
    """
    create_list: list[dict] = plan.get("create", [])
    reuse_ids: list[str] = list(plan.get("reuse", []))
    created_slugs: list[str] = []

    template = (files("lean_agent.personas") / "_template_persona.md").read_text(
        encoding="utf-8",
    )

    for i, entry in enumerate(create_list):
        slug: str = entry["slug"]
        try:
            yield {
                "kind": "phase",
                "phase": "generating_persona",
                "persona_index": i + 1,
                "persona_total": len(create_list),
                "persona_slug": slug,
            }

            instruction = (
                f"Create a persona named '{slug}'. {entry['description']}"
            )

            user_msg = build_persona_user_message(
                current_content=template,
                instruction=instruction,
            )
            req = LLMRequest(
                system=PERSONA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            resp = client.complete(req)
            content = _strip_outer_fence(resp.text)

            persona = load_persona_from_str(content, slug=slug)
            atomic_write_persona(personas_root / f"{slug}.md", content)
            created_slugs.append(slug)
            yield {"kind": "persona_created", "slug": slug, "name": persona.name}
        except Exception as exc:
            yield {"kind": "done", "ok": False, "errors": [str(exc)]}
            return

    # --- compose preset ---
    try:
        yield {"kind": "phase", "phase": "composing"}

        lines: list[str] = []
        description = plan.get("description")
        if description:
            lines.append(f"> {description}")
            lines.append("")

        all_ids = reuse_ids + created_slugs
        for pid in all_ids:
            lines.append(f"- {pid}")
        lines.append("")  # trailing newline
        content = "\n".join(lines)

        # Rebuild available ids including newly created personas
        available = _available_ids(personas_root)
        load_preset_from_str(content, name="new", available_ids=available)

        yield {"kind": "done", "ok": True, "content": content}
    except Exception as exc:
        yield {"kind": "done", "ok": False, "errors": [str(exc)]}
        return
