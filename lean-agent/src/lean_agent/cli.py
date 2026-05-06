from datetime import date
from typing import Annotated

import click
import typer
from typer.core import TyperGroup

from lean_agent import __version__, paths, state
from lean_agent.commands._layout import LegacyHomeLayoutError, check_legacy_layout
from lean_agent.commands.export_kit import export_kit as cmd_export_kit
from lean_agent.commands.init import init_project as cmd_init
from lean_agent.commands.kill import kill as cmd_kill
from lean_agent.commands.promote import promote as cmd_promote
from lean_agent.commands.revise import revise as cmd_revise
from lean_agent.commands.run_r1 import run_r1 as cmd_run_r1
from lean_agent.commands.use import (
    ProjectNotFound,
    list_available as cmd_list_available,
    set_current as cmd_set_current,
    show_current as cmd_show_current,
)
from lean_agent.llm import AnthropicLLMClient


def _resolve_slug(explicit: str | None) -> str:
    """Resolve the project slug for a command. Precedence: explicit > stored > error.

    Both branches validate against `cmd_list_available()` so a typo on either side
    surfaces as a friendly typer.BadParameter, not a downstream FileNotFoundError.
    """
    try:
        slugs, current = cmd_list_available()
    except state.StateFileCorrupt as e:
        raise typer.BadParameter(str(e)) from e
    if explicit is not None:
        if explicit not in slugs:
            raise typer.BadParameter(
                f"project '{explicit}' not found in {paths.projects_root()} "
                f"— run 'lean use list' to see available projects"
            )
        return explicit
    if current is None:
        raise typer.BadParameter("no project context — use --slug <s> or 'lean use <s>'")
    if current not in slugs:
        raise typer.BadParameter(
            f"current project '{current}' not found in {paths.projects_root()} "
            f"— run 'lean use <other>' or pass --slug"
        )
    return current


app = typer.Typer(
    help="Lean Startup Agent — pre-filter hypotheses, rehearse interviews, export real-interview kit."
)


@app.callback()
def _root() -> None:
    """Root callback — fires before every subcommand. Aborts the run if the user
    is on legacy v0.1.0 home-dir layout (~/.lean-personas/ or ~/lean-projects/).

    Click handles --help before this callback runs, so `lean --help` is not
    blocked by the legacy-layout check.
    """
    try:
        check_legacy_layout()
    except LegacyHomeLayoutError as e:
        raise typer.BadParameter(str(e)) from e


run_app = typer.Typer(help="Run a phase for a hypothesis.")
app.add_typer(run_app, name="run")


class _SubcommandFirstGroup(TyperGroup):
    """Dispatch a registered sub-command name before consuming the optional positional.

    Without this, `lean use list` would have Click 8.2 greedily bind `list` to the
    callback's `slug` argument, never reaching the `list` sub-command.

    Couples to Click 8.2 internals (`ctx._protected_args` is the documented handoff
    between `Group.parse_args` and `Group.invoke`, but is not public API). Re-verify
    on any Click major bump (the dep range is currently locked via typer>=0.25,<0.26).
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if args and args[0] in self.commands:
            for p in self.params:
                if p.name is not None:
                    ctx.params.setdefault(p.name, p.get_default(ctx))
            ctx._protected_args = [args[0]]
            ctx.args = list(args[1:])
            ctx.invoked_subcommand = args[0]
            return ctx.args
        return super().parse_args(ctx, args)


use_app = typer.Typer(help="Manage current project context.")
app.add_typer(use_app, name="use", invoke_without_command=True, cls=_SubcommandFirstGroup)


@use_app.callback(invoke_without_command=True)
def use_root(
    ctx: typer.Context,
    slug: Annotated[
        str | None,
        typer.Argument(help="Project slug to set as current. Omit to print current."),
    ] = None,
) -> None:
    """Set, show, or list the current project."""
    if ctx.invoked_subcommand is not None:
        return  # delegate to sub-command (e.g., `list`)
    if slug is None:
        try:
            current = cmd_show_current()
        except state.StateFileCorrupt as e:
            raise typer.BadParameter(str(e)) from e
        if current is None:
            typer.echo("no project set", err=True)
        else:
            typer.echo(current)
        return
    try:
        cmd_set_current(slug)
    except ProjectNotFound as e:
        raise typer.BadParameter(str(e)) from e
    typer.echo(f"current: {slug}")


@use_app.command("list")
def use_list() -> None:
    """List available projects, marking the current one with `* `."""
    try:
        slugs, current = cmd_list_available()
    except state.StateFileCorrupt as e:
        raise typer.BadParameter(str(e)) from e
    for s in slugs:
        prefix = "* " if s == current else "  "
        typer.echo(f"{prefix}{s}")


@app.command()
def version() -> None:
    """Print the lean-agent version."""
    typer.echo(__version__)


@app.command()
def init(
    idea: Annotated[str, typer.Argument(help="The idea description (quote it).")],
    owner: Annotated[str, typer.Option(help="Project owner")] = "me",
) -> None:
    """Create a new project with a pre-filtered hypothesis list."""
    try:
        llm = AnthropicLLMClient()
        slug = cmd_init(
            idea=idea,
            llm=llm,
            today=date.today(),
            owner=owner,
            progress=lambda msg: typer.echo(f"→ {msg}", err=True),
        )
    except RuntimeError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except FileExistsError as e:
        raise typer.BadParameter(str(e)) from e
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e
    typer.echo(f"created: {paths.project_dir(slug)}")


@run_app.command("R1")
def run_r1(
    hypothesis_id: Annotated[str, typer.Argument(metavar="H<n>")],
    slug: Annotated[
        str | None, typer.Option("--slug", help="Project slug (overrides current).")
    ] = None,
    panel: Annotated[str | None, typer.Option(help="Named panel preset")] = None,
    personas: Annotated[str | None, typer.Option(help="Comma-separated persona ids")] = None,
    n: Annotated[int, typer.Option(help="Default panel size when no preset/ids")] = 5,
) -> None:
    """Simulate R1 for one hypothesis."""
    resolved_slug = _resolve_slug(slug)
    try:
        llm = AnthropicLLMClient()
        h_dir = cmd_run_r1(
            slug=resolved_slug,
            hypothesis_id=hypothesis_id,
            llm=llm,
            today=date.today(),
            panel_name=panel,
            panel_ids=personas,
            n=n,
            progress=lambda msg: typer.echo(f"→ {msg}", err=True),
        )
    except RuntimeError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e
    typer.echo(f"wrote: {h_dir}")


@app.command()
def promote(
    hypothesis_id: Annotated[str, typer.Argument()],
    slug: Annotated[
        str | None, typer.Option("--slug", help="Project slug (overrides current).")
    ] = None,
) -> None:
    """Mark a hypothesis ready for real interviews."""
    resolved_slug = _resolve_slug(slug)
    cmd_promote(slug=resolved_slug, hypothesis_id=hypothesis_id, today=date.today())
    typer.echo(f"promoted: {hypothesis_id}")


@app.command()
def revise(
    hypothesis_id: Annotated[str, typer.Argument()],
    note: Annotated[str, typer.Option(help="Why revise — appears in §3 Key Learning")],
    slug: Annotated[
        str | None, typer.Option("--slug", help="Project slug (overrides current).")
    ] = None,
) -> None:
    """Send a hypothesis back to the backlog with a note."""
    resolved_slug = _resolve_slug(slug)
    cmd_revise(slug=resolved_slug, hypothesis_id=hypothesis_id, note=note, today=date.today())
    typer.echo(f"revised: {hypothesis_id}")


@app.command()
def kill(
    hypothesis_id: Annotated[str, typer.Argument()],
    note: Annotated[str, typer.Option(help="Funeral note — what we learned")],
    slug: Annotated[
        str | None, typer.Option("--slug", help="Project slug (overrides current).")
    ] = None,
) -> None:
    """Kill a hypothesis with a funeral note."""
    resolved_slug = _resolve_slug(slug)
    cmd_kill(slug=resolved_slug, hypothesis_id=hypothesis_id, note=note, today=date.today())
    typer.echo(f"💀 killed: {hypothesis_id}")


@app.command("export-kit")
def export_kit(
    hypothesis_id: Annotated[str, typer.Argument()],
    slug: Annotated[
        str | None, typer.Option("--slug", help="Project slug (overrides current).")
    ] = None,
) -> None:
    """Produce the 4-file real-interview packet."""
    resolved_slug = _resolve_slug(slug)
    project_readme = (paths.project_dir(resolved_slug) / "README.md").read_text(encoding="utf-8")
    idea_line = next(
        (line for line in project_readme.splitlines() if line.startswith("# ")), "# (unknown)"
    )
    idea = idea_line.removeprefix("# ").strip()
    out = cmd_export_kit(
        slug=resolved_slug, hypothesis_id=hypothesis_id, today=date.today(), idea=idea
    )
    typer.echo(f"kit: {out}")
