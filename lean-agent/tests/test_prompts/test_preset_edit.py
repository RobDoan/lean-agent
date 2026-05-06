def test_build_system_prompt_injects_sorted_available_ids():
    from lean_agent.prompts.preset_edit import build_system_prompt

    sys = build_system_prompt(available_ids=["bob", "alice", "carol"])

    assert "Available persona ids" in sys
    # Sorted alphabetically
    assert sys.index("alice") < sys.index("bob") < sys.index("carol")
    # Output rules
    assert "no code fences" in sys.lower()
    assert "1 to 12 personas" in sys


def test_build_user_message_wraps_current_and_instruction():
    from lean_agent.prompts.preset_edit import build_user_message

    msg = build_user_message(current_content="- alice\n- bob\n", instruction="add carol")

    assert "<current_file>" in msg
    assert "- alice" in msg
    assert "<instruction>" in msg
    assert "add carol" in msg
