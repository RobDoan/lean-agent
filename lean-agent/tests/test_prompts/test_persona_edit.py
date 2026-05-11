def test_system_prompt_locks_required_format_rules():
    from lean_agent.prompts.persona_edit import SYSTEM_PROMPT

    # Spot-check the contract: format rules must mention all 4 sections by name
    assert "## Backstory" in SYSTEM_PROMPT
    assert "## Beliefs" in SYSTEM_PROMPT
    assert "## Biases" in SYSTEM_PROMPT
    assert "## How she answers questions" in SYSTEM_PROMPT
    # No code fences in output
    assert "no code fences" in SYSTEM_PROMPT.lower()
    # Do not include id field
    assert "Do NOT include an `id` field" in SYSTEM_PROMPT


def test_build_user_message_wraps_current_and_instruction():
    from lean_agent.prompts.persona_edit import build_user_message

    msg = build_user_message(current_content="OLD CONTENT", instruction="make it shorter")

    assert "<current_file>" in msg
    assert "OLD CONTENT" in msg
    assert "</current_file>" in msg
    assert "<instruction>" in msg
    assert "make it shorter" in msg
    assert "</instruction>" in msg


def test_build_user_message_handles_empty_current_for_create():
    from lean_agent.prompts.persona_edit import build_user_message

    msg = build_user_message(current_content="", instruction="create a new persona")

    assert "<current_file>" in msg
    assert "<instruction>" in msg
    assert "create a new persona" in msg
