def test_new_v0_3_exceptions_exist_and_carry_messages():
    from lean_agent.commands.errors import (
        PersonaNotFound,
        PersonaIdConflict,
        PersonaInUseByPreset,
        PresetNotFound,
        PresetNameConflict,
        LLMOutputInvalid,
    )

    e1 = PersonaNotFound("alice")
    assert e1.persona_id == "alice"
    assert "alice" in str(e1)

    e2 = PersonaIdConflict("alice")
    assert e2.persona_id == "alice"

    e3 = PersonaInUseByPreset("alice", referenced_by=["smb-saas", "creator"])
    assert e3.persona_id == "alice"
    assert e3.referenced_by == ["smb-saas", "creator"]

    e4 = PresetNotFound("smb-saas")
    assert e4.preset_name == "smb-saas"

    e5 = PresetNameConflict("smb-saas")
    assert e5.preset_name == "smb-saas"

    e6 = LLMOutputInvalid(["frontmatter missing", "section X empty"])
    assert e6.errors == ["frontmatter missing", "section X empty"]
