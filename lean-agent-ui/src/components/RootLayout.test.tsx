import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { RootLayout } from "./RootLayout";

describe("RootLayout", () => {
  it("renders TopNav above the Outlet", () => {
    render(
      <MemoryRouter initialEntries={["/x"]}>
        <Routes>
          <Route element={<RootLayout />}>
            <Route path="/x" element={<p>child page</p>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    // Both nav and child render
    expect(screen.getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByText("child page")).toBeInTheDocument();
  });
});
