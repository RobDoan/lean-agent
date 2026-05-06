from pathlib import Path

import pytest

from tests.fixtures.fake_home import make_project


def test_read_research_tree_raises_when_project_missing(tmp_home: Path) -> None:
    from lean_agent.commands.errors import ProjectNotFoundError
    from lean_agent.commands.read_research_tree import read_research_tree

    with pytest.raises(ProjectNotFoundError):
        read_research_tree("nope")


def test_read_research_tree_lists_backlog(tmp_home: Path) -> None:
    from lean_agent.commands.read_research_tree import read_research_tree

    make_project(
        tmp_home,
        "p1",
        idea="x",
        backlog=[("H1", "We believe gig workers"), ("H2", "We believe migrants")],
    )

    tree = read_research_tree("p1")
    assert tree.slug == "p1"
    assert tree.idea == "x"
    assert len(tree.hypotheses) == 2
    assert tree.hypotheses[0].id == "H1"
    assert tree.hypotheses[0].title == "We believe gig workers"
    assert tree.hypotheses[1].id == "H2"


def test_hypothesis_has_run_when_dir_exists(tmp_home: Path) -> None:
    from lean_agent.commands.read_research_tree import read_research_tree

    make_project(
        tmp_home,
        "p1",
        backlog=[("H1", "stmt"), ("H2", "stmt2")],
        run_hypotheses=[("H1", "modern-slug")],
        synthesised=["H1"],
        interviews={"H1": ["alex-2026", "jane-2026"]},
    )

    tree = read_research_tree("p1")
    h1, h2 = tree.hypotheses
    assert h1.has_run is True
    assert h1.has_synthesis is True
    assert h1.interview_count == 2
    assert h2.has_run is False
    assert h2.has_synthesis is False
    assert h2.interview_count == 0


def test_legacy_we_believe_dir_resolves(tmp_home: Path) -> None:
    """Pre-v0.1.2 dirs named H<n>-we-believe-*/ should still match."""
    from lean_agent.commands.read_research_tree import read_research_tree

    make_project(
        tmp_home,
        "p1",
        backlog=[("H1", "We believe legacy")],
        run_hypotheses=[("H1", "we-believe-legacy")],  # old slug shape
        synthesised=["H1"],
    )

    tree = read_research_tree("p1")
    assert tree.hypotheses[0].has_run is True
    assert tree.hypotheses[0].has_synthesis is True


def test_read_research_tree_parses_idea_triage(tmp_home: Path) -> None:
    from lean_agent.commands.read_research_tree import read_research_tree

    make_project(
        tmp_home,
        "p1",
        idea="x",
        idea_triage=[
            "What if we used AI for invoice follow-ups?",
            "Could we build a community feature?",
        ],
        backlog=[("H1", "stmt")],
    )

    tree = read_research_tree("p1")
    assert tree.idea_triage == [
        "What if we used AI for invoice follow-ups?",
        "Could we build a community feature?",
    ]


def test_malformed_backlog_returns_empty_hypotheses(tmp_home: Path, caplog: pytest.LogCaptureFixture) -> None:
    """If 00-hypothesis-list.md exists but has no backlog table, degrade gracefully."""
    from lean_agent.commands.read_research_tree import read_research_tree

    project = make_project(tmp_home, "p1", idea="x", backlog=[])
    # Overwrite to remove the backlog section entirely.
    (project / "01-research" / "00-hypothesis-list.md").write_text("# Just a title\n")

    tree = read_research_tree("p1")
    assert tree.hypotheses == []
