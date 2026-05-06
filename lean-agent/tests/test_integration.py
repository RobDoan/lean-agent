from datetime import date
from pathlib import Path

from lean_agent.commands.export_kit import export_kit
from lean_agent.commands.init import init_project
from lean_agent.commands.promote import promote
from lean_agent.commands.run_r1 import run_r1
from lean_agent.llm import StubLLMClient
from lean_agent.state import read_current_slug
from tests.test_commands.test_run_r1 import (
    _GUIDE_RESP,
    _INIT_RESP,
    _INTERVIEW_RESP,
    _SYNTHESIS_RESP,
    _seed_personas,
)


def test_full_v0_1_0_loop(tmp_home: Path):
    """init → run R1 → promote → export-kit, end to end. Asserts v0.1.0 additions:
    auto-set-current after init + progress messages from init and run R1."""
    _seed_personas(tmp_home)
    progress_log: list[str] = []

    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(
        idea="AI invoice follow-ups",
        llm=init_llm,
        today=date(2026, 5, 1),
        owner="quy",
        progress=progress_log.append,
    )

    # v0.1.0: init writes the new slug to state.
    assert read_current_slug() == slug
    # v0.1.0: init emits 3 progress lines.
    assert progress_log[:3] == [
        "generating hypotheses...",
        f"wrote: {tmp_home / '.lean-agent' / 'projects' / slug}",
        f"set current project: {slug}",
    ]
    progress_log.clear()

    run_llm = StubLLMClient(responses=[_GUIDE_RESP] + [_INTERVIEW_RESP] * 5 + [_SYNTHESIS_RESP])
    run_r1(
        slug=slug,
        hypothesis_id="H1",
        llm=run_llm,
        today=date(2026, 5, 1),
        progress=progress_log.append,
    )
    # v0.1.0: run R1 emits 9 progress lines.
    assert len(progress_log) == 9
    assert progress_log[0] == "resolving panel (5 personas)..."
    assert progress_log[1] == "generating discussion guide..."
    for i in range(1, 6):
        assert progress_log[1 + i].startswith(f"interview {i}/5:")
    assert progress_log[7] == "synthesizing across 5 transcripts..."
    assert progress_log[8].startswith("wrote: ")

    promote(slug=slug, hypothesis_id="H1", today=date(2026, 5, 1))

    kit = export_kit(
        slug=slug, hypothesis_id="H1", today=date(2026, 5, 1), idea="AI invoice follow-ups"
    )

    # Filesystem witnesses for spec §6.1.
    proj = tmp_home / ".lean-agent" / "projects" / slug
    assert (proj / ".git").is_dir()
    assert (proj / "README.md").exists()
    assert (proj / "ROADMAP.md").exists()
    assert (proj / "01-research" / "00-hypothesis-list.md").exists()
    h1 = next((proj / "01-research").glob("H1-*"))
    assert (h1 / "01-problem-validation-sprint.md").exists()
    assert (h1 / "synthesis.md").exists()
    assert len(list((h1 / "interviews").glob("*.md"))) == 5

    syn = (h1 / "synthesis.md").read_text(encoding="utf-8")
    assert "Steel-man" in syn
    assert "💀 Kill" in syn

    hl = (proj / "01-research" / "00-hypothesis-list.md").read_text(encoding="utf-8")
    assert "ready-for-real-interviews" in hl

    for name in [
        "discussion_guide.md",
        "recruiting_criteria.md",
        "consent_form.md",
        "transcript_template.md",
    ]:
        assert (kit / name).exists(), f"{name} missing from interview-kit"

    from git import Repo

    msgs = [c.message for c in Repo(proj).iter_commits()]
    assert any('init: pre-filtered hypothesis list for "AI invoice follow-ups"' in m for m in msgs)
    assert any("run: R1 simulated for H1" in m for m in msgs)
    assert any("promote: H1 ready for real interviews" in m for m in msgs)
    assert any("export-kit: H1" in m for m in msgs)


def test_api_e2e_full_chain(tmp_home) -> None:
    """End-to-end via TestClient: list → detail → hypothesis → interview."""
    from fastapi.testclient import TestClient

    from lean_agent.api import app
    from tests.fixtures.fake_home import make_project

    make_project(
        tmp_home,
        "stable-coin",
        idea="i want to build a stable coin app",
        backlog=[
            ("H1", "We believe gig workers will achieve same-day liquidity"),
            ("H2", "We believe migrants will save 40% on remittance costs"),
        ],
        run_hypotheses=[("H1", "gig-workers"), ("H2", "migrants")],
        synthesised=["H1"],
        interviews={"H1": ["alex-2026", "jane-2026"], "H2": ["maria-2026"]},
    )

    client = TestClient(app)

    # 1. List projects
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    assert any(p["slug"] == "stable-coin" for p in projects)
    sc = next(p for p in projects if p["slug"] == "stable-coin")
    assert sc["hypothesis_count"] == 2
    assert sc["run_count"] == 2
    assert sc["with_synthesis_count"] == 1

    # 2. Project detail
    r = client.get("/api/projects/stable-coin")
    assert r.status_code == 200
    detail = r.json()
    assert len(detail["hypotheses"]) == 2

    # 3. Hypothesis with synthesis
    r = client.get("/api/projects/stable-coin/hypotheses/H1")
    assert r.status_code == 200
    h1 = r.json()
    assert h1["synthesis_markdown"] is not None
    assert len(h1["interviews"]) == 2

    # 4. Single interview
    r = client.get("/api/projects/stable-coin/hypotheses/H1/interviews/alex-2026")
    assert r.status_code == 200
    intv = r.json()
    assert intv["name"] == "alex-2026"
    assert "Interview" in intv["markdown"]

    # 5. Hypothesis without synthesis
    r = client.get("/api/projects/stable-coin/hypotheses/H2")
    assert r.status_code == 200
    h2 = r.json()
    assert h2["synthesis_markdown"] is None
