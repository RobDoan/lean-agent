from collections.abc import Callable
from datetime import date
from importlib.resources import files
from pathlib import Path

from lean_agent import paths, state
from lean_agent._text import parse_first_json_object
from lean_agent.git_ops import commit_all, init_repo
from lean_agent.llm import LLMClient, LLMRequest
from lean_agent.prompts.init_hypotheses import build as build_init
from lean_agent.render import render
from lean_agent.slugify import slugify_idea


def _ensure_personas_seeded() -> None:
    """First-run UX: if ~/.lean-agent/personas/ is empty, copy bundled starters + presets."""
    target = paths.personas_root()
    if target.exists() and any(target.glob("*.md")):
        return
    target.mkdir(parents=True, exist_ok=True)
    starter_root = Path(str(files("lean_agent.personas").joinpath("starter")))
    for f in starter_root.glob("*.md"):
        (target / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    presets_src = starter_root / "_panel-presets"
    presets_dst = target / "_panel-presets"
    presets_dst.mkdir(exist_ok=True)
    for f in presets_src.glob("*.md"):
        (presets_dst / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")


def init_project(
    *,
    idea: str,
    llm: LLMClient,
    today: date,
    owner: str,
    progress: Callable[[str], None] | None = None,
) -> str:
    def _emit(msg: str) -> None:
        if progress is not None:
            progress(msg)

    slug = slugify_idea(idea)
    if not slug:
        raise ValueError(
            "idea text produced an empty slug; provide a non-empty English description"
        )
    proj = paths.project_dir(slug)
    if proj.exists():
        raise FileExistsError(f"project already exists: {proj}")

    # All operations that can fail (LLM call, JSON parse) happen BEFORE any
    # project-filesystem mutation, so a failed init doesn't leave a half-created
    # directory that blocks retry. Persona seeding is idempotent and lives outside
    # the project tree, so it's safe to run before the LLM call.
    _ensure_personas_seeded()

    _emit("generating hypotheses...")
    system, messages = build_init(idea=idea)
    resp = llm.complete(LLMRequest(system=system, messages=messages))
    data = parse_first_json_object(resp.text)

    # Markdown tables use `|` as cell separator. Replace any `|` an LLM put in a
    # hypothesis statement with `/` so the table renders and `_HYP_ROW` parses correctly.
    for h in data.get("hypotheses", []):
        if "statement" in h:
            h["statement"] = h["statement"].replace("|", "/")

    proj.mkdir(parents=True)
    (proj / "01-research").mkdir()

    today_str = today.isoformat()
    hl = render(
        "hypothesis_list.md.j2",
        {
            "idea": idea,
            "slug": slug,
            "owner": owner,
            "today": today_str,
            "idea_angles": data["idea_angles"],
            "hypotheses": data["hypotheses"],
            "active_entries": [],
            "validated": [],
            "invalidated": [],
            "inconclusive": [],
        },
    )
    paths.hypothesis_list_path(slug).write_text(hl, encoding="utf-8")

    paths.project_readme_path(slug).write_text(
        render("project_readme.md.j2", {"idea": idea, "slug": slug, "today": today_str}),
        encoding="utf-8",
    )
    paths.project_roadmap_path(slug).write_text(
        render(
            "project_roadmap.md.j2",
            {
                "idea": idea,
                "today": today_str,
                "active": [],
                "concluded": [],
                "promoted": [],
                "next_up": data["hypotheses"],
            },
        ),
        encoding="utf-8",
    )

    init_repo(proj)
    commit_all(proj, f'init: pre-filtered hypothesis list for "{idea}"')
    _emit(f"wrote: {proj}")
    state.write_current_slug(slug)
    _emit(f"set current project: {slug}")
    return slug
