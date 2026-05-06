from datetime import date

from lean_agent import paths
from lean_agent.commands._state import update_active_block
from lean_agent.git_ops import commit_all


def promote(*, slug: str, hypothesis_id: str, today: date) -> None:
    update_active_block(
        slug,
        hypothesis_id,
        status="✅ ready-for-real-interviews",
        decision="🚀 Promote",
        key_learning=f"Survived simulation on {today.isoformat()}; export-kit recommended.",
        evidence=f"see synthesis.md in {hypothesis_id}-*/",
    )
    commit_all(paths.project_dir(slug), f"promote: {hypothesis_id} ready for real interviews")
