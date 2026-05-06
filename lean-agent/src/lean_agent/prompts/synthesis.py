from typing import Any

from lean_agent.prompts.system import GUARDRAILS


def build(*, hypothesis_statement: str, transcripts: list[str]) -> tuple[str, list[dict[str, Any]]]:
    # Separator assumes transcripts are raw model output (no YAML frontmatter).
    # Task 13 wraps each transcript with a small markdown header; no `---` collisions.
    block = "\n\n---\n\n".join(transcripts)
    user = f"""\
Synthesize across the following simulated interviews.

HYPOTHESIS:
> {hypothesis_statement}

TRANSCRIPTS:
{block}

Output strictly JSON with this shape:
{{
  "steelman": "<the strongest objection — written as if from someone who tried this and failed>",
  "themes": ["<short bullet>", "..."],
  "kill_signal": {{
    "would_use": <int>, "would_avoid": <int>, "total": <int>, "kill_threshold_met": <true|false>
  }},
  "confident": ["<thing the LLM training-data prior is good for>", "..."],
  "unknown": ["<thing only a real human can answer>", "..."],
  "recommendation": "<one of: 🚀 Promote / ✏️ Revise & rerun / 💀 Kill>"
}}

Apply the KILL-BIAS rule: if would_use < 3 OR would_avoid >= total/2, set kill_threshold_met=true and recommend Kill.
"""
    return GUARDRAILS, [{"role": "user", "content": user}]
