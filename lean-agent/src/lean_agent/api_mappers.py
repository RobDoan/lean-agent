"""Domain entity → DTO transformers (CLAUDE.md §2.1 mapper layer)."""
from __future__ import annotations

from lean_agent.api_schemas import (
    HypothesisDetail,
    HypothesisListItem,
    InterviewMeta,
    PersonaDetail,
    PersonaSummary,
    PresetDetail,
    PresetSummary,
    ProjectDetail,
    ProjectSummary,
)
from lean_agent.commands.list_projects import Project
from lean_agent.commands.read_research_tree import Hypothesis, ResearchTree
from lean_agent.panel_presets.loader import Preset
from lean_agent.personas.loader import Persona


def project_to_summary(p: Project) -> ProjectSummary:
    return ProjectSummary(
        slug=p.slug,
        idea=p.idea,
        hypothesis_count=p.hypothesis_count,
        run_count=p.run_count,
        with_synthesis_count=p.with_synthesis_count,
        created_at=p.created_at,
    )


def hypothesis_to_list_item(h: Hypothesis) -> HypothesisListItem:
    return HypothesisListItem(
        id=h.id,
        title=h.title,
        has_run=h.has_run,
        has_synthesis=h.has_synthesis,
        interview_count=h.interview_count,
    )


def tree_to_detail(tree: ResearchTree) -> ProjectDetail:
    return ProjectDetail(
        slug=tree.slug,
        idea=tree.idea,
        idea_triage=tree.idea_triage,
        hypotheses=[hypothesis_to_list_item(h) for h in tree.hypotheses],
    )


def hypothesis_to_detail(
    h: Hypothesis,
    *,
    synthesis_markdown: str | None,
    sprint_markdown: str | None,
    interviews: list[tuple[str, str]],
) -> HypothesisDetail:
    """interviews: list of (basename_without_md, full_filename) pairs."""
    return HypothesisDetail(
        id=h.id,
        title=h.title,
        synthesis_markdown=synthesis_markdown,
        sprint_markdown=sprint_markdown,
        interviews=[InterviewMeta(name=n, filename=f) for n, f in interviews],
    )


def persona_to_summary_dto(p: Persona) -> PersonaSummary:
    return PersonaSummary(id=p.id, name=p.name, role=p.metadata.get("role"))


def persona_to_detail_dto(p: Persona, raw_content: str) -> PersonaDetail:
    return PersonaDetail(
        id=p.id,
        name=p.name,
        metadata={k: str(v) for k, v in p.metadata.items()},
        backstory=p.backstory,
        beliefs=p.beliefs,
        biases=p.biases,
        how_she_answers=p.how_she_answers,
        raw_content=raw_content,
    )


def preset_to_summary_dto(p: Preset) -> PresetSummary:
    return PresetSummary(name=p.name, persona_count=len(p.persona_ids), description=p.description)


def preset_to_detail_dto(p: Preset, raw_content: str) -> PresetDetail:
    return PresetDetail(name=p.name, persona_ids=list(p.persona_ids), raw_content=raw_content, description=p.description)
