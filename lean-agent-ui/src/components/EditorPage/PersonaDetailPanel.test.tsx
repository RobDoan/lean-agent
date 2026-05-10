import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import * as api from "@/lib/api";
import { renderWithQuery } from "@/lib/test/query";
import { PersonaDetailPanel } from "./PersonaDetailPanel";

describe("PersonaDetailPanel", () => {
  it("fetches and displays persona details", async () => {
    vi.spyOn(api, "getPersona").mockResolvedValue({
      id: "alice",
      name: "Alice",
      metadata: { role: "PM", income: "120k" },
      backstory: "Alice is a PM.",
      beliefs: "Believes in user research.",
      biases: "Anchoring bias.",
      how_she_answers: "Thoughtfully.",
      raw_content: "---\nid: alice\n---",
    });

    renderWithQuery(
      <PersonaDetailPanel personaId="alice" onClose={vi.fn()} />,
    );

    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    expect(screen.getByText("PM")).toBeInTheDocument();
    expect(screen.getByText("120k")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", async () => {
    vi.spyOn(api, "getPersona").mockResolvedValue({
      id: "alice",
      name: "Alice",
      metadata: {},
      backstory: "x",
      beliefs: "x",
      biases: "x",
      how_she_answers: "x",
      raw_content: "---\nid: alice\n---",
    });

    const onClose = vi.fn();
    renderWithQuery(
      <PersonaDetailPanel personaId="alice" onClose={onClose} />,
    );

    const closeBtn = screen.getByRole("button", { name: /close panel/i });
    closeBtn.click();
    expect(onClose).toHaveBeenCalledOnce();
  });
});
