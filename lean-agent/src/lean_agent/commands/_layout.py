from pathlib import Path


class LegacyHomeLayoutError(RuntimeError):
    """Raised when ~/.lean-personas/ or ~/lean-projects/ still exist post-v0.1.1.

    This is a one-shot upgrade-path helper. Removable in v0.2 once we trust
    nobody is left on legacy paths.
    """


def check_legacy_layout() -> None:
    legacy_personas = Path.home() / ".lean-personas"
    legacy_projects = Path.home() / "lean-projects"
    detected = [p for p in (legacy_personas, legacy_projects) if p.exists()]
    if not detected:
        return

    mv_commands: list[str] = []
    if legacy_personas.exists():
        mv_commands.append("mv ~/.lean-personas ~/.lean-agent/personas")
    if legacy_projects.exists():
        mv_commands.append("mv ~/lean-projects ~/.lean-agent/projects")

    detected_str = ", ".join(str(p) for p in detected)
    mv_block = "\n  ".join(mv_commands)
    raise LegacyHomeLayoutError(
        "lean-agent v0.1.1 moved its home to ~/.lean-agent/. "
        f"Detected legacy paths: {detected_str}. "
        f"Run:\n  {mv_block}\n"
        "Then re-run your command. (One-time. See README §Upgrading from v0.1.0.)"
    )
