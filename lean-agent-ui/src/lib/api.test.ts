import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { listProjects, getProject, getHypothesis, getInterview, ApiClientError } from "@/lib/api";

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

describe("api client", () => {
  it("listProjects calls /api/projects and returns array", async () => {
    fetchMock.mockResolvedValue(jsonResponse([{ slug: "p1", idea: null, hypothesis_count: 0, run_count: 0, with_synthesis_count: 0, created_at: "x" }]));
    const result = await listProjects();
    expect(fetchMock).toHaveBeenCalledWith("/api/projects");
    expect(result).toHaveLength(1);
    expect(result[0].slug).toBe("p1");
  });

  it("getProject calls /api/projects/{slug}", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ slug: "p1", idea: "x", hypotheses: [] }));
    const result = await getProject("p1");
    expect(fetchMock).toHaveBeenCalledWith("/api/projects/p1");
    expect(result.slug).toBe("p1");
  });

  it("getHypothesis calls nested path", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "H1", title: "t", synthesis_markdown: null, sprint_markdown: null, interviews: [] }));
    const result = await getHypothesis("p1", "H1");
    expect(fetchMock).toHaveBeenCalledWith("/api/projects/p1/hypotheses/H1");
    expect(result.id).toBe("H1");
  });

  it("getInterview calls deepest path", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ name: "alex", markdown: "# I" }));
    const result = await getInterview("p1", "H1", "alex");
    expect(fetchMock).toHaveBeenCalledWith("/api/projects/p1/hypotheses/H1/interviews/alex");
    expect(result.name).toBe("alex");
  });

  it("throws ApiClientError on non-2xx", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "missing" }, 404));
    await expect(getProject("nope")).rejects.toBeInstanceOf(ApiClientError);
  });

  it("ApiClientError carries status + detail", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "missing" }, 404));
    try {
      await getProject("nope");
    } catch (e) {
      expect(e).toBeInstanceOf(ApiClientError);
      expect((e as ApiClientError).status).toBe(404);
      expect((e as ApiClientError).detail).toBe("missing");
    }
  });
});
