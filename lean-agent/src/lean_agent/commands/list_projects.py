"""Read-only orchestration: list projects in ~/.lean-agent/projects/ with summary stats."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from lean_agent import paths


_IDEA_RE = re.compile(r"^\s*\*\*Idea:\*\*\s+(.+?)\s*$", re.MULTILINE)
_BACKLOG_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|\s*(H\d+)\s*\|\s*(.+?)\s*\|", re.MULTILINE
)


@dataclass(frozen=True)
class Project:
    slug: str
    idea: str | None
    hypothesis_count: int
    run_count: int
    with_synthesis_count: int
    created_at: str  # ISO 8601


def list_projects() -> list[Project]:
    return [_build_project(slug) for slug in paths.list_project_slugs()]


def _build_project(slug: str) -> Project:
    project_root = paths.project_dir(slug)
    research = paths.research_dir(slug)
    hyp_list = paths.hypothesis_list_path(slug)

    idea: str | None = None
    backlog_ids: list[str] = []
    if hyp_list.exists():
        text = hyp_list.read_text()
        m = _IDEA_RE.search(text)
        if m:
            idea = m.group(1).strip()
        # Extract hypothesis IDs from the backlog table.
        backlog_section = _extract_backlog_section(text)
        backlog_ids = [m.group(1) for m in _BACKLOG_ROW_RE.finditer(backlog_section)]

    run_count = 0
    with_synthesis_count = 0
    if research.exists():
        for hid in backlog_ids:
            hdir = paths.hypothesis_dir_glob(slug, hid)
            if hdir is not None:
                run_count += 1
                if (hdir / "synthesis.md").exists():
                    with_synthesis_count += 1

    mtime = datetime.fromtimestamp(project_root.stat().st_mtime, tz=timezone.utc)
    return Project(
        slug=slug,
        idea=idea,
        hypothesis_count=len(backlog_ids),
        run_count=run_count,
        with_synthesis_count=with_synthesis_count,
        created_at=mtime.isoformat(),
    )


def _extract_backlog_section(text: str) -> str:
    """Return the slice of text under '## 2. Hypothesis Backlog' up to next '## ' heading."""
    start = text.find("## 2. Hypothesis Backlog")
    if start == -1:
        return ""
    end = text.find("\n## ", start + 1)
    return text[start:end] if end != -1 else text[start:]
