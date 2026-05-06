import pytest
from jinja2 import UndefinedError

from lean_agent.render import render


def test_render_inline_template_via_environment(tmp_path, monkeypatch):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "hello.md.j2").write_text("Hello, {{ name }}!")
    monkeypatch.setattr("lean_agent.render._template_dir", lambda: template_dir)
    assert render("hello.md.j2", {"name": "Sarah"}) == "Hello, Sarah!"


def test_render_preserves_trailing_newline(tmp_path, monkeypatch):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "x.md.j2").write_text("a\n")
    monkeypatch.setattr("lean_agent.render._template_dir", lambda: template_dir)
    assert render("x.md.j2", {}).endswith("\n")  # rendered output preserves trailing newline


def test_render_for_loop_does_not_emit_blank_lines(tmp_path, monkeypatch):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "list.md.j2").write_text(
        "Items:\n{% for x in xs %}- {{ x }}\n{% endfor %}done\n"
    )
    monkeypatch.setattr("lean_agent.render._template_dir", lambda: template_dir)
    out = render("list.md.j2", {"xs": ["a", "b"]})
    assert out == "Items:\n- a\n- b\ndone\n"


def test_render_raises_on_missing_var(tmp_path, monkeypatch):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "x.md.j2").write_text("Hello, {{ missing }}!")
    monkeypatch.setattr("lean_agent.render._template_dir", lambda: template_dir)
    with pytest.raises(UndefinedError):
        render("x.md.j2", {})


def test_all_bundled_templates_load():
    """Every shipped template must be loadable via the real env."""
    from lean_agent.render import _env

    env = _env()
    expected = [
        "hypothesis_list.md.j2",
        "problem_validation_sprint.md.j2",
        "synthesis.md.j2",
        "transcript.md.j2",
        "project_readme.md.j2",
        "project_roadmap.md.j2",
        "interview_kit/discussion_guide.md.j2",
        "interview_kit/recruiting_criteria.md.j2",
        "interview_kit/consent_form.md.j2",
        "interview_kit/transcript_template.md.j2",
    ]
    for name in expected:
        env.get_template(name)


def test_discussion_guide_handles_questions_without_leading_warning():
    """A question dict missing 'leading_warning' must not crash under StrictUndefined."""
    from lean_agent.render import render

    out = render(
        "interview_kit/discussion_guide.md.j2",
        {
            "hypothesis": {"id": "H1", "statement": "test"},
            "today": "2026-05-02",
            "questions": [
                {"text": "Tell me about your week"},  # no leading_warning, no rephrase
                {"text": "Walk me through your last invoice"},
            ],
        },
    )
    # Each question on its own visual block (blank line between them).
    assert "**1. Tell me about your week**" in out
    assert "**2. Walk me through your last invoice**" in out
    assert "Possibly leading" not in out


def test_discussion_guide_renders_leading_warning_when_present():
    from lean_agent.render import render

    out = render(
        "interview_kit/discussion_guide.md.j2",
        {
            "hypothesis": {"id": "H1", "statement": "test"},
            "today": "2026-05-02",
            "questions": [
                {
                    "text": "Would you pay for this?",
                    "leading_warning": True,
                    "rephrase": "Tell me about a recent time you paid for a tool like this.",
                },
            ],
        },
    )
    assert "Possibly leading" in out
    assert "Tell me about a recent time" in out
