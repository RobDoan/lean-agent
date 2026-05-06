from pathlib import Path

from tests.fixtures.fake_home import make_project


def test_list_projects_empty(tmp_home: Path) -> None:
    from lean_agent.commands.list_projects import list_projects

    assert list_projects() == []


def test_list_projects_returns_one_per_slug_alphabetical(tmp_home: Path) -> None:
    from lean_agent.commands.list_projects import list_projects

    make_project(tmp_home, "zeta-app", idea="Z")
    make_project(tmp_home, "alpha-app", idea="A")

    projects = list_projects()
    slugs = [p.slug for p in projects]
    assert slugs == ["alpha-app", "zeta-app"]


def test_list_projects_parses_idea(tmp_home: Path) -> None:
    from lean_agent.commands.list_projects import list_projects

    make_project(tmp_home, "p1", idea="i want to build a thing")

    projects = list_projects()
    assert projects[0].idea == "i want to build a thing"


def test_list_projects_idea_none_when_absent(tmp_home: Path) -> None:
    from lean_agent.commands.list_projects import list_projects

    make_project(tmp_home, "p1", idea=None)

    projects = list_projects()
    assert projects[0].idea is None


def test_list_projects_counts(tmp_home: Path) -> None:
    from lean_agent.commands.list_projects import list_projects

    make_project(
        tmp_home,
        "p1",
        idea="x",
        backlog=[("H1", "stmt1"), ("H2", "stmt2"), ("H3", "stmt3")],
        run_hypotheses=[("H1", "ran-1"), ("H2", "ran-2")],
        synthesised=["H1"],
    )

    projects = list_projects()
    assert projects[0].hypothesis_count == 3
    assert projects[0].run_count == 2
    assert projects[0].with_synthesis_count == 1
