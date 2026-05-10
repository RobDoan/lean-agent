import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import * as api from "@/lib/api";
import { PresetPersonaChecklist } from "./PresetPersonaChecklist";

function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

const CONTENT = "> My panel\n\n- alice\n- bob\n";

describe("PresetPersonaChecklist", () => {
  it("renders description and persona ids with checkboxes", () => {
    vi.spyOn(api, "listPersonas").mockResolvedValue([
      { id: "alice", name: "Alice", role: null },
      { id: "bob", name: "Bob", role: null },
    ]);

    renderWithQuery(
      <PresetPersonaChecklist
        content={CONTENT}
        onContentChange={vi.fn()}
        onPersonaClick={vi.fn()}
      />,
    );

    expect(screen.getByText("My panel")).toBeInTheDocument();
    expect(screen.getByText("alice")).toBeInTheDocument();
    expect(screen.getByText("bob")).toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")).toHaveLength(2);
    expect(screen.getByRole("checkbox", { name: "Include alice" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Include bob" })).toBeChecked();
  });

  it("unchecking a persona triggers onContentChange without that persona", async () => {
    vi.spyOn(api, "listPersonas").mockResolvedValue([]);
    const onChange = vi.fn();

    renderWithQuery(
      <PresetPersonaChecklist
        content={CONTENT}
        onContentChange={onChange}
        onPersonaClick={vi.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("checkbox", { name: "Include bob" }));
    expect(onChange).toHaveBeenCalledWith("> My panel\n\n- alice\n");
  });

  it("clicking persona name calls onPersonaClick", async () => {
    vi.spyOn(api, "listPersonas").mockResolvedValue([]);
    const onClick = vi.fn();

    renderWithQuery(
      <PresetPersonaChecklist
        content={CONTENT}
        onContentChange={vi.fn()}
        onPersonaClick={onClick}
      />,
    );

    await userEvent.click(screen.getByText("alice"));
    expect(onClick).toHaveBeenCalledWith("alice");
  });

  it("shows Add Persona button", () => {
    vi.spyOn(api, "listPersonas").mockResolvedValue([]);

    renderWithQuery(
      <PresetPersonaChecklist
        content={CONTENT}
        onContentChange={vi.fn()}
        onPersonaClick={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /add persona/i })).toBeInTheDocument();
  });
});
