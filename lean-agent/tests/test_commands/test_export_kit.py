from datetime import date
from pathlib import Path

from lean_agent.commands.export_kit import _hypothesis_dir, export_kit
from lean_agent.commands.init import init_project
from lean_agent.commands.promote import promote
from lean_agent.commands.run_r1 import run_r1
from lean_agent.llm import StubLLMClient
from lean_agent.paths import research_dir
from tests.test_commands.test_run_r1 import (
    _GUIDE_RESP,
    _INIT_RESP,
    _INTERVIEW_RESP,
    _SYNTHESIS_RESP,
    _seed_personas,
)


def test_export_kit_writes_four_files(tmp_home: Path):
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
    promote(slug=slug, hypothesis_id="H1", today=date(2026, 5, 1))

    kit_dir = export_kit(slug=slug, hypothesis_id="H1", today=date(2026, 5, 1), idea="x")
    for name in [
        "discussion_guide.md",
        "recruiting_criteria.md",
        "consent_form.md",
        "transcript_template.md",
    ]:
        assert (kit_dir / name).exists(), f"{name} missing"
    assert "Discussion Guide" in (kit_dir / "discussion_guide.md").read_text(encoding="utf-8")


def test_hypothesis_dir_resolves_legacy_we_believe_pattern(tmp_home: Path):
    """Regression guard for v0.1.2 slug change: existing H<n>-we-believe-*/
    directories from v0/v0.1.0/v0.1.1 projects must continue to be resolvable
    via the H<n>-* glob in commands/export_kit._hypothesis_dir.
    """
    slug = "demo-project"
    legacy_dir = research_dir(slug) / "H1-we-believe-small-e-commerce-shops"
    legacy_dir.mkdir(parents=True)

    resolved = _hypothesis_dir(slug, "H1")

    assert resolved == legacy_dir


def test_hypothesis_dir_resolves_new_audience_topic_pattern(tmp_home: Path):
    """v0.1.2 forward case: new-shape H<n>-<audience-and-topic>/ dirs resolve
    via the same glob.
    """
    slug = "demo-project"
    new_dir = research_dir(slug) / "H1-small-e-commerce-shops-will-adopt-invoice-reminders"
    new_dir.mkdir(parents=True)

    resolved = _hypothesis_dir(slug, "H1")

    assert resolved == new_dir
