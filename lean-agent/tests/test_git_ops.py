from pathlib import Path

from lean_agent.git_ops import commit_all, has_repo, init_repo


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
