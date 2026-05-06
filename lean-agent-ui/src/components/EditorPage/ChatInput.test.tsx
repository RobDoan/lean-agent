import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInput } from "./ChatInput";

describe("ChatInput", () => {
  it("calls onSend with the textarea value when Send clicked", async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    await userEvent.type(screen.getByRole("textbox"), "make her terse");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(onSend).toHaveBeenCalledWith("make her terse");
  });

  it("disables Send button when disabled prop is true", () => {
    render(<ChatInput onSend={vi.fn()} disabled={true} />);
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("does not call onSend when textarea is empty", async () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).not.toHaveBeenCalled();
  });

  it("clears textarea after Send", async () => {
    render(<ChatInput onSend={vi.fn()} disabled={false} />);
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    await userEvent.type(textarea, "x");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(textarea.value).toBe("");
  });
});
