from __future__ import annotations
from lean_agent import paths
from lean_agent.commands.errors import HypothesisNotFoundError, InterviewNotFoundError

def read_interview_content(slug: str, hid: str, name: str) -> str:
    hdir = paths.hypothesis_dir_glob(slug, hid)
    if hdir is None:
        raise HypothesisNotFoundError(slug, hid)
    interview = hdir / "interviews" / f"{name}.md"
    if not interview.exists():
        raise InterviewNotFoundError(slug, hid, name)
    return interview.read_text()
