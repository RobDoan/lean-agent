import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import Dashboard from "@/pages/Dashboard";
import NotFound from "@/pages/NotFound";

describe("NotFound", () => {
  it("renders heading and back-to-dashboard link when navigated to an unmatched URL", () => {
    render(
      <RouterProvider
        router={createMemoryRouter(
          [
            { path: "/", element: <Dashboard /> },
            { path: "*", element: <NotFound /> },
          ],
          { initialEntries: ["/totally-bogus-url"] },
        )}
      />,
    );
    expect(screen.getByRole("heading", { name: /not found/i })).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /back to dashboard/i });
    expect(link).toHaveAttribute("href", "/");
  });
});
