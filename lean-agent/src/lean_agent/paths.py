from importlib.resources import files
from pathlib import Path


def lean_agent_home() -> Path:
    return Path.home() / ".lean-agent"


def personas_root() -> Path:
    return lean_agent_home() / "personas"


def projects_root() -> Path:
    return lean_agent_home() / "projects"


def project_dir(slug: str) -> Path:
    return projects_root() / slug


def research_dir(slug: str) -> Path:
    return project_dir(slug) / "01-research"


def hypothesis_list_path(slug: str) -> Path:
    return research_dir(slug) / "00-hypothesis-list.md"


def hypothesis_dir(slug: str, hypothesis_id: str, hypothesis_slug: str) -> Path:
    return research_dir(slug) / f"{hypothesis_id}-{hypothesis_slug}"


def project_roadmap_path(slug: str) -> Path:
    return project_dir(slug) / "ROADMAP.md"


def project_readme_path(slug: str) -> Path:
    return project_dir(slug) / "README.md"


def list_project_slugs() -> list[str]:
    root = projects_root()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def hypothesis_dir_glob(slug: str, hypothesis_id: str) -> Path | None:
    """Find the H<n>-*/ dir for a hypothesis. Returns the first sorted match, or None."""
    research = research_dir(slug)
    if not research.exists():
        return None
    matches = sorted(research.glob(f"{hypothesis_id}-*"))
    return matches[0] if matches else None


def interviews_dir(slug: str, hypothesis_dir_name: str) -> Path:
    """Path to the interviews/ subdir under an H<n>-*/ dir."""
    return research_dir(slug) / hypothesis_dir_name / "interviews"


def interview_path(slug: str, hypothesis_dir_name: str, interview_name: str) -> Path:
    """Path to a single interview file (markdown). interview_name MUST NOT include the .md suffix."""
    return interviews_dir(slug, hypothesis_dir_name) / f"{interview_name}.md"


def ensure_templates() -> None:
    """Copy ship-with-package template starters into ~/.lean-agent/personas/ if absent.

    Idempotent — only copies files that don't exist. Safe to run on every app
    startup. Reads templates via importlib.resources so the package can be
    installed as a wheel (no path-relative dependency).
    """
    home = lean_agent_home()
    personas_dir = home / "personas"
    personas_dir.mkdir(parents=True, exist_ok=True)

    package_root = files("lean_agent.personas")
    for filename in ("_template_persona.md", "_template_preset.md"):
        target = personas_dir / filename
        if target.exists():
            continue
        source = package_root / filename
        target.write_bytes(source.read_bytes())
