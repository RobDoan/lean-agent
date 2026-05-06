"""Read-only interview-content route (lazy-loaded by the UI on expand)."""
from __future__ import annotations

from fastapi import APIRouter, Path

from lean_agent.api_schemas import InterviewContent
from lean_agent.api_routes.hypotheses import HID_PATTERN
from lean_agent.api_routes.projects import SLUG_PATTERN
from lean_agent.commands.read_interview_content import read_interview_content

NAME_PATTERN = r"^[a-z0-9-]+$"

router = APIRouter(
    prefix="/api/projects/{slug}/hypotheses/{hid}/interviews",
    tags=["interviews"],
)


@router.get("/{name}", response_model=InterviewContent)
def get_interview_endpoint(
    slug: str = Path(..., pattern=SLUG_PATTERN),
    hid: str = Path(..., pattern=HID_PATTERN),
    name: str = Path(..., pattern=NAME_PATTERN),
) -> InterviewContent:
    markdown = read_interview_content(slug, hid, name)
    return InterviewContent(name=name, markdown=markdown)
