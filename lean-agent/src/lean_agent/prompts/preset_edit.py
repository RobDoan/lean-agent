"""System prompt + user-message envelope for prompt-driven panel-preset edits.

The system prompt is templated per request: the available persona-id set is
injected so the LLM can pick by content (e.g. 'a panel for SaaS founders').
"""
from __future__ import annotations


_SYSTEM_PROMPT_TEMPLATE = """\
You are editing a panel-preset file for the lean-agent tool. A panel-preset is
a markdown file that optionally starts with a description blockquote, followed
by a bullet list of persona ids that compose a named panel.

Format:
  > A one-line description of this panel's purpose and audience.

  - persona-id-1
  - persona-id-2

Available persona ids (the ONLY ones you may use):
{ids_block}

Your job: take the user's current preset and their change instruction, and
return the new preset in full.

Rules:
  - Output ONLY the file content. No explanation, no preamble, no code fences,
    no headings.
  - Optionally include a one-line description as a blockquote (`> ...`) before
    the bullet list. If the current file has a description, preserve or update
    it. If creating a new preset, include a description.
  - Each bullet line is `- <persona-id>` where `<persona-id>` is one of the
    available ids exactly as shown.
  - No duplicates. No personas not in the available list.
  - 1 to 12 personas per preset.
"""


def build_system_prompt(available_ids: list[str]) -> str:
    """Build the system prompt with available persona ids injected (sorted, one per line)."""
    ids_block = "\n".join(sorted(available_ids))
    return _SYSTEM_PROMPT_TEMPLATE.format(ids_block=ids_block)


def build_user_message(*, current_content: str, instruction: str) -> str:
    """Wrap (current preset, instruction) into the single-shot user-message envelope."""
    return (
        "<current_file>\n"
        f"{current_content}\n"
        "</current_file>\n"
        "\n"
        "<instruction>\n"
        f"{instruction}\n"
        "</instruction>\n"
    )
