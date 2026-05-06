import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Persona:
    id: str
    name: str
    metadata: dict[str, Any]
    backstory: str
    beliefs: str
    biases: str
    how_she_answers: str
    raw_path: Path | None  # None for in-memory parses (LLM output)


_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    m = _FRONTMATTER.match(text)
    if not m:
        raise ValueError("frontmatter missing or malformed")
    fm_block, body = m.group(1), m.group(2)
    meta: dict[str, Any] = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


def _section(body: str, heading: str) -> str:
    pat = re.compile(
        rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pat.search(body)
    return m.group(1).strip() if m else ""


def _build_persona(text: str, raw_path: Path | None) -> Persona:
    # Normalise Windows CRLF endings to LF so the frontmatter regex
    # (which expects "\n") matches consistently across platforms.
    text = text.replace("\r\n", "\n")
    meta, body = _parse_frontmatter(text)
    return Persona(
        id=meta["id"],
        name=meta.get("name", meta["id"]),
        metadata=meta,
        backstory=_section(body, "Backstory"),
        beliefs=_section(body, "Beliefs"),
        biases=_section(body, "Biases"),
        how_she_answers=_section(body, "How she answers questions"),
        raw_path=raw_path,
    )


def load_persona(path: Path) -> Persona:
    # utf-8-sig strips a BOM if present; _build_persona normalises CRLF endings.
    text = path.read_text(encoding="utf-8-sig")
    return _build_persona(text, raw_path=path)


def load_persona_from_str(text: str) -> Persona:
    """Parse persona content from a string (e.g. LLM output) without disk I/O."""
    return _build_persona(text, raw_path=None)


def load_all(root: Path) -> list[Persona]:
    if not root.exists():
        return []
    return [load_persona(p) for p in sorted(root.glob("*.md")) if not p.name.startswith("_")]
