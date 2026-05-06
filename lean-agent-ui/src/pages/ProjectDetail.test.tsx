import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { renderWithQuery } from "@/lib/test/query";
import ProjectDetail from "@/pages/ProjectDetail";

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

function renderAt(path: string) {
  return renderWithQuery(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/projects/:slug" element={<ProjectDetail />} />
        <Route path="/projects/:slug/:hid" element={<ProjectDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProjectDetail", () => {
  it("groups hypotheses into 'with synthesis' and 'no synthesis'", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        slug: "p1",
        idea: "x",
        idea_triage: [],
        hypotheses: [
          { id: "H1", title: "t1", has_run: true, has_synthesis: true, interview_count: 2 },
          { id: "H2", title: "t2", has_run: false, has_synthesis: false, interview_count: 0 },
        ],
      }),
    );
    renderAt("/projects/p1");
    await waitFor(() => {
      expect(screen.getByText(/with synthesis/i)).toBeInTheDocument();
      expect(screen.getByText(/no synthesis/i)).toBeInTheDocument();
      expect(screen.getByText("H1")).toBeInTheDocument();
      expect(screen.getByText("H2")).toBeInTheDocument();
    });
  });

  it("placeholder when no hypothesis selected and no triage", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ slug: "p1", idea: "x", idea_triage: [], hypotheses: [] }));
    renderAt("/projects/p1");
    await waitFor(() => {
      expect(screen.getByText(/select a hypothesis/i)).toBeInTheDocument();
    });
  });

  it("shows Idea Triage when no hypothesis selected", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        slug: "p1",
        idea: "x",
        idea_triage: ["What if we used AI for invoices?", "Could we build a community?"],
        hypotheses: [],
      }),
    );
    renderAt("/projects/p1");
    await waitFor(() => {
      expect(screen.getByText(/idea triage/i)).toBeInTheDocument();
      expect(screen.getByText("What if we used AI for invoices?")).toBeInTheDocument();
      expect(screen.getByText("Could we build a community?")).toBeInTheDocument();
    });
  });

  it("loads hypothesis content when :hid is in URL", async () => {
    fetchMock.mockImplementation((url: string) => {
      if (url === "/api/projects/p1") {
        return Promise.resolve(jsonResponse({
          slug: "p1",
          idea: "x",
          idea_triage: [],
          hypotheses: [{ id: "H1", title: "stmt", has_run: true, has_synthesis: true, interview_count: 0 }],
        }));
      }
      if (url === "/api/projects/p1/hypotheses/H1") {
        return Promise.resolve(jsonResponse({
          id: "H1",
          title: "stmt",
          synthesis_markdown: "# Synthesis body",
          sprint_markdown: null,
          interviews: [],
        }));
      }
      return Promise.reject(new Error("unexpected url " + url));
    });
    renderAt("/projects/p1/H1");
    await waitFor(() => {
      expect(screen.getByText(/synthesis body/i)).toBeInTheDocument();
    });
  });
});

describe("ProjectDetail — B1 error a11y", () => {
  it("project-load error is announced via role=alert + aria-live=polite", async () => {
    fetchMock.mockRejectedValueOnce(new Error("backend down"));
    renderAt("/projects/p1");
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveAttribute("aria-live", "polite");
  });

  it("hypothesis-load error is announced via role=alert + aria-live=polite", async () => {
    // First call: project fetch succeeds.
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        slug: "p1",
        idea: "x",
        idea_triage: [],
        hypotheses: [
          { id: "H1", title: "t1", has_run: true, has_synthesis: false, interview_count: 0 },
        ],
      }),
    );
    // Second call: hypothesis fetch fails.
    fetchMock.mockRejectedValueOnce(new Error("hyp gone"));
    renderAt("/projects/p1/H1");
    const alerts = await screen.findAllByRole("alert");
    expect(alerts.length).toBeGreaterThanOrEqual(1);
    alerts.forEach((a) => expect(a).toHaveAttribute("aria-live", "polite"));
  });
});
