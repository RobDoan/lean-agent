import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";

import { useDraftStream } from "./useDraftStream";
import { mockSseResponse } from "./test/sse";

describe("useDraftStream", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("starts in idle state", () => {
    const { result } = renderHook(() => useDraftStream("persona", "alice"));
    expect(result.current.state).toBe("idle");
    expect(result.current.proposedText).toBe("");
  });

  it("transitions IDLE → STREAMING → DONE_OK as tokens arrive then done.ok=true", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "token", data: { text: "Hello" } },
        { event: "token", data: { text: " world" } },
        { event: "done", data: { ok: true, content: "Hello world" } },
      ]),
    );

    const { result } = renderHook(() => useDraftStream("persona", "alice"));

    act(() => {
      result.current.send("be friendly");
    });

    await waitFor(() => expect(result.current.state).toBe("done_ok"));
    expect(result.current.proposedText).toBe("Hello world");
    expect(result.current.errors).toEqual([]);
  });

  it("transitions to DONE_ERR when done.ok=false with errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "token", data: { text: "garbage" } },
        { event: "done", data: { ok: false, content: "garbage", errors: ["frontmatter missing"] } },
      ]),
    );

    const { result } = renderHook(() => useDraftStream("persona", "alice"));
    act(() => result.current.send("x"));

    await waitFor(() => expect(result.current.state).toBe("done_err"));
    expect(result.current.errors).toEqual(["frontmatter missing"]);
  });

  it("transitions to ERROR when SSE error event arrives", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "error", data: { message: "rate limit" } }]),
    );

    const { result } = renderHook(() => useDraftStream("persona", "alice"));
    act(() => result.current.send("x"));

    await waitFor(() => expect(result.current.state).toBe("error"));
    expect(result.current.errors).toEqual(["rate limit"]);
  });

  it("reset() clears proposedText + errors and returns to IDLE", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "x" } }]),
    );

    const { result } = renderHook(() => useDraftStream("persona", "alice"));
    act(() => result.current.send("x"));
    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    act(() => result.current.reset());
    expect(result.current.state).toBe("idle");
    expect(result.current.proposedText).toBe("");
  });

  it("posts to /api/personas/draft with target_id+instruction", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "x" } }]),
    );

    const { result } = renderHook(() => useDraftStream("persona", "alice"));
    act(() => result.current.send("be terse"));

    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/personas/draft",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ target_id: "alice", instruction: "be terse" }),
      }),
    );
  });

  it("uses preset draft URL when target=preset", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "x" } }]),
    );

    const { result } = renderHook(() => useDraftStream("preset", "smb-saas"));
    act(() => result.current.send("x"));

    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/panel-presets/draft",
      expect.objectContaining({
        body: JSON.stringify({ target_name: "smb-saas", instruction: "x" }),
      }),
    );
  });

  it("targetId=null sends create-mode body", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "x" } }]),
    );

    const { result } = renderHook(() => useDraftStream("persona", null));
    act(() => result.current.send("create"));

    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/personas/draft",
      expect.objectContaining({
        body: JSON.stringify({ target_id: null, instruction: "create" }),
      }),
    );
  });
});


describe("useDraftStream iterative refinement (v0.3.1)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("send with currentContent includes current_content in body", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "refined" } }]),
    );

    const { result } = renderHook(() => useDraftStream("persona", "alice"));
    act(() => result.current.send("refine", "prior draft content"));

    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/personas/draft",
      expect.objectContaining({
        body: JSON.stringify({
          target_id: "alice",
          instruction: "refine",
          current_content: "prior draft content",
        }),
      }),
    );
  });

  it("send without currentContent does NOT include current_content in body", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "x" } }]),
    );

    const { result } = renderHook(() => useDraftStream("persona", "alice"));
    act(() => result.current.send("initial prompt"));

    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/personas/draft",
      expect.objectContaining({
        body: JSON.stringify({ target_id: "alice", instruction: "initial prompt" }),
      }),
    );
  });

  it("preset send with currentContent includes current_content", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "x" } }]),
    );

    const { result } = renderHook(() => useDraftStream("preset", "smb-saas"));
    act(() => result.current.send("add bob", "- alice\n"));

    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/panel-presets/draft",
      expect.objectContaining({
        body: JSON.stringify({
          target_name: "smb-saas",
          instruction: "add bob",
          current_content: "- alice\n",
        }),
      }),
    );
  });
});


describe("useDraftStream auto-gen flow (v0.3.2)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("sendAutoGen posts to /api/panel-presets/auto-gen with instruction", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "phase", data: { phase: "analyzing" } },
        { event: "plan_ready", data: { plan: { description: "test", reuse: [], create: [] } } },
      ]),
    );

    const { result } = renderHook(() => useDraftStream("preset", null));
    act(() => result.current.sendAutoGen("low-income gig workers"));

    await waitFor(() => expect(result.current.state).toBe("plan_ready"));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/panel-presets/auto-gen",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ instruction: "low-income gig workers" }),
      }),
    );
  });

  it("phase:analyzing transitions state to analyzing", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "phase", data: { phase: "analyzing" } },
        { event: "plan_ready", data: { plan: { description: "d", reuse: [], create: [] } } },
      ]),
    );

    const { result } = renderHook(() => useDraftStream("preset", null));
    act(() => result.current.sendAutoGen("x"));

    await waitFor(() => expect(result.current.state).toBe("plan_ready"));
    expect(result.current.plan).toEqual({ description: "d", reuse: [], create: [] });
  });

  it("plan_ready stores plan and transitions to plan_ready", async () => {
    const plan = {
      description: "Panel for gig workers",
      reuse: ["sarah-freelance-designer"],
      create: [{ slug: "maria-gig", name: "Maria", description: "gig worker" }],
    };

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "phase", data: { phase: "analyzing" } },
        { event: "plan_ready", data: { plan } },
      ]),
    );

    const { result } = renderHook(() => useDraftStream("preset", null));
    act(() => result.current.sendAutoGen("gig workers"));

    await waitFor(() => expect(result.current.state).toBe("plan_ready"));
    expect(result.current.plan).toEqual(plan);
  });

  it("confirmPlan posts to /api/panel-presets/auto-gen/confirm with plan", async () => {
    const plan = { description: "d", reuse: ["alice"], create: [{ slug: "bob", name: "Bob", description: "x" }] };

    // First call: auto-gen returns plan_ready
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        mockSseResponse([
          { event: "phase", data: { phase: "analyzing" } },
          { event: "plan_ready", data: { plan } },
        ]),
      )
      // Second call: confirm returns done
      .mockResolvedValueOnce(
        mockSseResponse([
          { event: "phase", data: { phase: "generating_persona" } },
          { event: "persona_created", data: { slug: "bob", name: "Bob" } },
          { event: "phase", data: { phase: "composing" } },
          { event: "done", data: { ok: true, content: "> d\n\n- alice\n- bob\n" } },
        ]),
      );

    const { result } = renderHook(() => useDraftStream("preset", null));
    act(() => result.current.sendAutoGen("x"));
    await waitFor(() => expect(result.current.state).toBe("plan_ready"));

    act(() => result.current.confirmPlan());
    await waitFor(() => expect(result.current.state).toBe("done_ok"));

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/panel-presets/auto-gen/confirm",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ plan }),
      }),
    );
    expect(result.current.proposedText).toBe("> d\n\n- alice\n- bob\n");
    expect(result.current.createdPersonas).toEqual([{ slug: "bob", name: "Bob" }]);
  });

  it("reset clears plan and createdPersonas", async () => {
    const plan = { description: "d", reuse: [], create: [] };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "plan_ready", data: { plan } },
      ]),
    );

    const { result } = renderHook(() => useDraftStream("preset", null));
    act(() => result.current.sendAutoGen("x"));
    await waitFor(() => expect(result.current.state).toBe("plan_ready"));

    act(() => result.current.reset());
    expect(result.current.state).toBe("idle");
    expect(result.current.plan).toBeNull();
    expect(result.current.createdPersonas).toEqual([]);
  });
});
