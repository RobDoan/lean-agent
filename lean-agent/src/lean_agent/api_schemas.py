"""Pydantic DTOs for the v0.2.0 read-only API. Mirrored as TS in lean-agent-ui/src/lib/types.ts."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectSummary(BaseModel):
    slug: str
    idea: str | None
    hypothesis_count: int
    run_count: int
    with_synthesis_count: int
    created_at: str  # ISO 8601


class HypothesisListItem(BaseModel):
    id: str
    title: str
    has_run: bool
    has_synthesis: bool
    interview_count: int


class ProjectDetail(BaseModel):
    slug: str
    idea: str | None
    idea_triage: list[str]
    hypotheses: list[HypothesisListItem]


class InterviewMeta(BaseModel):
    name: str       # basename without .md
    filename: str   # full filename including .md


class HypothesisDetail(BaseModel):
    id: str
    title: str
    synthesis_markdown: str | None
    sprint_markdown: str | None
    interviews: list[InterviewMeta]


class InterviewContent(BaseModel):
    name: str
    markdown: str


class HealthResponse(BaseModel):
    status: str
    version: str


# ----- v0.3 persona schemas -----


class PersonaSummary(BaseModel):
    id: str
    name: str
    role: str | None = None


class PersonaDetail(BaseModel):
    id: str
    name: str
    metadata: dict[str, str]
    backstory: str
    beliefs: str
    biases: str
    how_she_answers: str
    raw_content: str


class PersonaDraftRequest(BaseModel):
    target_id: str | None = None
    instruction: str = Field(min_length=1, max_length=2000)
    current_content: str | None = None


class PersonaCreateRequest(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", max_length=64)
    content: str = Field(min_length=1, max_length=20000)


class PersonaEditRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20000)


# ----- v0.3 panel-preset schemas -----


class PresetSummary(BaseModel):
    name: str
    persona_count: int
    description: str | None = None


class PresetDetail(BaseModel):
    name: str
    persona_ids: list[str]
    raw_content: str
    description: str | None = None


class PresetDraftRequest(BaseModel):
    target_name: str | None = None
    instruction: str = Field(min_length=1, max_length=2000)
    current_content: str | None = None


class PresetCreateRequest(BaseModel):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", max_length=64)
    content: str = Field(min_length=1, max_length=10000)


class PresetEditRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


# ----- v0.3.2 preset auto-generation schemas -----


class PresetAutoGenRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=2000)


class PresetPlanPersona(BaseModel):
    slug: str
    name: str
    description: str


class PresetPlan(BaseModel):
    description: str
    reuse: list[str]
    create: list[PresetPlanPersona]


class PresetConfirmRequest(BaseModel):
    plan: PresetPlan


# ----- v0.3.2 preset history schemas -----


class PresetHistoryEntry(BaseModel):
    sha: str
    message: str
    date: str


class PresetVersionContent(BaseModel):
    sha: str
    content: str
