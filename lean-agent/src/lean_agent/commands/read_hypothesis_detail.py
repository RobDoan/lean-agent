from __future__ import annotations
from dataclasses import dataclass
from lean_agent import paths
from lean_agent.commands.errors import HypothesisNotFoundError
from lean_agent.commands.read_research_tree import read_research_tree, Hypothesis

@dataclass(frozen=True)
class HypothesisDetailInternal:
    hypothesis: Hypothesis
    synthesis_markdown: str | None
    sprint_markdown: str | None
    interviews: list[tuple[str, str]]

def read_hypothesis_detail(slug: str, hid: str) -> HypothesisDetailInternal:
    tree = read_research_tree(slug)
    matching = [h for h in tree.hypotheses if h.id == hid]
    if not matching:
        raise HypothesisNotFoundError(slug, hid)
    h = matching[0]

    synthesis_markdown: str | None = None
    sprint_markdown: str | None = None
    interviews: list[tuple[str, str]] = []

    hdir = paths.hypothesis_dir_glob(slug, hid)
    if hdir is not None:
        synth = hdir / "synthesis.md"
        if synth.exists():
            synthesis_markdown = synth.read_text()
        sprint = hdir / "01-problem-validation-sprint.md"
        if sprint.exists():
            sprint_markdown = sprint.read_text()
        idir = hdir / "interviews"
        if idir.exists():
            for f in sorted(idir.glob("*.md")):
                interviews.append((f.stem, f.name))

    return HypothesisDetailInternal(
        hypothesis=h,
        synthesis_markdown=synthesis_markdown,
        sprint_markdown=sprint_markdown,
        interviews=interviews,
    )
