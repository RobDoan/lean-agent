from lean_agent.prompts.discussion_guide import build as build_guide
from lean_agent.prompts.init_hypotheses import build as build_init
from lean_agent.prompts.interview import build as build_interview
from lean_agent.prompts.synthesis import build as build_synth
from lean_agent.prompts.system import GUARDRAILS


def test_guardrails_contains_three_rules():
    assert "Confession" in GUARDRAILS
    assert "Steel-man" in GUARDRAILS
    assert "Kill" in GUARDRAILS


def test_init_prompt_includes_idea_and_asks_for_json():
    sys, msgs = build_init(idea="AI invoice follow-ups for freelancers")
    assert "AI invoice follow-ups for freelancers" in msgs[0]["content"]
    assert "JSON" in msgs[0]["content"]
    assert GUARDRAILS in sys


def test_discussion_guide_prompt_uses_hypothesis():
    sys, msgs = build_guide(hypothesis_statement="Personalized onboarding +25%")
    assert "Personalized onboarding +25%" in msgs[0]["content"]
    assert GUARDRAILS in sys


def test_interview_prompt_includes_persona_and_questions():
    sys, msgs = build_interview(
        persona_md="---\nid: sarah\nname: Sarah\n---\n## Beliefs\n- x\n",
        hypothesis_statement="X",
        questions=["q1", "q2"],
    )
    assert "Sarah" in msgs[0]["content"]
    assert "q1" in msgs[0]["content"]
    assert GUARDRAILS in sys


def test_synthesis_prompt_includes_all_transcripts():
    sys, msgs = build_synth(
        hypothesis_statement="X",
        transcripts=["transcript A", "transcript B"],
    )
    assert "transcript A" in msgs[0]["content"]
    assert "transcript B" in msgs[0]["content"]
    content_lower = msgs[0]["content"].lower()
    assert "kill_signal" in content_lower or "kill signal" in content_lower
    assert GUARDRAILS in sys
