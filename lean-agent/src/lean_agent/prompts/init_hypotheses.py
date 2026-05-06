from typing import Any

from lean_agent.prompts.system import GUARDRAILS


def build(*, idea: str, n: int = 10) -> tuple[str, list[dict[str, Any]]]:
    user = f"""\
The user has a fresh idea:

> {idea}

Pre-filter using your training-data prior. Produce:

1. **Idea triage** — 3 to 5 adjacent angles to consider (single-line bullets).
2. **Hypothesis backlog** — exactly {n} hypotheses ranked by `Score = (Impact × Risk) / Effort`. For each, give:
   - id (H1 .. H{n})
   - statement (one sentence, "We believe ... will achieve ...")
   - impact 1-5
   - risk 1-5
   - effort 1-5
   - score (computed)
   - expected_pain (one short phrase — the hidden pain you predict drives this)
   - expected_objection (one sentence — the strongest reason this fails)

Output JSON with this exact shape:
{{
  "idea_angles": ["..."],
  "hypotheses": [
    {{"id":"H1","statement":"...","impact":5,"risk":4,"effort":2,"score":10.0,"expected_pain":"...","expected_objection":"..."}}
  ]
}}
"""
    return GUARDRAILS, [{"role": "user", "content": user}]
