import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { renderWithQuery } from "@/lib/test/query";
import * as api from "@/lib/api";
import Dashboard from "@/pages/Dashboard";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

describe("Dashboard", () => {
  it("shows skeleton during fetch", () => {
    fetchMock.mockReturnValue(new Promise(() => {})); // never resolves
    const { container } = renderWithQuery(<MemoryRouter><Dashboard /></MemoryRouter>);
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders cards for each project", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse([
        { slug: "p1", idea: "first", hypothesis_count: 1, run_count: 0, with_synthesis_count: 0, created_at: "x" },
        { slug: "p2", idea: "second", hypothesis_count: 2, run_count: 1, with_synthesis_count: 1, created_at: "x" },
      ]),
    );
    renderWithQuery(<MemoryRouter><Dashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText("first")).toBeInTheDocument();
      expect(screen.getByText("second")).toBeInTheDocument();
    });
  });

  it("renders empty state when no projects", async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));
    renderWithQuery(<MemoryRouter><Dashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no projects/i)).toBeInTheDocument();
    });
  });

  it("renders error message on failure", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "boom" }, 500));
    renderWithQuery(<MemoryRouter><Dashboard /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/could not load/i)).toBeInTheDocument();
    });
  });
});

describe("Dashboard — B1 error a11y", () => {
  beforeEach(() => {
    vi.spyOn(api, "listProjects").mockRejectedValue(new Error("network down"));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("error message is announced via role=alert with aria-live=polite", async () => {
    renderWithQuery(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveAttribute("aria-live", "polite");
    expect(alert.textContent).toMatch(/Could not load/);
  });
});

describe("Dashboard — A1 equal-height grid", () => {
  beforeEach(() => {
    vi.spyOn(api, "listProjects").mockResolvedValue([
      {
        slug: "p1",
        idea: "short idea",
        hypothesis_count: 0,
        run_count: 0,
        with_synthesis_count: 0,
        created_at: "2026-05-05T00:00:00+00:00",
      },
    ]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uses auto-rows-fr on the project grid container so cards equalize height", async () => {
    renderWithQuery(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    const link = await screen.findByRole("link");
    const grid = link.closest("div");
    expect(grid?.className).toMatch(/\bauto-rows-fr\b/);
  });
});
