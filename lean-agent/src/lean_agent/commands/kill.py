from datetime import date

from lean_agent import paths
from lean_agent.commands._state import update_active_block
from lean_agent.git_ops import commit_all


def kill(*, slug: str, hypothesis_id: str, note: str, today: date) -> None:
    update_active_block(
        slug,
        hypothesis_id,
        status="💀 Killed (simulated)",
        decision="💀 Kill",
        key_learning=f"{today.isoformat()}: {note}",
        evidence=f"see synthesis.md in {hypothesis_id}-*/",
    )
    commit_all(paths.project_dir(slug), f"kill: {hypothesis_id} ({note[:50]})")
