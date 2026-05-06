"""Builder for synthesised ~/.lean-agent/ layouts in tests."""
from __future__ import annotations

from pathlib import Path


def make_project(
    home: Path,
    slug: str,
    *,
    idea: str | None = "test idea",
    idea_triage: list[str] | None = None,
    backlog: list[tuple[str, str]] | None = None,
    run_hypotheses: list[tuple[str, str]] | None = None,
    synthesised: list[str] | None = None,
    interviews: dict[str, list[str]] | None = None,
) -> Path:
    """Create a fake project under home/.lean-agent/projects/<slug>/.

    Args:
        home: tmp HOME path (from tmp_home fixture).
        slug: project slug.
        idea: text for "**Idea:** ..." line in 00-hypothesis-list.md, or None to omit.
        backlog: list of (id, statement) pairs to include in the backlog table.
        run_hypotheses: subset of backlog ids to materialise as H<n>-*/ dirs (with sprint kit).
        synthesised: subset of run_hypotheses ids that get a synthesis.md.
        interviews: hypothesis_id → list of interview-file basenames (no .md suffix).
    """
    project = home / ".lean-agent" / "projects" / slug
    research = project / "01-research"
    research.mkdir(parents=True)

    backlog = backlog or []
    run_hypotheses = run_hypotheses or []
    synthesised = synthesised or []
    interviews = interviews or {}

    # Write 00-hypothesis-list.md
    hyp_list = research / "00-hypothesis-list.md"
    parts = ["# The Hypothesis Engine\n"]
    if idea is not None:
        parts.append(f"**Idea:** {idea}\n")
    parts.append("**Project slug:** `" + slug + "`\n")
    idea_triage = idea_triage or ["some idea"]
    triage_bullets = "".join(f"- {b}\n" for b in idea_triage)
    parts.append(f"\n## 1. Idea Triage\n\n{triage_bullets}")
    parts.append("\n## 2. Hypothesis Backlog\n\n")
    parts.append("| Priority | ID | Hypothesis | Impact | Risk | Effort | Score | Expected pain | Expected objection |\n")
    parts.append("|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---|:---|\n")
    for i, (hid, statement) in enumerate(backlog, start=1):
        parts.append(f"| {i} | {hid} | {statement} | 3 | 3 | 3 | 3.0 | pain | objection |\n")
    parts.append("\n## 3. Active & Recent Experiments\n\nrest of file\n")
    hyp_list.write_text("".join(parts))

    # Materialise H<n>-*/ dirs for run hypotheses.
    for hid, dir_slug in run_hypotheses:
        hdir = research / f"{hid}-{dir_slug}"
        hdir.mkdir()
        (hdir / "01-problem-validation-sprint.md").write_text(
            f"# Sprint Kit — {hid}\n\nDiscussion guide here.\n"
        )
        if hid in synthesised:
            (hdir / "synthesis.md").write_text(
                f"# Synthesis — {hid}\n\nThemes go here.\n"
            )
        idir = hdir / "interviews"
        idir.mkdir()
        for name in interviews.get(hid, []):
            (idir / f"{name}.md").write_text(f"# Interview — {name}\n")

    return project
