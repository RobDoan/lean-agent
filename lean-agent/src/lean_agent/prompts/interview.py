from typing import Any

from lean_agent.prompts.system import GUARDRAILS


def build(
    *, persona_md: str, hypothesis_statement: str, questions: list[str]
) -> tuple[str, list[dict[str, Any]]]:
    questions_block = "\n".join(f"- {q}" for q in questions)
    user = f"""\
Role-play as the following persona for a simulated user-research interview.

PERSONA (verbatim definition):
---
{persona_md}
---

HYPOTHESIS UNDER TEST:
> {hypothesis_statement}

Answer each question in this persona's voice. Respect the "How she answers questions" + "Biases" sections strictly.

Questions:
{questions_block}

Output strictly:
- A `## Q & A` section with **Q1:** / **A1:** pairs (one per question).
- A `## Confession` section: what this persona just said that a real human probably wouldn't, and why.
- A `## Confidence` line: a single integer 1-5 — your confidence the simulated answer matches what a real person of this profile would say.
"""
    return GUARDRAILS, [{"role": "user", "content": user}]
