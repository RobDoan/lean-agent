from pathlib import Path
import pytest
from tests.fixtures.fake_home import make_project
from lean_agent.commands.read_hypothesis_detail import read_hypothesis_detail
from lean_agent.commands.errors import HypothesisNotFoundError

def test_read_hypothesis_detail_success(tmp_home: Path) -> None:
    make_project(
        tmp_home,
        "p1",
        backlog=[("H1", "stmt1")],
        run_hypotheses=[("H1", "ran-1")],
        synthesised=["H1"],
        interviews={"H1": ["a", "b"]},
    )
    detail = read_hypothesis_detail("p1", "H1")
    assert detail.hypothesis.id == "H1"
    assert detail.hypothesis.title == "stmt1"
    assert detail.synthesis_markdown is not None
    assert detail.sprint_markdown is not None
    assert len(detail.interviews) == 2

def test_read_hypothesis_detail_not_found(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")])
    with pytest.raises(HypothesisNotFoundError):
        read_hypothesis_detail("p1", "H2")
