import re

from lean_agent import paths


def update_active_block(
    slug: str,
    hypothesis_id: str,
    *,
    status: str,
    decision: str,
    key_learning: str,
    evidence: str,
) -> None:
    """Rewrite the four bullet lines of an §3 active block. Heading line is preserved.

    Expected block shape (must match commands/run_r1.py output):
        ### H<n> — <statement>\\n
        \\n
        - **Status:** ...\\n
        - **Decision:** ...\\n
        - **Key Learning:** ...\\n
        - **Evidence:** ...\\n
    """
    hl_path = paths.hypothesis_list_path(slug)
    text = hl_path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(### {re.escape(hypothesis_id)} — [^\n]+\n)\n((?:- \*\*[^\n]+\n){{1,8}})",
        re.MULTILINE,
    )
    new_block_body = (
        f"- **Status:** {status}\n"
        f"- **Decision:** {decision}\n"
        f"- **Key Learning:** {key_learning}\n"
        f"- **Evidence:** {evidence}\n"
    )
    new_text, n = pattern.subn(lambda m: m.group(1) + "\n" + new_block_body, text, count=1)
    if n == 0:
        raise ValueError(f"§3 active block for {hypothesis_id} not found")
    hl_path.write_text(new_text, encoding="utf-8")
