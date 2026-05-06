from pathlib import Path

from git.objects.util import Actor
from git.repo.base import Repo


# Per library-notes §gitpython: machines without global git config will fail
# index.commit() unless an Actor is supplied. Use a project-local identity.
#
# v0 design choice: ALL commits are attributed to this actor. Users editing markdown
# by hand and committing via `git commit` themselves will see "lean-agent" as the
# author in `git log`. This is intentional for v0; v0.3+ may add per-source actor
# attribution if dogfood reveals friction.
_LEAN_AGENT_ACTOR = Actor("lean-agent", "lean-agent@local")


def init_repo(path: Path) -> Repo:
    path.mkdir(parents=True, exist_ok=True)
    if (path / ".git").is_dir():
        return Repo(path)
    repo = Repo.init(path, initial_branch="main")
    return repo


def has_repo(path: Path) -> bool:
    return (path / ".git").is_dir()


def commit_all(path: Path, message: str) -> str | None:
    """Stage every change in `path` (including deletions) and commit. Returns sha or None if nothing changed."""
    # init_repo is idempotent — opens the existing repo if `.git/` is present, else inits.
    repo = init_repo(path)
    repo.git.add(A=True)  # stages adds, modifications, AND deletions
    # is_dirty(untracked_files=True) per library-notes: default excludes untracked.
    has_index_diff = bool(repo.index.diff("HEAD" if repo.head.is_valid() else None))
    has_workdir_changes = repo.is_dirty(untracked_files=True)
    if not has_index_diff and not has_workdir_changes:
        return None
    commit = repo.index.commit(message, author=_LEAN_AGENT_ACTOR, committer=_LEAN_AGENT_ACTOR)
    return commit.hexsha
