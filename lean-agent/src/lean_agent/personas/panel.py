import re
from pathlib import Path

from lean_agent.personas.loader import Persona, load_all


def resolve_panel(
    root: Path,
    *,
    ids: str | None = None,
    panel_name: str | None = None,
    n: int = 5,
) -> list[Persona]:
    """Pick a panel of personas by explicit ids, named preset, or default first-N."""
    available = {p.id: p for p in load_all(root)}

    if ids is not None:
        wanted = [s.strip() for s in ids.split(",") if s.strip()]
        missing = [w for w in wanted if w not in available]
        if missing:
            raise ValueError(f"missing personas: {missing}")
        return [available[w] for w in wanted]

    if panel_name is not None:
        preset_path = root / "_panel-presets" / f"{panel_name}.md"
        if not preset_path.exists():
            raise ValueError(f"panel preset not found: {panel_name}")
        ids_in_preset = re.findall(r"^\s*-\s*(\S+)", preset_path.read_text(), re.MULTILINE)
        missing = [i for i in ids_in_preset if i not in available]
        if missing:
            raise ValueError(f"missing personas: {missing}")
        return [available[i] for i in ids_in_preset]

    return list(available.values())[:n]
