import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeleteConfirmModal } from "./DeleteConfirmModal";

describe("DeleteConfirmModal", () => {
  it("renders nothing when open=false", () => {
    const { container } = render(
      <DeleteConfirmModal open={false} targetName="alice" onConfirm={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("calls onConfirm when Confirm clicked", async () => {
    const onConfirm = vi.fn();
    render(
      <DeleteConfirmModal open={true} targetName="alice" onConfirm={onConfirm} onCancel={vi.fn()} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    expect(onConfirm).toHaveBeenCalled();
  });

  it("calls onCancel when Cancel clicked", async () => {
    const onCancel = vi.fn();
    render(
      <DeleteConfirmModal open={true} targetName="alice" onConfirm={vi.fn()} onCancel={onCancel} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalled();
  });

  it("renders cascade list and disables Confirm when cascadeBlocked is provided", () => {
    render(
      <DeleteConfirmModal
        open={true}
        targetName="alice"
        cascadeBlockedBy={["smb-saas", "creator"]}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText("smb-saas")).toBeInTheDocument();
    expect(screen.getByText("creator")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /confirm delete/i })).toBeDisabled();
  });
});
