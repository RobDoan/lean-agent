from importlib.resources import files
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def _template_dir() -> Path:
    return Path(str(files("lean_agent").joinpath("templates")))


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_template_dir())),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )


def render(template_name: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 template from the bundled templates/ dir."""
    return _env().get_template(template_name).render(**context)
