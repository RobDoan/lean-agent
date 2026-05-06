import { describe, it, expect } from "vitest";
import { useQuery } from "@tanstack/react-query";
import { screen, waitFor } from "@testing-library/react";

import { renderWithQuery } from "./query";

function TestComp() {
  const { isPending, data } = useQuery({
    queryKey: ["test"],
    queryFn: async () => "hello",
  });
  if (isPending) return <p>loading</p>;
  return <p>{data}</p>;
}

describe("renderWithQuery", () => {
  it("provides QueryClientProvider so useQuery works", async () => {
    renderWithQuery(<TestComp />);
    await waitFor(() => expect(screen.getByText("hello")).toBeInTheDocument());
  });
});
