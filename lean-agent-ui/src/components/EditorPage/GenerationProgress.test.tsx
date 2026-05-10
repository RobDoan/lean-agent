import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { GenerationProgress } from "./GenerationProgress";

describe("GenerationProgress", () => {
  it("renders created personas with checkmarks", () => {
    render(
      <GenerationProgress
        createdPersonas={[
          { slug: "maria-gig-delivery", name: "Maria" },
          { slug: "carlos-rideshare", name: "Carlos" },
        ]}
        phase="generating"
      />,
    );
    expect(screen.getByText("maria-gig-delivery")).toBeInTheDocument();
    expect(screen.getByText("(Maria)")).toBeInTheDocument();
    expect(screen.getByText("carlos-rideshare")).toBeInTheDocument();
    expect(screen.getByText("(Carlos)")).toBeInTheDocument();
  });

  it("shows generating message during generating phase", () => {
    render(<GenerationProgress createdPersonas={[]} phase="generating" />);
    expect(screen.getByText("Generating personas...")).toBeInTheDocument();
    expect(screen.getByText("Generating...")).toBeInTheDocument();
  });

  it("shows composing message during composing phase", () => {
    render(<GenerationProgress createdPersonas={[]} phase="composing" />);
    expect(screen.getByText("Composing preset...")).toBeInTheDocument();
    expect(screen.getByText("Assembling preset from all personas...")).toBeInTheDocument();
  });
});
