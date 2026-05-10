def test_build_system_prompt_includes_persona_summaries():
    from lean_agent.prompts.preset_gap_analysis import build_system_prompt

    personas = [
        {"id": "bob", "name": "Bob", "role": "CTO", "income": "200k", "location": "NYC"},
        {"id": "alice", "name": "Alice", "role": "founder"},
    ]

    sys = build_system_prompt(personas)

    # Sorted alphabetically
    assert sys.index("alice") < sys.index("bob")
    # Contains persona fields
    assert "name=Alice" in sys
    assert "role=CTO" in sys
    assert "income=200k" in sys
    assert "location=NYC" in sys
    # Contains rules
    assert "1 and 12" in sys
    assert "No duplicates" in sys


def test_build_system_prompt_empty_personas():
    from lean_agent.prompts.preset_gap_analysis import build_system_prompt

    sys = build_system_prompt([])

    assert "(none)" in sys


def test_build_system_prompt_minimal_persona():
    from lean_agent.prompts.preset_gap_analysis import build_system_prompt

    sys = build_system_prompt([{"id": "dan"}])

    assert "dan" in sys
    # No trailing comma artifacts for id-only persona
    assert "dan\n" in sys or "dan" in sys


def test_build_user_message_wraps_instruction():
    from lean_agent.prompts.preset_gap_analysis import build_user_message

    msg = build_user_message("a panel of SaaS founders")

    assert "<instruction>" in msg
    assert "a panel of SaaS founders" in msg
    assert "</instruction>" in msg
