import { useReducer } from "react";

export type DraftStreamState =
  | "idle"
  | "streaming"
  | "done_ok"
  | "done_err"
  | "error";

type Action =
  | { type: "SEND_STARTED" }
  | { type: "TOKEN"; text: string }
  | { type: "DONE_OK"; content: string }
  | { type: "DONE_ERR"; content: string; errors: string[] }
  | { type: "ERROR"; message: string }
  | { type: "RESET" };

type State = {
  state: DraftStreamState;
  proposedText: string;
  errors: string[];
};

const INITIAL: State = { state: "idle", proposedText: "", errors: [] };

function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "SEND_STARTED":
      return { state: "streaming", proposedText: "", errors: [] };
    case "TOKEN":
      return { ...s, proposedText: s.proposedText + a.text };
    case "DONE_OK":
      return { state: "done_ok", proposedText: a.content, errors: [] };
    case "DONE_ERR":
      return { state: "done_err", proposedText: a.content, errors: a.errors };
    case "ERROR":
      return { ...s, state: "error", errors: [a.message] };
    case "RESET":
      return INITIAL;
  }
}

export function useDraftStream(
  target: "persona" | "preset",
  targetId: string | null,
) {
  const [state, dispatch] = useReducer(reducer, INITIAL);

  const send = (instruction: string): void => {
    // Fire-and-forget: keeps `act(() => send(...))` in tests synchronous so React's
    // act internals do not schedule stray setImmediate callbacks that bleed across tests.
    void (async () => {
      dispatch({ type: "SEND_STARTED" });
      const url = target === "persona" ? "/api/personas/draft" : "/api/panel-presets/draft";
      const body =
        target === "persona"
          ? JSON.stringify({ target_id: targetId, instruction })
          : JSON.stringify({ target_name: targetId, instruction });

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body,
        });
        if (!response.ok || !response.body) {
          dispatch({ type: "ERROR", message: `HTTP ${response.status}` });
          return;
        }
        await consumeSseStream(response.body, dispatch);
      } catch (e) {
        dispatch({ type: "ERROR", message: e instanceof Error ? e.message : String(e) });
      }
    })();
  };

  return {
    state: state.state,
    proposedText: state.proposedText,
    errors: state.errors,
    send,
    reset: () => dispatch({ type: "RESET" }),
  };
}

/** Consumes an SSE ReadableStream; returns after the first terminal event (done/error). */
async function consumeSseStream(
  body: ReadableStream<Uint8Array>,
  dispatch: (a: Action) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  outer: while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    // SSE records are separated by `\n\n`; iterate complete records, keep tail in buf.
    let idx;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const record = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      // Break outer loop once a terminal event is dispatched — avoids a trailing read.
      if (handleRecord(record, dispatch)) break outer;
    }
  }
  // Flush any trailing record (no trailing \n\n).
  if (buf.trim()) handleRecord(buf, dispatch);
}

/** Parses and dispatches one SSE record. Returns true if the event was terminal (done/error). */
function handleRecord(record: string, dispatch: (a: Action) => void): boolean {
  let event = "message";
  let data = "";
  for (const line of record.split("\n")) {
    if (line.startsWith("event:")) event = line.slice("event:".length).trim();
    else if (line.startsWith("data:")) data += line.slice("data:".length).trim();
  }
  if (!data) return false;
  let parsed: unknown;
  try {
    parsed = JSON.parse(data);
  } catch {
    return false;
  }
  if (
    event === "token" &&
    typeof parsed === "object" &&
    parsed !== null &&
    "text" in parsed &&
    typeof (parsed as { text: unknown }).text === "string"
  ) {
    dispatch({ type: "TOKEN", text: (parsed as { text: string }).text });
    return false;
  } else if (event === "done" && typeof parsed === "object" && parsed !== null) {
    const p = parsed as { ok?: unknown; content?: unknown; errors?: unknown };
    if (p.ok) {
      dispatch({ type: "DONE_OK", content: String(p.content ?? "") });
    } else {
      dispatch({
        type: "DONE_ERR",
        content: String(p.content ?? ""),
        errors: Array.isArray(p.errors) ? p.errors.map(String) : [],
      });
    }
    return true;
  } else if (
    event === "error" &&
    typeof parsed === "object" &&
    parsed !== null
  ) {
    const p = parsed as { message?: unknown };
    dispatch({ type: "ERROR", message: String(p.message ?? "stream error") });
    return true;
  }
  return false;
}
