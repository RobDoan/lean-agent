"""Small string-cleaning helpers shared across commands."""

import json
import re
from typing import Any


_JSON_FENCE = re.compile(r"^```(?:json)?\s*\n|\n```\s*$", re.MULTILINE)


def strip_json_fences(text: str) -> str:
    """Real LLMs sometimes wrap JSON in ```json … ``` fences. Strip them defensively."""
    return _JSON_FENCE.sub("", text.strip())


def parse_first_json_object(text: str) -> dict[str, Any]:
    """Parse the first JSON object out of `text`, ignoring leading/trailing prose.

    Real LLMs disobey "output strictly JSON" prompts — they wrap output in fences,
    prepend "Sure! Here's the JSON:", or append a paragraph of explanation after
    the closing brace. Bare `json.loads` fails on any of these with cryptic
    "Extra data" or "Expecting value" errors.

    This finds the first `{`, then uses JSONDecoder.raw_decode to parse exactly
    one valid JSON value and returns it. Anything before `{` and anything after
    the closing `}` is ignored.
    """
    cleaned = strip_json_fences(text).strip()
    start = cleaned.find("{")
    if start == -1:
        raise ValueError("no JSON object found in LLM response")
    decoder = json.JSONDecoder()
    obj, _end = decoder.raw_decode(cleaned[start:])
    if not isinstance(obj, dict):
        raise ValueError("first JSON value in LLM response was not an object")
    return obj
