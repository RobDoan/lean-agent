"""System prompt + user-message envelope for prompt-driven persona edits.

The LLM is asked to return the FULL new persona file (markdown) given the
current file + a free-text instruction. Output is post-processed once
(strip outer code fence) and validated by `personas.loader.load_persona_from_str`.
"""
from __future__ import annotations

SYSTEM_PROMPT = """\
You are editing a persona file for the lean-agent tool. A persona file is a
markdown document with strict structure:

  - YAML-style frontmatter delimited by `---`, containing at least: name.
    Other recommended fields: age, role, income, location.
  - Exactly four sections, each beginning with `##` and these EXACT headings:
      ## Backstory
      ## Beliefs
      ## Biases
      ## How she answers questions

Your job: take the user's current file and their change instruction, and
return the new file in full.

Rules:
  - Output ONLY the file content. No explanation, no preamble, no code fences.
  - Do NOT include an `id` field in the frontmatter. The persona's identity comes from the filename.
  - Keep all four section headings, even if a section is short.
  - Match the existing tone and style unless the instruction says otherwise.
  - Beliefs and Biases use bullet points (`-`); Backstory and "How she answers
    questions" use prose or bullets as in the source.
"""


def build_user_message(*, current_content: str, instruction: str) -> str:
    """Wrap (current file, instruction) into the single-shot user-message envelope."""
    return (
        "<current_file>\n"
        f"{current_content}\n"
        "</current_file>\n"
        "\n"
        "<instruction>\n"
        f"{instruction}\n"
        "</instruction>\n"
    )
