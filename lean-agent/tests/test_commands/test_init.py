import json
from datetime import date
from pathlib import Path

import pytest

from lean_agent.commands.init import init_project
from lean_agent.llm import StubLLMClient


CANNED = json.dumps(
    {
        "idea_angles": ["Angle A", "Angle B"],
        "hypotheses": [
            {
                "id": f"H{i}",
                "statement": f"hyp {i}",
                "impact": 4,
                "risk": 3,
                "effort": 2,
                "score": 6.0,
                "expected_pain": "p",
                "expected_objection": "o",
            }
            for i in range(1, 11)
        ],
    }
)


def test_init_creates_project_files(tmp_home: Path):
    llm = StubLLMClient(responses=[CANNED])
    slug = init_project(idea="AI invoice follow-ups", llm=llm, today=date(2026, 5, 1), owner="quy")
    proj = tmp_home / ".lean-agent" / "projects" / slug
    assert (proj / ".git").is_dir()
    assert (proj / "README.md").exists()
    assert (proj / "ROADMAP.md").exists()
    hl = (proj / "01-research" / "00-hypothesis-list.md").read_text()
    assert "AI invoice follow-ups" in hl
    assert "H1" in hl and "H10" in hl
    assert "Angle A" in hl


def test_init_commits_initial_state(tmp_home: Path):
    from git import Repo

    llm = StubLLMClient(responses=[CANNED])
    slug = init_project(idea="X", llm=llm, today=date(2026, 5, 1), owner="quy")
    repo = Repo(tmp_home / ".lean-agent" / "projects" / slug)
    msgs = [c.message for c in repo.iter_commits()]
    assert any("init" in m for m in msgs)


def test_init_refuses_when_project_exists(tmp_home: Path):
    llm = StubLLMClient(responses=[CANNED, CANNED])
    init_project(idea="dup", llm=llm, today=date(2026, 5, 1), owner="quy")
    with pytest.raises(FileExistsError):
        init_project(idea="dup", llm=llm, today=date(2026, 5, 1), owner="quy")


def test_init_seeds_personas_on_first_run(tmp_home: Path):
    """First-run UX: when ~/.lean-agent/personas/ is empty, copy bundled starters + presets."""
    llm = StubLLMClient(responses=[CANNED])
    init_project(idea="first idea", llm=llm, today=date(2026, 5, 1), owner="q")
    personas_root = tmp_home / ".lean-agent" / "personas"
    assert (personas_root / "sarah-freelance-designer.md").exists()
    assert (personas_root / "_panel-presets" / "smb-saas.md").exists()


def test_init_does_not_overwrite_existing_personas(tmp_home: Path):
    personas_root = tmp_home / ".lean-agent" / "personas"
    personas_root.mkdir(parents=True)
    (personas_root / "my-custom.md").write_text(
        "---\nid: my-custom\nname: Custom\n---\n"
        "## Backstory\nx\n## Beliefs\n- y\n## Biases\n- z\n## How she answers questions\n- w\n"
    )
    llm = StubLLMClient(responses=[CANNED])
    init_project(idea="x", llm=llm, today=date(2026, 5, 1), owner="q")
    files = sorted(p.name for p in personas_root.glob("*.md"))
    assert files == ["my-custom.md"]  # starters NOT copied because dir was non-empty


def test_init_sanitizes_pipe_in_hypothesis_statements(tmp_home: Path):
    """A hypothesis statement containing `|` would corrupt the markdown table; replace with `/`."""
    canned = json.dumps(
        {
            "idea_angles": ["A"],
            "hypotheses": [
                {
                    "id": "H1",
                    "statement": "We believe A | B will pay",
                    "impact": 4,
                    "risk": 3,
                    "effort": 2,
                    "score": 6.0,
                    "expected_pain": "p",
                    "expected_objection": "o",
                }
            ],
        }
    )
    llm = StubLLMClient(responses=[canned])
    slug = init_project(idea="pipe test", llm=llm, today=date(2026, 5, 1), owner="q")
    hl = (
        tmp_home / ".lean-agent" / "projects" / slug / "01-research" / "00-hypothesis-list.md"
    ).read_text(encoding="utf-8")
    # Pipe in statement was replaced with /
    assert "A / B will pay" in hl
    # Table row count: header + separator + 1 data row = 3 lines starting with `|`
    table_lines = [line for line in hl.splitlines() if line.startswith("|")]
    assert len(table_lines) == 3


def test_init_handles_hypothesis_list_wrapped_in_json_fences(tmp_home: Path):
    """Real LLMs sometimes wrap structured output in ```json fences. Don't blow up at init."""
    llm = StubLLMClient(responses=["```json\n" + CANNED + "\n```"])
    slug = init_project(idea="fenced idea", llm=llm, today=date(2026, 5, 1), owner="q")
    proj = tmp_home / ".lean-agent" / "projects" / slug
    hl = (proj / "01-research" / "00-hypothesis-list.md").read_text(encoding="utf-8")
    assert "H1" in hl and "H10" in hl
    assert "Angle A" in hl


def test_init_handles_trailing_prose_after_json(tmp_home: Path):
    """Real Sonnet sometimes appends explanation after the JSON closes. Bare json.loads
    fails with 'Extra data: line N column 1'. parse_first_json_object handles it."""
    chatty = (
        "Sure! Here's the analysis:\n\n"
        + CANNED
        + "\n\nLet me know if you want me to dig deeper into any of these hypotheses."
    )
    llm = StubLLMClient(responses=[chatty])
    slug = init_project(idea="chatty llm", llm=llm, today=date(2026, 5, 1), owner="q")
    hl = (
        tmp_home / ".lean-agent" / "projects" / slug / "01-research" / "00-hypothesis-list.md"
    ).read_text(encoding="utf-8")
    assert "H1" in hl and "H10" in hl


def test_init_does_not_create_project_dir_when_llm_returns_garbage(tmp_home: Path):
    """A failed parse must NOT leave a half-created project that blocks the user's retry."""
    llm = StubLLMClient(responses=["this is not JSON at all"])
    with pytest.raises(ValueError):
        init_project(idea="will fail", llm=llm, today=date(2026, 5, 1), owner="q")
    projects_root = tmp_home / ".lean-agent" / "projects"
    # No project dir created on failure.
    assert not projects_root.exists() or not any(projects_root.iterdir())


def test_init_emits_progress_messages(tmp_home: Path):
    llm = StubLLMClient(responses=[CANNED])
    messages: list[str] = []
    slug = init_project(
        idea="x",
        llm=llm,
        today=date(2026, 5, 1),
        owner="q",
        progress=messages.append,
    )
    assert messages[0] == "generating hypotheses..."
    assert messages[1].startswith("wrote: ")
    assert slug in messages[1]
    assert messages[2] == f"set current project: {slug}"


def test_init_sets_state_to_new_slug(tmp_home: Path):
    from lean_agent.state import read_current_slug

    llm = StubLLMClient(responses=[CANNED])
    slug = init_project(idea="x", llm=llm, today=date(2026, 5, 1), owner="q")
    assert read_current_slug() == slug


def test_init_default_progress_is_silent(tmp_home: Path):
    llm = StubLLMClient(responses=[CANNED])
    init_project(idea="x", llm=llm, today=date(2026, 5, 1), owner="q")
    # No raise == pass
