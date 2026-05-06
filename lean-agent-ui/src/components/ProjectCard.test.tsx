import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { ReactElement } from "react";

import { ProjectCard } from "@/components/ProjectCard";
import type { ProjectSummary } from "@/lib/types";

const project: ProjectSummary = {
  slug: "stable-coin-app",
  idea: "i want to build a stable coin app",
  hypothesis_count: 10,
  run_count: 2,
  with_synthesis_count: 1,
  created_at: "2026-05-04T00:00:00+00:00",
};

function renderWithRouter(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("ProjectCard", () => {
  it("renders idea text as title", () => {
    renderWithRouter(<ProjectCard project={project} />);
    expect(screen.getByText(/i want to build a stable coin app/)).toBeInTheDocument();
  });

  it("falls back to slug when idea is null", () => {
    renderWithRouter(<ProjectCard project={{ ...project, idea: null }} />);
    expect(screen.getByText("stable-coin-app")).toBeInTheDocument();
  });

  it("renders the count summary", () => {
    renderWithRouter(<ProjectCard project={project} />);
    expect(screen.getByText(/10/)).toBeInTheDocument();
    expect(screen.getByText(/2 run/)).toBeInTheDocument();
    expect(screen.getByText(/1 with synthesis/)).toBeInTheDocument();
  });

  it("treats empty-string idea symmetrically: title renders empty, description still renders slug", () => {
    renderWithRouter(<ProjectCard project={{ ...project, idea: "" }} />);
    // description should appear (null-check semantics, not truthy)
    expect(screen.getByText("stable-coin-app")).toBeInTheDocument();
    // title should be the rendered empty string (??-fallback only fires for null/undefined)
    // assert that the slug is NOT used as the title — i.e., it appears once (in description), not twice
    const slugMatches = screen.getAllByText("stable-coin-app");
    expect(slugMatches).toHaveLength(1);
  });
});
