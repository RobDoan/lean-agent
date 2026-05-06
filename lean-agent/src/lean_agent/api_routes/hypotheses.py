"""Read-only hypothesis routes."""
from __future__ import annotations

from fastapi import APIRouter, Path

from lean_agent.api_mappers import hypothesis_to_detail
from lean_agent.api_schemas import HypothesisDetail
from lean_agent.api_routes.projects import SLUG_PATTERN
from lean_agent.commands.read_hypothesis_detail import read_hypothesis_detail

HID_PATTERN = r"^H\d+$"

router = APIRouter(prefix="/api/projects/{slug}/hypotheses", tags=["hypotheses"])


@router.get("/{hid}", response_model=HypothesisDetail)
def get_hypothesis_endpoint(
    slug: str = Path(..., pattern=SLUG_PATTERN),
    hid: str = Path(..., pattern=HID_PATTERN),
) -> HypothesisDetail:
    detail = read_hypothesis_detail(slug, hid)
    return hypothesis_to_detail(
        detail.hypothesis,
        synthesis_markdown=detail.synthesis_markdown,
        sprint_markdown=detail.sprint_markdown,
        interviews=detail.interviews,
    )
