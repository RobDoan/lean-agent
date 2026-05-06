import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { InterviewItem } from "@/components/InterviewItem";
import type { InterviewMeta } from "@/lib/types";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const meta: InterviewMeta = { name: "buyer-1", filename: "buyer-1.md" };

describe("InterviewItem — B1 error a11y", () => {
  it("interview-load error is announced via role=alert + aria-live=polite", async () => {
    fetchMock.mockRejectedValueOnce(new Error("read fail"));
    render(<InterviewItem slug="stable-coin-app" hid="H1" meta={meta} />);
    fireEvent.click(screen.getByRole("button"));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveAttribute("aria-live", "polite");
  });
});
