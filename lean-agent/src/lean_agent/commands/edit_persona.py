"""Orchestration: prompt-driven persona edits.

draft_persona_change   — generator of {kind: "token"|"done", ...} events for SSE
commit_persona_create  — validate + atomic write (POST flow)
commit_persona_edit    — validate + atomic write (PUT flow)
delete_persona         — cascade-check against presets, then unlink

All functions take filesystem roots as parameters (no globals); the route
handler injects them from `paths.lean_agent_home()`.
"""
from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path
from typing import Iterator

from lean_agent.commands.errors import (
    LLMOutputInvalid,
    PersonaIdConflict,
    PersonaInUseByPreset,
    PersonaNotFound,
)
from lean_agent.llm import LLMClient, LLMRequest
from lean_agent.panel_presets.loader import list_preset_paths
from lean_agent.personas.loader import (
    Persona,
    load_persona_from_str,
)
from lean_agent.personas.writer import atomic_write_text, delete_persona_file
from lean_agent.prompts.persona_edit import SYSTEM_PROMPT, build_user_message


_FENCE_OUTER = re.compile(r"^```[a-z]*\n(.*)\n```\s*$", re.DOTALL)


def _strip_outer_fence(text: str) -> str:
    """If LLM wraps output in ```...```, strip exactly one outer fence pair."""
    m = _FENCE_OUTER.match(text.strip())
    return m.group(1) if m else text


def _persona_path(personas_root: Path, persona_id: str) -> Path:
    return personas_root / f"{persona_id}.md"


def _read_template() -> str:
    return (files("lean_agent.personas") / "_template_persona.md").read_text(encoding="utf-8")


def _validate_content(content: str) -> Persona:
    try:
        return load_persona_from_str(content)
    except (ValueError, KeyError) as e:
        raise LLMOutputInvalid([str(e)])


def draft_persona_change(
    *,
    target_id: str | None,
    instruction: str,
    client: LLMClient,
    personas_root: Path,
) -> Iterator[dict]:
    """Stream tokens from the LLM; yield {kind:"token",text} per chunk and a final {kind:"done",...}.

    target_id=None means create-mode (use empty template).
    """
    if target_id is not None:
        path = _persona_path(personas_root, target_id)
        if not path.exists():
            raise PersonaNotFound(target_id)
        current_content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    else:
        current_content = _read_template()

    user_message = build_user_message(
        current_content=current_content, instruction=instruction
    )
    req = LLMRequest(
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    buf: list[str] = []
    for chunk in client.complete_streaming(req):
        buf.append(chunk)
        yield {"kind": "token", "text": chunk}

    full = _strip_outer_fence("".join(buf))
    try:
        _validate_content(full)
        yield {"kind": "done", "ok": True, "content": full}
    except LLMOutputInvalid as e:
        yield {"kind": "done", "ok": False, "content": full, "errors": e.errors}


def commit_persona_create(
    *, persona_id: str, content: str, personas_root: Path,
) -> Persona:
    path = _persona_path(personas_root, persona_id)
    if path.exists():
        raise PersonaIdConflict(persona_id)
    persona = _validate_content(content)
    if persona.id != persona_id:
        raise LLMOutputInvalid(
            [f"id mismatch: URL id is {persona_id!r} but content frontmatter id is {persona.id!r}"]
        )
    atomic_write_text(path, content)
    return persona


def commit_persona_edit(
    *, persona_id: str, content: str, personas_root: Path,
) -> Persona:
    path = _persona_path(personas_root, persona_id)
    if not path.exists():
        raise PersonaNotFound(persona_id)
    persona = _validate_content(content)
    if persona.id != persona_id:
        raise LLMOutputInvalid(
            [f"id mismatch: URL id is {persona_id!r} but content frontmatter id is {persona.id!r}"]
        )
    atomic_write_text(path, content)
    return persona


def delete_persona(
    *, persona_id: str, personas_root: Path, presets_root: Path,
) -> None:
    path = _persona_path(personas_root, persona_id)
    if not path.exists():
        raise PersonaNotFound(persona_id)
    referenced_by = _find_referencing_presets(persona_id, presets_root)
    if referenced_by:
        raise PersonaInUseByPreset(persona_id, referenced_by=referenced_by)
    delete_persona_file(path)


_BULLET = re.compile(r"^\s*-\s*(\S+)\s*$", re.MULTILINE)


def _find_referencing_presets(persona_id: str, presets_root: Path) -> list[str]:
    """Return the names of all panel-presets whose bullet list contains persona_id."""
    if not presets_root.exists():
        return []
    referencing: list[str] = []
    for preset_path in list_preset_paths(presets_root):
        text = preset_path.read_text(encoding="utf-8-sig")
        ids = _BULLET.findall(text)
        if persona_id in ids:
            referencing.append(preset_path.stem)
    return sorted(referencing)
