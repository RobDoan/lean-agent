from pathlib import Path

from lean_agent.paths import (
    personas_root,
    projects_root,
    project_dir,
    research_dir,
    hypothesis_list_path,
    hypothesis_dir,
    project_roadmap_path,
    project_readme_path,
)


def test_personas_root_default(tmp_home: Path):
    assert personas_root() == tmp_home / ".lean-agent" / "personas"


def test_projects_root_default(tmp_home: Path):
    assert projects_root() == tmp_home / ".lean-agent" / "projects"


def test_project_dir(tmp_home: Path):
    assert project_dir("my-idea") == tmp_home / ".lean-agent" / "projects" / "my-idea"


def test_hypothesis_list_path(tmp_home: Path):
    p = hypothesis_list_path("my-idea")
    assert (
        p
        == tmp_home
        / ".lean-agent"
        / "projects"
        / "my-idea"
        / "01-research"
        / "00-hypothesis-list.md"
    )


def test_hypothesis_dir(tmp_home: Path):
    p = hypothesis_dir("my-idea", "H1", "personalized-onboarding")
    assert (
        p
        == tmp_home
        / ".lean-agent"
        / "projects"
        / "my-idea"
        / "01-research"
        / "H1-personalized-onboarding"
    )


def test_research_dir(tmp_home: Path):
    assert (
        research_dir("my-idea") == tmp_home / ".lean-agent" / "projects" / "my-idea" / "01-research"
    )


def test_project_roadmap_path(tmp_home: Path):
    assert (
        project_roadmap_path("my-idea")
        == tmp_home / ".lean-agent" / "projects" / "my-idea" / "ROADMAP.md"
    )


def test_project_readme_path(tmp_home: Path):
    assert (
        project_readme_path("my-idea")
        == tmp_home / ".lean-agent" / "projects" / "my-idea" / "README.md"
    )


def test_list_project_slugs_returns_empty_when_root_missing(tmp_home: Path):
    from lean_agent.paths import list_project_slugs

    assert list_project_slugs() == []


def test_list_project_slugs_returns_sorted_dirs_only(tmp_home: Path):
    from lean_agent.paths import list_project_slugs, projects_root

    root = projects_root()
    root.mkdir(parents=True)
    (root / "zeta").mkdir()
    (root / "alpha").mkdir()
    (root / "beta").mkdir()
    (root / "not-a-project.md").write_text("", encoding="utf-8")  # file, must be skipped
    assert list_project_slugs() == ["alpha", "beta", "zeta"]


def test_list_project_slugs_returns_empty_when_root_has_only_files(tmp_home: Path):
    from lean_agent.paths import list_project_slugs, projects_root

    root = projects_root()
    root.mkdir(parents=True)
    (root / "stray.txt").write_text("", encoding="utf-8")
    assert list_project_slugs() == []


def test_hypothesis_dir_glob_returns_first_match(tmp_home: Path) -> None:
    from lean_agent.paths import hypothesis_dir_glob, research_dir

    research = research_dir("test-project")
    research.mkdir(parents=True)
    (research / "H1-we-believe-foo").mkdir()
    (research / "H1-modern-slug").mkdir()

    result = hypothesis_dir_glob("test-project", "H1")
    assert result is not None
    assert result.name in ("H1-modern-slug", "H1-we-believe-foo")  # sorted-first


def test_hypothesis_dir_glob_returns_none_when_absent(tmp_home: Path) -> None:
    from lean_agent.paths import hypothesis_dir_glob

    assert hypothesis_dir_glob("missing-project", "H1") is None


def test_interviews_dir_resolves_under_hypothesis(tmp_home: Path) -> None:
    from lean_agent.paths import interviews_dir, research_dir

    research = research_dir("test-project")
    research.mkdir(parents=True)
    (research / "H1-foo").mkdir()

    result = interviews_dir("test-project", "H1-foo")
    assert result == research / "H1-foo" / "interviews"


def test_interview_path_appends_md_suffix(tmp_home: Path) -> None:
    from lean_agent.paths import interview_path

    p = interview_path("test-project", "H1-foo", "alex-2026-05-04")
    assert p.name == "alex-2026-05-04.md"
    assert p.parent.name == "interviews"


def test_ensure_templates_copies_when_absent(tmp_path: Path, monkeypatch):
    from lean_agent import paths

    monkeypatch.setattr(paths, "lean_agent_home", lambda: tmp_path)

    paths.ensure_templates()

    assert (tmp_path / "personas" / "_template_persona.md").exists()
    assert (tmp_path / "personas" / "_template_preset.md").exists()


def test_ensure_templates_idempotent(tmp_path: Path, monkeypatch):
    from lean_agent import paths

    monkeypatch.setattr(paths, "lean_agent_home", lambda: tmp_path)

    persona_template = tmp_path / "personas" / "_template_persona.md"
    persona_template.parent.mkdir(parents=True)
    persona_template.write_text("user-customised template")

    paths.ensure_templates()

    assert persona_template.read_text() == "user-customised template"  # not overwritten
