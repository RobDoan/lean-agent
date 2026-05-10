import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PlanReview } from "./PlanReview";
import type { PresetPlan } from "@/lib/types";

const PLAN: PresetPlan = {
  description: "Panel for low-income gig workers",
  reuse: ["sarah-freelance-designer"],
  create: [
    { slug: "maria-gig-delivery", name: "Maria", description: "Gig delivery worker in LA" },
    { slug: "carlos-rideshare", name: "Carlos", description: "Rideshare driver in Houston" },
  ],
};

describe("PlanReview", () => {
  it("renders reuse and create lists", () => {
    render(<PlanReview plan={PLAN} onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByText("Panel Plan")).toBeInTheDocument();
    expect(screen.getByText("Panel for low-income gig workers")).toBeInTheDocument();
    expect(screen.getByText("Reusing 1 existing persona")).toBeInTheDocument();
    expect(screen.getByText("sarah-freelance-designer")).toBeInTheDocument();
    expect(screen.getByText("Creating 2 new personas")).toBeInTheDocument();
    expect(screen.getByText("maria-gig-delivery")).toBeInTheDocument();
    expect(screen.getByText("carlos-rideshare")).toBeInTheDocument();
  });

  it("calls onConfirm when Confirm button is clicked", async () => {
    const onConfirm = vi.fn();
    render(<PlanReview plan={PLAN} onConfirm={onConfirm} onCancel={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /confirm/i }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("calls onCancel when Cancel button is clicked", async () => {
    const onCancel = vi.fn();
    render(<PlanReview plan={PLAN} onConfirm={vi.fn()} onCancel={onCancel} />);
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
