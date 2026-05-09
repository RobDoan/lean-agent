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
