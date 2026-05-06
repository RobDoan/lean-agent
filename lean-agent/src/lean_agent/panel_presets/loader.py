"""Panel-preset I/O — parse + validate against the available persona id set."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


MIN_PERSONAS = 1
MAX_PERSONAS = 12

_BULLET = re.compile(r"^\s*-\s*(\S+)\s*$", re.MULTILINE)


@dataclass
class Preset:
    name: str
    persona_ids: list[str]
    raw_path: Path | None  # None for in-memory parses (LLM output)


def _parse_bullets(text: str) -> list[str]:
    normalised = text.replace("\r\n", "\n")
    return _BULLET.findall(normalised)


def _validate(ids: list[str], available_ids: set[str]) -> None:
    if not (MIN_PERSONAS <= len(ids) <= MAX_PERSONAS):
        raise ValueError(
            f"preset must contain {MIN_PERSONAS} to {MAX_PERSONAS} personas; got {len(ids)}"
        )
    if len(set(ids)) != len(ids):
        seen: set[str] = set()
        dups = [i for i in ids if (i in seen) or seen.add(i)]  # type: ignore[func-returns-value]
        raise ValueError(f"duplicate persona ids: {sorted(set(dups))}")
    unknown = [i for i in ids if i not in available_ids]
    if unknown:
        raise ValueError(f"unknown persona ids: {sorted(set(unknown))}")


def load_preset(path: Path, *, available_ids: set[str]) -> Preset:
    text = path.read_text(encoding="utf-8-sig")
    ids = _parse_bullets(text)
    _validate(ids, available_ids)
    return Preset(name=path.stem, persona_ids=ids, raw_path=path)


def load_preset_from_str(text: str, *, name: str, available_ids: set[str]) -> Preset:
    """Parse preset content from a string (e.g. LLM output) without disk I/O."""
    ids = _parse_bullets(text)
    _validate(ids, available_ids)
    return Preset(name=name, persona_ids=ids, raw_path=None)


def list_preset_paths(root: Path) -> list[Path]:
    """Return all preset .md files under root, sorted, excluding underscore-prefixed."""
    if not root.exists():
        return []
    return sorted(p for p in root.glob("*.md") if not p.name.startswith("_"))
