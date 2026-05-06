"""Hand-rolled SSE wire-format helper. See library-notes.md "SSE — hand-rolled vs sse-starlette"."""
from __future__ import annotations

import json
from typing import Any


def sse(event: str, data: dict[str, Any]) -> str:
    """Format one SSE record: `event: <name>\\ndata: <json>\\n\\n`.

    JSON is utf-8 (ensure_ascii=False) so multibyte characters appear directly
    on the wire rather than as \\uXXXX escapes.
    """
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
