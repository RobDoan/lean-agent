from datetime import datetime, timezone

from lean_agent.api_mappers import (
    hypothesis_to_detail,
    hypothesis_to_list_item,
    project_to_summary,
    tree_to_detail,
)
from lean_agent.commands.list_projects import Project
from lean_agent.commands.read_research_tree import Hypothesis, ResearchTree


def test_project_to_summary_roundtrip() -> None:
    p = Project(
        slug="p1",
        idea="an idea",
        hypothesis_count=3,
        run_count=2,
        with_synthesis_count=1,
        created_at="2026-05-04T00:00:00+00:00",
    )
    dto = project_to_summary(p)
    assert dto.slug == "p1"
    assert dto.idea == "an idea"
    assert dto.hypothesis_count == 3
    assert dto.run_count == 2
    assert dto.with_synthesis_count == 1
    assert dto.created_at == "2026-05-04T00:00:00+00:00"


def test_project_to_summary_idea_none_passes_through() -> None:
    p = Project(
        slug="p1",
        idea=None,
        hypothesis_count=0,
        run_count=0,
        with_synthesis_count=0,
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )
    dto = project_to_summary(p)
    assert dto.idea is None


def test_hypothesis_to_list_item_roundtrip() -> None:
    h = Hypothesis(id="H1", title="stmt", has_run=True, has_synthesis=False, interview_count=2)
    dto = hypothesis_to_list_item(h)
    assert dto.id == "H1"
    assert dto.title == "stmt"
    assert dto.has_run is True
    assert dto.has_synthesis is False
    assert dto.interview_count == 2


def test_tree_to_detail_aggregates_hypotheses() -> None:
    tree = ResearchTree(
        slug="p1",
        idea="idea",
        idea_triage=["some idea"],
        hypotheses=[
            Hypothesis(id="H1", title="t1", has_run=True, has_synthesis=True, interview_count=3),
            Hypothesis(id="H2", title="t2", has_run=False, has_synthesis=False, interview_count=0),
        ],
    )
    dto = tree_to_detail(tree)
    assert dto.slug == "p1"
    assert dto.idea == "idea"
    assert len(dto.hypotheses) == 2
    assert dto.hypotheses[0].id == "H1"
    assert dto.hypotheses[1].id == "H2"


def test_hypothesis_to_detail_roundtrip() -> None:
    h = Hypothesis(id="H1", title="stmt", has_run=True, has_synthesis=True, interview_count=1)
    interviews = [("int1", "int1.md")]
    dto = hypothesis_to_detail(
        h, synthesis_markdown="synth", sprint_markdown="sprint", interviews=interviews
    )
    assert dto.id == "H1"
    assert dto.title == "stmt"
    assert dto.synthesis_markdown == "synth"
    assert dto.sprint_markdown == "sprint"
    assert len(dto.interviews) == 1
    assert dto.interviews[0].name == "int1"
    assert dto.interviews[0].filename == "int1.md"
