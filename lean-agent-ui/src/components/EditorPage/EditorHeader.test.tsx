import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EditorHeader } from "./EditorHeader";

describe("EditorHeader edit mode", () => {
  it("shows name + id and a Delete button", () => {
    render(
      <EditorHeader
        mode="edit"
        title="Alice"
        subtitle="alice"
        onDelete={vi.fn()}
        onIdChange={vi.fn()}
        idValue=""
        idValid={true}
      />,
    );
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("alice")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /delete/i })).toBeInTheDocument();
  });

  it("calls onDelete when Delete clicked", async () => {
    const onDelete = vi.fn();
    render(
      <EditorHeader
        mode="edit" title="Alice" subtitle="alice"
        onDelete={onDelete} onIdChange={vi.fn()} idValue="" idValid={true}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /delete/i }));
    expect(onDelete).toHaveBeenCalled();
  });
});

describe("EditorHeader create mode", () => {
  it("shows id input + validates against slug regex", async () => {
    const onIdChange = vi.fn();
    render(
      <EditorHeader
        mode="create" title="" subtitle="New persona"
        onDelete={vi.fn()} onIdChange={onIdChange} idValue="" idValid={false}
      />,
    );

    const input = screen.getByPlaceholderText(/id/i);
    await userEvent.type(input, "alice-pm");
    expect(onIdChange).toHaveBeenCalled();
  });

  it("shows validation message when idValid=false and idValue is non-empty", () => {
    render(
      <EditorHeader
        mode="create" title="" subtitle=""
        onDelete={vi.fn()} onIdChange={vi.fn()} idValue="Bad ID" idValid={false}
      />,
    );
    expect(screen.getByText(/lowercase letters, digits, and hyphens/i)).toBeInTheDocument();
  });
});
