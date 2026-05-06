import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import * as api from "@/lib/api";
import { renderWithQuery } from "@/lib/test/query";
import PersonasList from "./PersonasList";

describe("PersonasList", () => {
  it("renders cards for each persona", async () => {
    vi.spyOn(api, "listPersonas").mockResolvedValue([
      { id: "alice", name: "Alice", role: "Tester" },
      { id: "bob", name: "Bob", role: null },
    ]);

    renderWithQuery(<MemoryRouter><PersonasList /></MemoryRouter>);

    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /\+ new persona/i })).toHaveAttribute("href", "/personas/new");
  });

  it("shows role=alert on error", async () => {
    vi.spyOn(api, "listPersonas").mockRejectedValue(new Error("nope"));

    renderWithQuery(<MemoryRouter><PersonasList /></MemoryRouter>);

    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
    });
  });

  it("shows empty-state when no personas", async () => {
    vi.spyOn(api, "listPersonas").mockResolvedValue([]);

    renderWithQuery(<MemoryRouter><PersonasList /></MemoryRouter>);

    await waitFor(() => expect(screen.getByText(/no personas yet/i)).toBeInTheDocument());
  });
});
