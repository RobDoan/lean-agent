"""Orchestration: prompt-driven panel-preset edits. Mirrors edit_persona.py."""
from __future__ import annotations

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
from lean_agent.personas.loader import load_all
from lean_agent.prompts.preset_edit import build_system_prompt, build_user_message


_FENCE_OUTER = re.compile(r"^```[a-z]*\n(.*)\n```\s*$", re.DOTALL)


def _strip_outer_fence(text: str) -> str:
    m = _FENCE_OUTER.match(text.strip())
    return m.group(1) if m else text


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
) -> Iterator[dict]:
    """Stream tokens from the LLM; yield {kind:"token",text} per chunk and a final {kind:"done",...}.

    target_name=None means create-mode (use empty template).
    """
    available = _available_ids(personas_root)

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
