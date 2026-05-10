import { useEffect, useReducer, useRef } from "react";

import type { PresetPlan } from "@/lib/types";

export type DraftStreamState =
  | "idle"
  | "streaming"
  | "analyzing"
  | "plan_ready"
  | "generating"
  | "composing"
  | "done_ok"
  | "done_err"
  | "error";

type Action =
  | { type: "SEND_STARTED" }
  | { type: "TOKEN"; text: string }
  | { type: "DONE_OK"; content: string }
  | { type: "DONE_ERR"; content: string; errors: string[] }
  | { type: "ERROR"; message: string }
  | { type: "RESET" }
  | { type: "PHASE"; phase: string }
  | { type: "PLAN_READY"; plan: PresetPlan }
  | { type: "PERSONA_CREATED"; slug: string; name: string }
  | { type: "CONFIRM_STARTED" }
  | { type: "SET_PROPOSED_TEXT"; content: string };

type State = {
  state: DraftStreamState;
  proposedText: string;
  errors: string[];
  plan: PresetPlan | null;
  createdPersonas: { slug: string; name: string }[];
};

const INITIAL: State = {
  state: "idle",
  proposedText: "",
  errors: [],
  plan: null,
  createdPersonas: [],
};

function phaseToState(phase: string): DraftStreamState {
  switch (phase) {
    case "analyzing":
      return "analyzing";
    case "generating_persona":
      return "generating";
    case "composing":
      return "composing";
    default:
      return "streaming";
  }
}

function reducer(s: State, a: Action): State {
  switch (a.type) {
    case "SEND_STARTED":
      return { ...INITIAL, state: "streaming" };
    case "TOKEN":
      return { ...s, proposedText: s.proposedText + a.text };
    case "DONE_OK":
      return { ...s, state: "done_ok", proposedText: a.content, errors: [] };
    case "DONE_ERR":
      return { ...s, state: "done_err", proposedText: a.content, errors: a.errors };
    case "ERROR":
      return { ...s, state: "error", errors: [a.message] };
    case "RESET":
      return INITIAL;
    case "PHASE":
      return { ...s, state: phaseToState(a.phase) };
    case "PLAN_READY":
      return { ...s, state: "plan_ready", plan: a.plan };
    case "PERSONA_CREATED":
      return {
        ...s,
        createdPersonas: [...s.createdPersonas, { slug: a.slug, name: a.name }],
      };
    case "CONFIRM_STARTED":
      return { ...s, state: "generating", createdPersonas: [] };
    case "SET_PROPOSED_TEXT":
      return { ...s, proposedText: a.content };
  }
}

export function useDraftStream(
  target: "persona" | "preset",
  targetId: string | null,
) {
  const [state, dispatch] = useReducer(reducer, INITIAL);
  const stateRef = useRef(state);
  useEffect(() => { stateRef.current = state; });

  const send = (instruction: string, currentContent?: string): void => {
    void (async () => {
      dispatch({ type: "SEND_STARTED" });
      const url = target === "persona" ? "/api/personas/draft" : "/api/panel-presets/draft";
      const payload: Record<string, unknown> =
        target === "persona"
          ? { target_id: targetId, instruction }
          : { target_name: targetId, instruction };
      if (currentContent !== undefined) {
        payload.current_content = currentContent;
      }
      const body = JSON.stringify(payload);

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

  const sendAutoGen = (instruction: string): void => {
    void (async () => {
      dispatch({ type: "SEND_STARTED" });
      const url = "/api/panel-presets/auto-gen";
      const body = JSON.stringify({ instruction });

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

  const confirmPlan = (): void => {
    const currentPlan = stateRef.current.plan;
    if (!currentPlan) return;
    void (async () => {
      dispatch({ type: "CONFIRM_STARTED" });
      const url = "/api/panel-presets/auto-gen/confirm";
      const body = JSON.stringify({ plan: currentPlan });

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
    plan: state.plan,
    createdPersonas: state.createdPersonas,
    send,
    sendAutoGen,
    confirmPlan,
    setProposedText: (content: string) => dispatch({ type: "SET_PROPOSED_TEXT", content }),
    reset: () => dispatch({ type: "RESET" }),
  };
}

/** Consumes an SSE ReadableStream; returns after the first terminal event (done/error/plan_ready). */
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
    let idx;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const record = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      if (handleRecord(record, dispatch)) break outer;
    }
  }
  if (buf.trim()) handleRecord(buf, dispatch);
}

/** Parses and dispatches one SSE record. Returns true if the event was terminal (done/error/plan_ready). */
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
  } else if (event === "phase" && typeof parsed === "object" && parsed !== null) {
    const p = parsed as { phase?: unknown };
    dispatch({ type: "PHASE", phase: String(p.phase ?? "") });
    return false;
  } else if (event === "plan_ready" && typeof parsed === "object" && parsed !== null) {
    const p = parsed as { plan?: unknown };
    dispatch({ type: "PLAN_READY", plan: p.plan as PresetPlan });
    return true;
  } else if (event === "persona_created" && typeof parsed === "object" && parsed !== null) {
    const p = parsed as { slug?: unknown; name?: unknown };
    dispatch({
      type: "PERSONA_CREATED",
      slug: String(p.slug ?? ""),
      name: String(p.name ?? ""),
    });
    return false;
  }
  return false;
}
