from lean_agent import paths, state


class ProjectNotFound(ValueError):
    """Raised when set_current is asked for a slug that doesn't exist."""


def set_current(slug: str) -> None:
    available = paths.list_project_slugs()
    if slug not in available:
        raise ProjectNotFound(f"project '{slug}' not found in {paths.projects_root()}")
    state.write_current_slug(slug)


def show_current() -> str | None:
    return state.read_current_slug()


def list_available() -> tuple[list[str], str | None]:
    return paths.list_project_slugs(), state.read_current_slug()
