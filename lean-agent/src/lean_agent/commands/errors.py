"""Domain errors raised by orchestration. Translated to HTTP at the API boundary."""


class LeanAgentDomainError(Exception):
    """Base class for domain errors."""


class ProjectNotFoundError(LeanAgentDomainError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Project not found: {slug}")
        self.slug = slug


class HypothesisNotFoundError(LeanAgentDomainError):
    def __init__(self, slug: str, hypothesis_id: str) -> None:
        super().__init__(f"Hypothesis not found: {slug}/{hypothesis_id}")
        self.slug = slug
        self.hypothesis_id = hypothesis_id


class InterviewNotFoundError(LeanAgentDomainError):
    def __init__(self, slug: str, hypothesis_id: str, name: str) -> None:
        super().__init__(f"Interview not found: {slug}/{hypothesis_id}/{name}")
        self.slug = slug
        self.hypothesis_id = hypothesis_id
        self.name = name


class PersonaNotFound(Exception):
    def __init__(self, persona_id: str) -> None:
        self.persona_id = persona_id
        super().__init__(f"persona not found: {persona_id}")


class PersonaIdConflict(Exception):
    def __init__(self, persona_id: str) -> None:
        self.persona_id = persona_id
        super().__init__(f"persona id already exists: {persona_id}")


class PersonaInUseByPreset(Exception):
    def __init__(self, persona_id: str, referenced_by: list[str]) -> None:
        self.persona_id = persona_id
        self.referenced_by = referenced_by
        super().__init__(
            f"persona {persona_id} is referenced by panel preset(s): {referenced_by}"
        )


class PresetNotFound(Exception):
    def __init__(self, preset_name: str) -> None:
        self.preset_name = preset_name
        super().__init__(f"panel preset not found: {preset_name}")


class PresetNameConflict(Exception):
    def __init__(self, preset_name: str) -> None:
        self.preset_name = preset_name
        super().__init__(f"panel preset name already exists: {preset_name}")


class LLMOutputInvalid(Exception):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"LLM output invalid: {errors}")
