import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import * as api from "@/lib/api";
import { renderWithQuery } from "@/lib/test/query";
import PresetsList from "./PresetsList";

describe("PresetsList", () => {
  it("renders cards for each preset", async () => {
    vi.spyOn(api, "listPresets").mockResolvedValue([
      { name: "smb-saas", persona_count: 3 },
    ]);

    renderWithQuery(<MemoryRouter><PresetsList /></MemoryRouter>);

    await waitFor(() => expect(screen.getByText("smb-saas")).toBeInTheDocument());
    expect(screen.getByText(/3 personas/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /\+ new panel preset/i })).toHaveAttribute("href", "/panel-presets/new");
  });

  it("shows role=alert on error", async () => {
    vi.spyOn(api, "listPresets").mockRejectedValue(new Error("nope"));

    renderWithQuery(<MemoryRouter><PresetsList /></MemoryRouter>);

    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert).toBeInTheDocument();
    });
  });

  it("shows empty-state when no presets", async () => {
    vi.spyOn(api, "listPresets").mockResolvedValue([]);

    renderWithQuery(<MemoryRouter><PresetsList /></MemoryRouter>);

    await waitFor(() => expect(screen.getByText(/no panel presets yet/i)).toBeInTheDocument());
  });
});
