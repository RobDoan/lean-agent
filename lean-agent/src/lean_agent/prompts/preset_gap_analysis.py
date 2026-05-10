"""System prompt + user-message envelope for gap-analysis of panel instructions.

The LLM decides which existing personas to reuse and which new ones to create
so a panel instruction can be fulfilled.
"""
from __future__ import annotations


_SYSTEM_PROMPT_TEMPLATE = """\
You are a gap-analysis assistant for the lean-agent tool. Given a panel
instruction and a set of available personas, you decide which existing personas
to reuse and which new ones must be created.

Available personas:
{persona_block}

Your job: analyse the user's panel instruction and return a JSON object with
exactly these keys:

  "description" -- a one-line summary of the panel's purpose (string).
  "reuse"       -- list of existing persona ids to include (may be empty).
  "create"      -- list of objects for personas that must be created. Each
                   object has keys "slug", "name", "description" (all strings).

Rules:
  - Reuse matching personas whenever possible; only create what is missing.
  - Every id in "reuse" MUST be one of the available persona ids listed above.
  - Slugs in "create" MUST match the pattern [a-z0-9][a-z0-9-]*[a-z0-9] (no
    leading/trailing hyphens, lowercase alphanumeric and hyphens only).
  - Total count (len(reuse) + len(create)) must be between 1 and 12 inclusive.
  - No duplicates: a slug in "create" must not duplicate any id in "reuse".
  - Output ONLY the JSON object. No explanation, no preamble, no code fences.
"""


def build_system_prompt(personas: list[dict]) -> str:
    """Build the system prompt with persona summaries injected.

    Each dict must have at least ``id``; ``name``, ``role``, ``income``, and
    ``location`` are optional and included when present.
    """
    lines: list[str] = []
    for p in sorted(personas, key=lambda x: x["id"]):
        parts = [p["id"]]
        for field in ("name", "role", "income", "location"):
            if field in p and p[field]:
                parts.append(f"{field}={p[field]}")
        lines.append("  " + ", ".join(parts))
    persona_block = "\n".join(lines) if lines else "  (none)"
    return _SYSTEM_PROMPT_TEMPLATE.format(persona_block=persona_block)


def build_user_message(instruction: str) -> str:
    """Wrap the panel instruction into the user-message envelope."""
    return (
        "<instruction>\n"
        f"{instruction}\n"
        "</instruction>\n"
    )
