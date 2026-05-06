export type SseEvent = {
  event: "token" | "done" | "error";
  data: unknown;
};

export function mockSseResponse(events: SseEvent[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      for (const e of events) {
        const record = `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`;
        controller.enqueue(encoder.encode(record));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    headers: { "content-type": "text/event-stream" },
  });
}
