from typing import Any

from lean_agent.prompts.system import GUARDRAILS


def build(*, hypothesis_statement: str) -> tuple[str, list[dict[str, Any]]]:
    user = f"""\
For the hypothesis:

> {hypothesis_statement}

Write a 5-7 question discussion guide for a 30-minute user interview. Rules:

- All questions must be open-ended and behaviour-focused ("Tell me about a time when…").
- No leading questions, no "would you" hypotheticals.
- One question per line. No numbering. No commentary.
"""
    return GUARDRAILS, [{"role": "user", "content": user}]
