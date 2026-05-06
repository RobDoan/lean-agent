import json
from pathlib import Path


class StateFileCorrupt(RuntimeError):
    """Raised when the state file exists but cannot be parsed as JSON."""


def state_path() -> Path:
    return Path.home() / ".lean-agent" / "state.json"


def read_current_slug() -> str | None:
    path = state_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise StateFileCorrupt(
            f"state file at {path} is corrupt — delete it or fix it manually"
        ) from e
    slug = data.get("current_slug")
    if not isinstance(slug, str) or not slug:
        return None
    return slug


def write_current_slug(slug: str) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"current_slug": slug}, indent=2) + "\n", encoding="utf-8")
