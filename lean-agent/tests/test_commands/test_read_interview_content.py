from pathlib import Path
import pytest
from tests.fixtures.fake_home import make_project
from lean_agent.commands.read_interview_content import read_interview_content
from lean_agent.commands.errors import InterviewNotFoundError

def test_read_interview_content_success(tmp_home: Path) -> None:
    make_project(
        tmp_home,
        "p1",
        backlog=[("H1", "s1")],
        run_hypotheses=[("H1", "ran")],
        interviews={"H1": ["alex"]},
    )
    content = read_interview_content("p1", "H1", "alex")
    assert content == "# Interview — alex\n" # make_project fixture default content

def test_read_interview_content_not_found(tmp_home: Path) -> None:
    make_project(tmp_home, "p1", backlog=[("H1", "s1")], run_hypotheses=[("H1", "ran")])
    with pytest.raises(InterviewNotFoundError):
        read_interview_content("p1", "H1", "nope")
