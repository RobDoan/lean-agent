import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";

import * as api from "@/lib/api";
import { renderWithQuery } from "@/lib/test/query";
import { PresetHistory } from "./PresetHistory";
import userEvent from "@testing-library/user-event";

describe("PresetHistory", () => {
  it("shows toggle button and fetches history when opened", async () => {
    vi.spyOn(api, "getPresetHistory").mockResolvedValue([
      { sha: "abc1234", message: "create preset", date: "2025-01-01T00:00:00Z" },
      { sha: "def5678", message: "update preset", date: "2025-01-02T00:00:00Z" },
    ]);

    renderWithQuery(<PresetHistory presetName="my-preset" />);

    expect(screen.getByText("Version History")).toBeInTheDocument();

    await userEvent.click(screen.getByText("Version History"));

    await waitFor(() => expect(screen.getByText("abc1234")).toBeInTheDocument());
    expect(screen.getByText("create preset")).toBeInTheDocument();
    expect(screen.getByText("def5678")).toBeInTheDocument();
  });

  it("shows empty state when no history", async () => {
    vi.spyOn(api, "getPresetHistory").mockResolvedValue([]);

    renderWithQuery(<PresetHistory presetName="my-preset" />);

    await userEvent.click(screen.getByText("Version History"));

    await waitFor(() =>
      expect(screen.getByText("No version history yet.")).toBeInTheDocument(),
    );
  });
});
