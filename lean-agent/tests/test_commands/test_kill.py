from datetime import date
from pathlib import Path

from lean_agent.commands.init import init_project
from lean_agent.commands.kill import kill
from lean_agent.commands.run_r1 import run_r1
from lean_agent.llm import StubLLMClient
from tests.test_commands.test_run_r1 import (
    _GUIDE_RESP,
    _INIT_RESP,
    _INTERVIEW_RESP,
    _SYNTHESIS_RESP,
    _seed_personas,
)


def test_kill_writes_funeral_note_and_moves_to_library(tmp_home: Path):
    _seed_personas(tmp_home)
    slug = init_project(
        idea="x",
        llm=StubLLMClient(responses=[_INIT_RESP]),
        today=date(2026, 5, 1),
        owner="q",
    )
    run_r1(
        slug=slug,
        hypothesis_id="H1",
        llm=StubLLMClient(responses=[_GUIDE_RESP] + [_INTERVIEW_RESP] * 5 + [_SYNTHESIS_RESP]),
        today=date(2026, 5, 1),
    )
    kill(
        slug=slug,
        hypothesis_id="H1",
        note="0/5 would pay; rails solve it.",
        today=date(2026, 5, 1),
    )
    hl = (
        tmp_home / ".lean-agent" / "projects" / slug / "01-research" / "00-hypothesis-list.md"
    ).read_text(encoding="utf-8")
    assert "💀" in hl
    assert "rails solve it" in hl
