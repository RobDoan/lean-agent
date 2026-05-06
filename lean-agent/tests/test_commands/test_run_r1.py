import json
from datetime import date
from pathlib import Path

import pytest

from lean_agent.commands.init import init_project
from lean_agent.commands.run_r1 import run_r1
from lean_agent.llm import StubLLMClient


_INIT_RESP = json.dumps(
    {
        "idea_angles": ["A"],
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

_GUIDE_RESP = (
    "Tell me about your last week.\n"
    "What's the worst part of getting paid?\n"
    "What have you tried?\n"
    "Who has solved this for you?\n"
    "What would make you switch?"
)

_INTERVIEW_RESP = """## Q & A

**Q1:** Tell me about your last week.

**A1:** Last Tuesday I chased down 3 invoices.

**Q2:** What's the worst part?

**A2:** The follow-up emails feel like begging.

**Q3:** What have you tried?

**A3:** FreshBooks reminders, manual emails.

**Q4:** Who has solved this?

**A4:** No one in my circle.

**Q5:** What would make you switch?

**A5:** Peer recommendation + 30-min setup.

## Confession
A real Sarah might never admit how often she forgets entirely.

## Confidence
3
"""

_SYNTHESIS_RESP = json.dumps(
    {
        "steelman": "Founders that built this folded — payment chasing is solved by Stripe + bank rails for >70% of cases.",
        "themes": ["follow-up feels like begging", "peer trust is the wedge"],
        "kill_signal": {
            "would_use": 1,
            "would_avoid": 2,
            "total": 5,
            "kill_threshold_met": True,
        },
        "confident": ["Pain exists across 5 personas"],
        "unknown": ["Willingness-to-pay at $20/mo"],
        "recommendation": "💀 Kill",
    }
)


def _seed_personas(home: Path) -> None:
    root = home / ".lean-agent" / "personas"
    root.mkdir(parents=True)
    for pid in ["sarah", "mike", "jamie", "alex", "priya"]:
        (root / f"{pid}.md").write_text(
            f"""---
id: {pid}
name: {pid.title()}
---

## Backstory
x
## Beliefs
- y
## Biases
- z
## How she answers questions
- w
""",
            encoding="utf-8",
        )


def test_run_r1_creates_artifacts(tmp_home: Path):
    _seed_personas(tmp_home)
    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(idea="AI invoice", llm=init_llm, today=date(2026, 5, 1), owner="q")

    # 1 guide + 5 interviews + 1 synthesis = 7 calls
    run_llm = StubLLMClient(responses=[_GUIDE_RESP] + [_INTERVIEW_RESP] * 5 + [_SYNTHESIS_RESP])
    run_r1(slug=slug, hypothesis_id="H1", llm=run_llm, today=date(2026, 5, 1))

    proj = tmp_home / ".lean-agent" / "projects" / slug
    h_dir = next((proj / "01-research").glob("H1-*"))
    assert (h_dir / "01-problem-validation-sprint.md").exists()
    assert (h_dir / "synthesis.md").exists()
    assert len(list((h_dir / "interviews").glob("*.md"))) == 5

    syn = (h_dir / "synthesis.md").read_text(encoding="utf-8")
    assert "Steel-man" in syn
    assert "kill_threshold_met" not in syn  # rendered through template, not raw json
    assert "💀 Kill" in syn

    hl = (proj / "01-research" / "00-hypothesis-list.md").read_text(encoding="utf-8")
    assert "Testing (simulated)" in hl


def test_run_r1_unknown_hypothesis_raises(tmp_home: Path):
    _seed_personas(tmp_home)
    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(idea="x", llm=init_llm, today=date(2026, 5, 1), owner="q")
    with pytest.raises(ValueError, match="not found"):
        run_r1(
            slug=slug, hypothesis_id="H99", llm=StubLLMClient(responses=[]), today=date(2026, 5, 1)
        )


def test_second_run_r1_keeps_active_block_inside_section_3(tmp_home: Path):
    """Two R1 runs must produce two §3 active blocks, both BEFORE §4 Learning Library."""
    _seed_personas(tmp_home)
    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(idea="x", llm=init_llm, today=date(2026, 5, 1), owner="q")

    for hid in ("H1", "H2"):
        run_llm = StubLLMClient(responses=[_GUIDE_RESP] + [_INTERVIEW_RESP] * 5 + [_SYNTHESIS_RESP])
        run_r1(slug=slug, hypothesis_id=hid, llm=run_llm, today=date(2026, 5, 1))

    hl = (
        tmp_home / ".lean-agent" / "projects" / slug / "01-research" / "00-hypothesis-list.md"
    ).read_text(encoding="utf-8")
    h1_idx = hl.index("### H1 —")
    h2_idx = hl.index("### H2 —")
    section_4_idx = hl.index("## 4. Learning Library")
    assert h1_idx < h2_idx < section_4_idx, "both active blocks must precede §4"


def test_run_r1_strips_numbering_from_guide_questions(tmp_home: Path, mocker):
    """Real LLMs sometimes return numbered questions despite the prompt; we must strip."""
    _seed_personas(tmp_home)
    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(idea="x", llm=init_llm, today=date(2026, 5, 1), owner="q")

    numbered_guide = (
        "1. Tell me about your last week.\n"
        "2) Walk me through your last invoice.\n"
        "- What did you try first?\n"
        "* What would make you switch?\n"
        "5. What did you give up?\n"
    )
    run_llm = StubLLMClient(responses=[numbered_guide] + [_INTERVIEW_RESP] * 5 + [_SYNTHESIS_RESP])
    run_r1(slug=slug, hypothesis_id="H1", llm=run_llm, today=date(2026, 5, 1))

    proj = tmp_home / ".lean-agent" / "projects" / slug
    h_dir = next((proj / "01-research").glob("H1-*"))
    pvs = (h_dir / "01-problem-validation-sprint.md").read_text(encoding="utf-8")
    # Numbered "1. 1. Tell me…" must NOT appear; only the template's own numbering.
    assert "1. 1." not in pvs
    assert "1. 2)" not in pvs
    assert "1. -" not in pvs
    # Question content survives the strip.
    assert "Tell me about your last week" in pvs
    assert "Walk me through your last invoice" in pvs
    assert "What did you try first" in pvs


def test_run_r1_handles_synthesis_wrapped_in_json_fences(tmp_home: Path):
    """Real LLMs sometimes wrap JSON in ```json fences. Don't blow up on 7th call."""
    _seed_personas(tmp_home)
    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(idea="x", llm=init_llm, today=date(2026, 5, 1), owner="q")

    fenced_synthesis = "```json\n" + _SYNTHESIS_RESP + "\n```"
    run_llm = StubLLMClient(responses=[_GUIDE_RESP] + [_INTERVIEW_RESP] * 5 + [fenced_synthesis])
    run_r1(slug=slug, hypothesis_id="H1", llm=run_llm, today=date(2026, 5, 1))

    proj = tmp_home / ".lean-agent" / "projects" / slug
    h_dir = next((proj / "01-research").glob("H1-*"))
    syn = (h_dir / "synthesis.md").read_text(encoding="utf-8")
    assert "💀 Kill" in syn  # rendered correctly despite fenced input


def test_run_r1_emits_progress_messages(tmp_home: Path):
    _seed_personas(tmp_home)
    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(idea="x", llm=init_llm, today=date(2026, 5, 1), owner="q")

    messages: list[str] = []
    run_llm = StubLLMClient(responses=[_GUIDE_RESP] + [_INTERVIEW_RESP] * 5 + [_SYNTHESIS_RESP])
    run_r1(
        slug=slug,
        hypothesis_id="H1",
        llm=run_llm,
        today=date(2026, 5, 1),
        progress=messages.append,
    )

    # Sequence shape: 1 panel + 1 guide + 5 interviews + 1 synthesis + 1 wrote = 9
    assert len(messages) == 9
    assert messages[0] == "resolving panel (5 personas)..."
    assert messages[1] == "generating discussion guide..."
    for i, msg in enumerate(messages[2:7], start=1):
        assert msg.startswith(f"interview {i}/5:")
        assert msg.endswith("...")
    assert messages[7] == "synthesizing across 5 transcripts..."
    assert messages[8].startswith("wrote: ")


def test_run_r1_default_progress_is_silent(tmp_home: Path):
    """Default progress=None must remain a no-op so existing tests unchanged."""
    _seed_personas(tmp_home)
    init_llm = StubLLMClient(responses=[_INIT_RESP])
    slug = init_project(idea="x", llm=init_llm, today=date(2026, 5, 1), owner="q")
    run_llm = StubLLMClient(responses=[_GUIDE_RESP] + [_INTERVIEW_RESP] * 5 + [_SYNTHESIS_RESP])
    # Must not raise even with no progress kwarg supplied.
    run_r1(slug=slug, hypothesis_id="H1", llm=run_llm, today=date(2026, 5, 1))


def test_hypothesis_slug_strips_we_believe_prefix():
    """The 'We believe ' boilerplate prefix is dropped before slugification.

    Per design §3.2: a statement like 'We believe small e-commerce shops will adopt
    invoice reminders' should produce a slug that surfaces audience + topic, not
    `we-believe-X` boilerplate.
    """
    from lean_agent.commands.run_r1 import _hypothesis_slug

    assert (
        _hypothesis_slug("We believe small e-commerce shops will adopt invoice reminders")
        == "small-e-commerce-shops-will-adopt-invoice-reminders"
    )


def test_hypothesis_slug_prefix_strip_is_case_insensitive():
    """'we believe' (lowercase) and 'WE BELIEVE' (uppercase) strip the same way."""
    from lean_agent.commands.run_r1 import _hypothesis_slug

    assert _hypothesis_slug("we believe finance teams need automation") == _hypothesis_slug(
        "WE BELIEVE finance teams need automation"
    )
    assert _hypothesis_slug("we believe finance teams need automation").startswith("finance-teams")


def test_hypothesis_slug_passes_through_when_no_we_believe_prefix():
    """A statement that doesn't start with 'we believe' is slugified as-is at default
    8-word width — no prefix-strip happens, but max_words=8 (not 4) is in effect."""
    from lean_agent.commands.run_r1 import _hypothesis_slug

    # No prefix to strip — slugified at default 8 tokens.
    assert (
        _hypothesis_slug("Small consultancies need lighter time-tracking onboarding flows")
        == "small-consultancies-need-lighter-time-tracking-onboarding-flows"
    )


def test_hypothesis_slug_caps_at_eight_tokens():
    """slugify_idea splits on every non-alphanumeric (so 'early-stage' counts as 2
    tokens, 'follow-ups' counts as 2). The 8-token cap may chop trailing tokens.
    Verifies the design §3.2 / §6.1 #4 worked example."""
    from lean_agent.commands.run_r1 import _hypothesis_slug

    # 'early-stage SaaS founders will pay for follow-ups' splits to 9 tokens after
    # the 'We believe ' strip; cap at 8 drops the trailing 'ups'.
    assert (
        _hypothesis_slug("We believe early-stage SaaS founders will pay for follow-ups")
        == "early-stage-saas-founders-will-pay-for-follow"
    )
