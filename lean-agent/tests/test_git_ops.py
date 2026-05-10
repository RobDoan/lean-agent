from pathlib import Path

from lean_agent.git_ops import commit_all, file_at_revision, file_history, has_repo, init_repo


def test_init_creates_repo(tmp_path: Path):
    init_repo(tmp_path / "proj")
    assert has_repo(tmp_path / "proj")
    assert (tmp_path / "proj" / ".git").is_dir()


def test_commit_all_records_files(tmp_path: Path):
    proj = tmp_path / "proj"
    init_repo(proj)
    (proj / "a.md").write_text("hello\n")
    sha = commit_all(proj, "feat: add a")
    assert isinstance(sha, str) and len(sha) >= 7

    from git import Repo

    repo = Repo(proj)
    assert any("feat: add a" in c.message for c in repo.iter_commits())


def test_commit_all_no_changes_returns_none(tmp_path: Path):
    proj = tmp_path / "proj"
    init_repo(proj)
    assert commit_all(proj, "noop") is None


def test_commit_all_stages_deletions(tmp_path: Path):
    """Per library-notes: `git add -A` (not index.add(...)) is required to stage deletions."""
    proj = tmp_path / "proj"
    init_repo(proj)
    f = proj / "x.md"
    f.write_text("v1")
    commit_all(proj, "init x")
    f.unlink()
    sha = commit_all(proj, "remove x")
    assert sha is not None  # the deletion was actually staged + committed


def test_file_history_returns_commits_for_file(tmp_path: Path):
    proj = tmp_path / "proj"
    init_repo(proj)
    f = proj / "a.md"
    f.write_text("v1")
    commit_all(proj, "create a")
    f.write_text("v2")
    commit_all(proj, "update a")

    history = file_history(proj, "a.md")
    assert len(history) == 2
    assert history[0]["message"] == "update a"
    assert history[1]["message"] == "create a"
    assert "sha" in history[0]
    assert "date" in history[0]


def test_file_history_empty_for_no_repo(tmp_path: Path):
    assert file_history(tmp_path / "nope", "x.md") == []


def test_file_history_empty_for_untracked_file(tmp_path: Path):
    proj = tmp_path / "proj"
    init_repo(proj)
    (proj / "a.md").write_text("v1")
    commit_all(proj, "init")
    assert file_history(proj, "nonexistent.md") == []


def test_file_at_revision_returns_content(tmp_path: Path):
    proj = tmp_path / "proj"
    init_repo(proj)
    f = proj / "a.md"
    f.write_text("v1")
    sha1 = commit_all(proj, "create a")
    f.write_text("v2")
    commit_all(proj, "update a")

    content = file_at_revision(proj, "a.md", sha1[:8])
    assert content == "v1"


def test_file_at_revision_returns_none_for_bad_sha(tmp_path: Path):
    proj = tmp_path / "proj"
    init_repo(proj)
    (proj / "a.md").write_text("v1")
    commit_all(proj, "init")
    assert file_at_revision(proj, "a.md", "0000000") is None


def test_file_at_revision_no_repo(tmp_path: Path):
    assert file_at_revision(tmp_path / "nope", "x.md", "abc1234") is None
