from pathlib import Path

import pytest

from lean_agent.personas.loader import Persona, load_all, load_persona


SAMPLE = """---
id: sarah-test
name: Sarah Test
age: 34
role: Freelance designer
income: $80k/year
location: Portland, OR
---

## Backstory
Two years freelance.

## Beliefs
- Time is scarce.

## Biases
- Lies about checking invoices weekly.

## How she answers questions
- Story-driven.
"""


def test_load_persona(tmp_path: Path):
    p = tmp_path / "sarah-test.md"
    p.write_text(SAMPLE)
    persona = load_persona(p)
    assert isinstance(persona, Persona)
    assert persona.id == "sarah-test"
    assert persona.name == "Sarah Test"
    assert persona.metadata["role"] == "Freelance designer"
    assert "Story-driven" in persona.how_she_answers


def test_load_persona_missing_frontmatter_raises(tmp_path: Path):
    p = tmp_path / "broken.md"
    p.write_text("just a body\n")
    with pytest.raises(ValueError, match="frontmatter"):
        load_persona(p)


def test_load_all_skips_underscore_files(tmp_path: Path):
    (tmp_path / "real.md").write_text(SAMPLE)
    (tmp_path / "_killed-ideas.md").write_text("# notes\n")
    (tmp_path / "_panel-presets").mkdir()
    out = load_all(tmp_path)
    assert [p.id for p in out] == ["sarah-test"]


def test_starter_personas_all_load():
    from importlib.resources import files

    from lean_agent.personas.loader import load_all

    starter = Path(str(files("lean_agent.personas").joinpath("starter")))
    out = load_all(starter)
    assert {p.id for p in out} == {
        "sarah-freelance-designer",
        "mike-saas-pm",
        "jamie-ecom-founder",
        "alex-engineering-manager",
        "priya-marketing-lead",
    }


def test_starter_panel_presets_exist():
    from importlib.resources import files

    presets = Path(str(files("lean_agent.personas").joinpath("starter/_panel-presets")))
    names = {p.stem for p in presets.glob("*.md")}
    assert {"smb-saas", "creator-economy", "enterprise-pm"}.issubset(names)


def test_load_persona_handles_crlf_and_bom(tmp_path: Path):
    """A persona file saved with Windows CRLF + UTF-8 BOM must still parse."""
    from lean_agent.personas.loader import load_persona

    body = (
        "---\n"
        "id: windows-sarah\n"
        "name: Sarah Windows\n"
        "---\n"
        "\n"
        "## Backstory\n"
        "Saved on Windows.\n"
        "\n"
        "## Beliefs\n"
        "- x\n"
        "\n"
        "## Biases\n"
        "- y\n"
        "\n"
        "## How she answers questions\n"
        "- z\n"
    )
    crlf = body.replace("\n", "\r\n")
    p = tmp_path / "windows-sarah.md"
    p.write_bytes(b"\xef\xbb\xbf" + crlf.encode("utf-8"))  # UTF-8 BOM + CRLF

    persona = load_persona(p)
    assert persona.id == "windows-sarah"
    assert persona.name == "Sarah Windows"
    assert "Saved on Windows." in persona.backstory


def test_load_persona_from_str_parses_valid_content():
    from lean_agent.personas.loader import load_persona_from_str

    text = """---
id: test-id
name: Test Person
role: Tester
---

## Backstory
Some backstory.

## Beliefs
- Believes things.

## Biases
- Has biases.

## How she answers questions
Direct.
"""
    persona = load_persona_from_str(text)

    assert persona.id == "test-id"
    assert persona.name == "Test Person"
    assert persona.metadata["role"] == "Tester"
    assert persona.backstory == "Some backstory."
    assert "Believes things." in persona.beliefs
    assert persona.raw_path is None  # signals in-memory parse


def test_load_persona_from_str_raises_on_missing_frontmatter():
    from lean_agent.personas.loader import load_persona_from_str

    with pytest.raises(ValueError, match="frontmatter"):
        load_persona_from_str("no frontmatter here")


def test_load_persona_from_str_raises_on_missing_id():
    from lean_agent.personas.loader import load_persona_from_str

    text = """---
name: No Id
---

## Backstory
x

## Beliefs
x

## Biases
x

## How she answers questions
x
"""
    with pytest.raises(KeyError):
        load_persona_from_str(text)
