import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DiffView } from "./DiffView";

describe("DiffView", () => {
  it("renders both left and right text", async () => {
    render(<DiffView left="hello" right="world" />);
    expect(await screen.findByText("hello")).toBeInTheDocument();
    expect(await screen.findByText("world")).toBeInTheDocument();
  });

  it("renders even when one side is empty (idle / streaming start)", async () => {
    render(<DiffView left="hello" right="" />);
    expect(await screen.findByText("hello")).toBeInTheDocument();
  });
});
