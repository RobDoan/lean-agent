import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MarkdownView } from "@/components/MarkdownView";

describe("MarkdownView — C1 heading-demote", () => {
  it("renders # as <h2>", () => {
    render(<MarkdownView markdown={"# Top heading"} />);
    expect(screen.getByRole("heading", { level: 2, name: "Top heading" })).toBeInTheDocument();
  });

  it("renders ## as <h3>", () => {
    render(<MarkdownView markdown={"## Sub heading"} />);
    expect(screen.getByRole("heading", { level: 3, name: "Sub heading" })).toBeInTheDocument();
  });

  it("renders ### as <h4>", () => {
    render(<MarkdownView markdown={"### Third heading"} />);
    expect(screen.getByRole("heading", { level: 4, name: "Third heading" })).toBeInTheDocument();
  });

  it("does NOT demote #### (h4 stays as <h4>)", () => {
    render(<MarkdownView markdown={"#### Fourth heading"} />);
    expect(screen.getByRole("heading", { level: 4, name: "Fourth heading" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { level: 5 })).toBeNull();
  });
});
