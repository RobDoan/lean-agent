import re
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from lean_agent import paths
from lean_agent._text import parse_first_json_object
from lean_agent.git_ops import commit_all
from lean_agent.llm import LLMClient, LLMRequest
from lean_agent.personas.panel import resolve_panel
from lean_agent.prompts.discussion_guide import build as build_guide
from lean_agent.prompts.interview import build as build_interview
from lean_agent.prompts.synthesis import build as build_synth
from lean_agent.render import render
from lean_agent.slugify import slugify_idea


_HYP_ROW = re.compile(r"^\|\s*\d+\s*\|\s*(H\d+)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)
_SECTION_4_BOUNDARY = re.compile(r"\n\n## 4\. ", re.MULTILINE)
_LEAD = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


def _strip_lead(line: str) -> str:
    """Remove leading bullet (`-`, `*`, `•`) or numbering (`1.`, `1)`) from a question line.

    The discussion-guide prompt instructs no-numbering, but real LLMs frequently disobey.
    Stripping at parse time keeps the PVS render and export-kit clean.
    """
    return _LEAD.sub("", line, count=1)


def _read_hypothesis(slug: str, hypothesis_id: str) -> dict[str, Any]:
    text = paths.hypothesis_list_path(slug).read_text(encoding="utf-8")
    for hid, statement in _HYP_ROW.findall(text):
        if hid == hypothesis_id:
            return {"id": hid, "statement": statement.strip()}
    raise ValueError(f"hypothesis not found: {hypothesis_id}")


def _hypothesis_slug(statement: str) -> str:
    # Strip leading "We believe " (case-insensitive) so the slug surfaces audience
    # + topic instead of prompt-template boilerplate. If the statement doesn't start
    # with "we believe", slugify_idea handles it as-is. max_words drops to the
    # slugify_idea default (8) so the slug captures audience + verb + topic.
    cleaned = re.sub(r"^we\s+believe\s+", "", statement, count=1, flags=re.IGNORECASE)
    return slugify_idea(cleaned)


def _mark_active_in_hypothesis_list(
    slug: str, hypothesis_id: str, statement: str, today: str
) -> None:
    """Append (or replace empty-state with) an active-block in §3 of hypothesis-list.md.

    Block format MUST match the regex used by commands/_state.py:
        '### H<n> — <statement>\\n\\n- **Status:** ...\\n- **Decision:** ...\\n- **Key Learning:** ...\\n- **Evidence:** ...\\n'

    Insertion strategy:
    - First R1 ever: replace the `*(empty — …)*` marker that the init template wrote.
    - Second+ R1: insert just before `## 4. Learning Library` so the new active
      block stays inside §3, not appended after EOF (where it would visually
      land inside §4).
    """
    hl_path = paths.hypothesis_list_path(slug)
    text = hl_path.read_text(encoding="utf-8")
    block = (
        f"### {hypothesis_id} — {statement}\n\n"
        f"- **Status:** 🟡 Testing (simulated)\n"
        f"- **Decision:** ⏳ Awaiting synthesis review\n"
        f"- **Key Learning:** *(pending)*\n"
        f"- **Evidence:** simulated transcripts in `{hypothesis_id}-*/`\n"
    )
    empty_marker = "*(empty — run `lean run R1 H1` to start)*"
    if empty_marker in text:
        text = text.replace(empty_marker, block.rstrip())
    else:
        # Insert just before "\n\n## 4. " so the active block stays inside §3.
        m = _SECTION_4_BOUNDARY.search(text)
        if m:
            text = text[: m.start()] + "\n\n" + block.rstrip() + text[m.start() :]
        else:
            # Defensive: if §4 boundary is missing (user-edited template), append.
            text = text.rstrip() + "\n\n" + block
    hl_path.write_text(text, encoding="utf-8")


def run_r1(
    *,
    slug: str,
    hypothesis_id: str,
    llm: LLMClient,
    today: date,
    panel_ids: str | None = None,
    panel_name: str | None = None,
    n: int = 5,
    progress: Callable[[str], None] | None = None,
) -> Path:
    def _emit(msg: str) -> None:
        if progress is not None:
            progress(msg)

    today_str = today.isoformat()
    hyp = _read_hypothesis(slug, hypothesis_id)
    h_slug = _hypothesis_slug(hyp["statement"])
    h_dir = paths.hypothesis_dir(slug, hypothesis_id, h_slug)
    (h_dir / "interviews").mkdir(parents=True, exist_ok=True)

    _emit(f"resolving panel ({n} personas)...")
    personas = resolve_panel(paths.personas_root(), ids=panel_ids, panel_name=panel_name, n=n)

    # 1. Discussion guide
    _emit("generating discussion guide...")
    sys_prompt, msgs = build_guide(hypothesis_statement=hyp["statement"])
    guide_text = llm.complete(LLMRequest(system=sys_prompt, messages=msgs)).text
    questions = [
        _strip_lead(q.strip())
        for q in guide_text.splitlines()
        if q.strip() and not q.strip().startswith("#")
    ]

    pvs = render(
        "problem_validation_sprint.md.j2",
        {
            "today": today_str,
            "hypothesis": {
                **hyp,
                "riskiest_assumption": "(write me)",
                "success_criteria": "(write me)",
                "kill_criteria": "(write me)",
            },
            "personas": [{"id": p.id} for p in personas],
            "discussion_guide": questions,
        },
    )
    (h_dir / "01-problem-validation-sprint.md").write_text(pvs, encoding="utf-8")

    # 2. Per-persona interviews
    transcripts: list[str] = []
    for i, p in enumerate(personas, start=1):
        _emit(f"interview {i}/{len(personas)}: {p.id}...")
        # load_all() always sets raw_path; this guards against future code
        # that passes in-memory personas.
        if p.raw_path is None:
            raise ValueError(
                f"persona '{p.id}' has no raw_path; run_r1 requires disk-backed personas"
            )
        sys_prompt, msgs = build_interview(
            persona_md=p.raw_path.read_text(encoding="utf-8"),
            hypothesis_statement=hyp["statement"],
            questions=questions,
        )
        body = llm.complete(LLMRequest(system=sys_prompt, messages=msgs)).text
        transcript_path = h_dir / "interviews" / f"{p.id}-{today_str}.md"
        full = (
            f"# Interview transcript — {p.name}\n\n"
            f"**Persona ID:** {p.id}\n"
            f"**Hypothesis:** {hyp['id']} — {hyp['statement']}\n"
            f"**Date:** {today_str}\n"
            f"**Mode:** Simulated\n\n---\n\n"
            f"{body}\n"
        )
        transcript_path.write_text(full, encoding="utf-8")
        transcripts.append(full)

    # 3. Synthesis
    _emit(f"synthesizing across {len(personas)} transcripts...")
    sys_prompt, msgs = build_synth(hypothesis_statement=hyp["statement"], transcripts=transcripts)
    syn_text = llm.complete(LLMRequest(system=sys_prompt, messages=msgs)).text.strip()
    syn_data = parse_first_json_object(syn_text)
    syn = render(
        "synthesis.md.j2",
        {
            "hypothesis": hyp,
            "today": today_str,
            "persona_ids": [p.id for p in personas],
            "steelman": syn_data["steelman"],
            "themes": syn_data["themes"],
            "kill_signal": syn_data["kill_signal"],
            "confident": syn_data["confident"],
            "unknown": syn_data["unknown"],
            "recommendation": syn_data["recommendation"],
        },
    )
    (h_dir / "synthesis.md").write_text(syn, encoding="utf-8")

    # 4. Update §3 of hypothesis-list.md
    _mark_active_in_hypothesis_list(slug, hyp["id"], hyp["statement"], today_str)

    # 5. Commit
    commit_all(paths.project_dir(slug), f"run: R1 simulated for {hyp['id']}")
    _emit(f"wrote: {h_dir}")
    return h_dir
