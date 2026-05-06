import { describe, it, expect } from "vitest";
import { mockSseResponse } from "./sse";

describe("mockSseResponse", () => {
  it("returns a Response whose body streams the encoded SSE events", async () => {
    const response = mockSseResponse([
      { event: "token", data: { text: "hi" } },
      { event: "done", data: { ok: true, content: "hi" } },
    ]);

    expect(response.headers.get("content-type")).toBe("text/event-stream");

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let body = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      body += decoder.decode(value);
    }

    expect(body).toContain("event: token");
    expect(body).toContain('"text":"hi"');
    expect(body).toContain("event: done");
  });
});
