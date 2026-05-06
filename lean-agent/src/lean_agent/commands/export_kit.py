import re
from datetime import date
from pathlib import Path
from typing import Any

from lean_agent import paths
from lean_agent.git_ops import commit_all
from lean_agent.render import render


def _collect_questions(pvs_text: str) -> list[dict[str, Any]]:
    block = re.search(r"## 3\. Discussion Guide\n(.*?)(?=^## )", pvs_text, re.DOTALL | re.MULTILINE)
    if not block:
        return []
    items = re.findall(r"^\s*\d+\.\s+(.*)$", block.group(1), re.MULTILINE)
    out = []
    for q in items:
        leading = q.lower().startswith(("would you", "do you think", "could you imagine"))
        rephrase = "Tell me about a recent time you …" if leading else None
        out.append({"text": q, "leading_warning": leading, "rephrase": rephrase})
    return out


def _hypothesis_dir(slug: str, hypothesis_id: str) -> Path:
    research = paths.research_dir(slug)
    matches = list(research.glob(f"{hypothesis_id}-*"))
    if not matches:
        raise ValueError(f"hypothesis dir not found for {hypothesis_id}")
    return matches[0]


def export_kit(*, slug: str, hypothesis_id: str, today: date, idea: str) -> Path:
    h_dir = _hypothesis_dir(slug, hypothesis_id)
    pvs = (h_dir / "01-problem-validation-sprint.md").read_text(encoding="utf-8")
    statement_match = re.search(r"\*\*Hypothesis:\*\* (.+)$", pvs, re.MULTILINE)
    statement = statement_match.group(1).strip() if statement_match else "(unknown)"
    hypothesis = {"id": hypothesis_id, "statement": statement}

    kit_dir = h_dir / "interview-kit"
    kit_dir.mkdir(exist_ok=True)
    today_str = today.isoformat()

    (kit_dir / "discussion_guide.md").write_text(
        render(
            "interview_kit/discussion_guide.md.j2",
            {"hypothesis": hypothesis, "today": today_str, "questions": _collect_questions(pvs)},
        ),
        encoding="utf-8",
    )
    (kit_dir / "recruiting_criteria.md").write_text(
        render(
            "interview_kit/recruiting_criteria.md.j2",
            {
                "hypothesis": hypothesis,
                "criteria": [
                    "Active in the relevant domain in the last 90 days",
                    "Has experienced the predicted pain at least once in the last 30 days",
                ],
                "screeners": ["What's the last tool you started using for this? When?"],
                "disqualifiers": ["Built or sells a competing product"],
            },
        ),
        encoding="utf-8",
    )
    (kit_dir / "consent_form.md").write_text(
        render("interview_kit/consent_form.md.j2", {"idea": idea}),
        encoding="utf-8",
    )
    (kit_dir / "transcript_template.md").write_text(
        render("interview_kit/transcript_template.md.j2", {"hypothesis": hypothesis}),
        encoding="utf-8",
    )

    commit_all(paths.project_dir(slug), f"export-kit: {hypothesis_id}")
    return kit_dir
