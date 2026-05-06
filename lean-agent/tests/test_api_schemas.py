import pytest


def test_persona_draft_request_validates_instruction_length():
    from lean_agent.api_schemas import PersonaDraftRequest
    from pydantic import ValidationError

    PersonaDraftRequest(target_id="alice", instruction="x")  # ok
    PersonaDraftRequest(target_id=None, instruction="create")  # ok create-mode

    with pytest.raises(ValidationError):
        PersonaDraftRequest(target_id="alice", instruction="")  # too short

    with pytest.raises(ValidationError):
        PersonaDraftRequest(target_id="alice", instruction="x" * 2001)  # too long


def test_persona_create_request_validates_id_slug():
    from lean_agent.api_schemas import PersonaCreateRequest
    from pydantic import ValidationError

    PersonaCreateRequest(id="alice", content="x")  # ok
    PersonaCreateRequest(id="alice-saas-pm", content="x")  # ok with hyphens

    with pytest.raises(ValidationError):
        PersonaCreateRequest(id="Alice", content="x")  # uppercase rejected

    with pytest.raises(ValidationError):
        PersonaCreateRequest(id="-alice", content="x")  # leading hyphen rejected

    with pytest.raises(ValidationError):
        PersonaCreateRequest(id="alice-", content="x")  # trailing hyphen rejected

    with pytest.raises(ValidationError):
        PersonaCreateRequest(id="a", content="x")  # too short (regex requires >=2 chars)


def test_persona_to_summary_dto():
    from lean_agent.api_mappers import persona_to_summary_dto
    from lean_agent.personas.loader import Persona

    p = Persona(
        id="alice", name="Alice", metadata={"role": "Tester"},
        backstory="x", beliefs="y", biases="z", how_she_answers="w", raw_path=None,
    )
    dto = persona_to_summary_dto(p)
    assert dto.id == "alice"
    assert dto.name == "Alice"
    assert dto.role == "Tester"


def test_persona_to_summary_dto_missing_role():
    from lean_agent.api_mappers import persona_to_summary_dto
    from lean_agent.personas.loader import Persona

    p = Persona(
        id="alice", name="Alice", metadata={},
        backstory="x", beliefs="y", biases="z", how_she_answers="w", raw_path=None,
    )
    dto = persona_to_summary_dto(p)
    assert dto.role is None


def test_persona_to_detail_dto_carries_raw_content():
    from lean_agent.api_mappers import persona_to_detail_dto
    from lean_agent.personas.loader import Persona

    p = Persona(
        id="alice", name="Alice", metadata={"role": "Tester"},
        backstory="b", beliefs="bel", biases="bi", how_she_answers="h", raw_path=None,
    )
    dto = persona_to_detail_dto(p, raw_content="RAW")
    assert dto.id == "alice"
    assert dto.raw_content == "RAW"
    assert dto.backstory == "b"


def test_preset_to_summary_dto():
    from lean_agent.api_mappers import preset_to_summary_dto
    from lean_agent.panel_presets.loader import Preset

    p = Preset(name="smb-saas", persona_ids=["alice", "bob"], raw_path=None)
    dto = preset_to_summary_dto(p)
    assert dto.name == "smb-saas"
    assert dto.persona_count == 2


def test_preset_to_detail_dto():
    from lean_agent.api_mappers import preset_to_detail_dto
    from lean_agent.panel_presets.loader import Preset

    p = Preset(name="smb-saas", persona_ids=["alice", "bob"], raw_path=None)
    dto = preset_to_detail_dto(p, raw_content="- alice\n- bob\n")
    assert dto.name == "smb-saas"
    assert dto.persona_ids == ["alice", "bob"]
    assert dto.raw_content == "- alice\n- bob\n"
