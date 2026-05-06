import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TopNav } from "./TopNav";

describe("TopNav", () => {
  it("renders three links: Dashboard, Personas, Panel Presets", () => {
    render(<MemoryRouter><TopNav /></MemoryRouter>);
    expect(screen.getByRole("link", { name: /dashboard/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: /personas/i })).toHaveAttribute("href", "/personas");
    expect(screen.getByRole("link", { name: /panel presets/i })).toHaveAttribute("href", "/panel-presets");
  });

  it("brand 'lean-agent' is a link to /", () => {
    render(<MemoryRouter><TopNav /></MemoryRouter>);
    const brandLink = screen.getByRole("link", { name: /lean-agent/i });
    expect(brandLink).toHaveAttribute("href", "/");
  });
});
