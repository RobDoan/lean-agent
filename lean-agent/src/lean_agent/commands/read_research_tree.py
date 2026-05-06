"""Read-only orchestration: parse 00-hypothesis-list.md backlog + scan H<n>-*/ dirs."""
from __future__ import annotations

import re
from dataclasses import dataclass

from lean_agent import paths
from lean_agent.commands.errors import ProjectNotFoundError
from lean_agent.commands.list_projects import _IDEA_RE, _extract_backlog_section


_BACKLOG_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|\s*(H\d+)\s*\|\s*(.+?)\s*\|", re.MULTILINE
)

_TRIAGE_SECTION_RE = re.compile(
    r"## 1\. Idea Triage\s*\n(.*?)(?=\n## )", re.DOTALL
)
_TRIAGE_BULLET_RE = re.compile(r"^\s*-\s+(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class Hypothesis:
    id: str
    title: str
    has_run: bool
    has_synthesis: bool
    interview_count: int


@dataclass(frozen=True)
class ResearchTree:
    slug: str
    idea: str | None
    idea_triage: list[str]
    hypotheses: list[Hypothesis]


def read_research_tree(slug: str) -> ResearchTree:
    project_root = paths.project_dir(slug)
    if not project_root.exists():
        raise ProjectNotFoundError(slug)

    hyp_list = paths.hypothesis_list_path(slug)
    if not hyp_list.exists():
        return ResearchTree(slug=slug, idea=None, idea_triage=[], hypotheses=[])

    text = hyp_list.read_text()
    idea_m = _IDEA_RE.search(text)
    idea = idea_m.group(1).strip() if idea_m else None

    triage_section_m = _TRIAGE_SECTION_RE.search(text)
    idea_triage: list[str] = []
    if triage_section_m:
        idea_triage = [m.group(1).strip() for m in _TRIAGE_BULLET_RE.finditer(triage_section_m.group(1))]

    backlog_section = _extract_backlog_section(text)
    rows = list(_BACKLOG_ROW_RE.finditer(backlog_section))

    hypotheses: list[Hypothesis] = []
    for row in rows:
        hid = row.group(1)
        title = row.group(2).strip()
        hypotheses.append(_build_hypothesis(slug, hid, title))

    return ResearchTree(slug=slug, idea=idea, idea_triage=idea_triage, hypotheses=hypotheses)


def _build_hypothesis(slug: str, hid: str, title: str) -> Hypothesis:
    hdir = paths.hypothesis_dir_glob(slug, hid)
    has_run = hdir is not None
    has_synthesis = has_run and hdir is not None and (hdir / "synthesis.md").exists()
    interview_count = 0
    if has_run and hdir is not None:
        idir = hdir / "interviews"
        if idir.exists():
            interview_count = len(list(idir.glob("*.md")))
    return Hypothesis(
        id=hid,
        title=title,
        has_run=has_run,
        has_synthesis=has_synthesis,
        interview_count=interview_count,
    )
