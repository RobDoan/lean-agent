import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { ReactElement } from "react";

import { HypothesisListItem } from "@/components/HypothesisListItem";
import type { HypothesisListItem as Item } from "@/lib/types";

const baseItem: Item = {
  id: "H1",
  title: "We believe gig workers will achieve same-day liquidity",
  has_run: true,
  has_synthesis: true,
  interview_count: 5,
};

function renderWithRouter(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("HypothesisListItem", () => {
  it("renders id + title", () => {
    renderWithRouter(<HypothesisListItem slug="p1" item={baseItem} />);
    expect(screen.getByText(/H1/)).toBeInTheDocument();
    expect(screen.getByText(/gig workers/)).toBeInTheDocument();
  });

  it("links to nested URL", () => {
    renderWithRouter(<HypothesisListItem slug="p1" item={baseItem} />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/p/p1/h/H1");
  });

  it("shows 'not run' badge when has_run is false", () => {
    renderWithRouter(<HypothesisListItem slug="p1" item={{ ...baseItem, has_run: false, has_synthesis: false }} />);
    expect(screen.getByText(/not run/i)).toBeInTheDocument();
  });

  it("does not show 'not run' badge when has_run is true", () => {
    renderWithRouter(<HypothesisListItem slug="p1" item={baseItem} />);
    expect(screen.queryByText(/not run/i)).not.toBeInTheDocument();
  });
});
