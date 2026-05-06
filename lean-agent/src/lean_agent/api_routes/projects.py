"""Read-only project routes."""
from __future__ import annotations

from fastapi import APIRouter, Path

from lean_agent.api_mappers import project_to_summary, tree_to_detail
from lean_agent.api_schemas import ProjectDetail, ProjectSummary
from lean_agent.commands.list_projects import list_projects
from lean_agent.commands.read_research_tree import read_research_tree

SLUG_PATTERN = r"^[a-z0-9-]+$"

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects_endpoint() -> list[ProjectSummary]:
    return [project_to_summary(p) for p in list_projects()]


@router.get("/{slug}", response_model=ProjectDetail)
def get_project_endpoint(slug: str = Path(..., pattern=SLUG_PATTERN)) -> ProjectDetail:
    tree = read_research_tree(slug)
    return tree_to_detail(tree)
