import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import * as api from "@/lib/api";
import { renderWithQuery } from "@/lib/test/query";
import { mockSseResponse } from "@/lib/test/sse";
import EditorPage from "./EditorPage";


const PERSONA_ALICE = `---
id: alice
name: Alice
---

## Backstory
x
## Beliefs
x
## Biases
x
## How she answers questions
x
`;


function _renderEdit(target: "persona" | "preset", id: string) {
  return renderWithQuery(
    <MemoryRouter initialEntries={[`/${target === "persona" ? "personas" : "panel-presets"}/${id}`]}>
      <Routes>
        <Route
          path={target === "persona" ? "/personas/:id" : "/panel-presets/:name"}
          element={<EditorPage target={target} mode="edit" />}
        />
        <Route path="/personas" element={<p>back</p>} />
        <Route path="/panel-presets" element={<p>back</p>} />
      </Routes>
    </MemoryRouter>,
  );
}


describe("EditorPage edit mode (persona)", () => {
  it("loads current content + Send/Accept/Reject disabled in IDLE", async () => {
    vi.spyOn(api, "getPersona").mockResolvedValue({
      id: "alice", name: "Alice", metadata: {},
      backstory: "x", beliefs: "x", biases: "x", how_she_answers: "x",
      raw_content: PERSONA_ALICE,
    });

    _renderEdit("persona", "alice");

    // In IDLE, content is shown in single-pane preview
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /accept/i })).toBeDisabled();
  });

  it("Accept enables only after done.ok=true; PUT called on click; navigates back", async () => {
    vi.spyOn(api, "getPersona").mockResolvedValue({
      id: "alice", name: "Alice", metadata: {},
      backstory: "x", beliefs: "x", biases: "x", how_she_answers: "x",
      raw_content: PERSONA_ALICE,
    });
    const editSpy = vi.spyOn(api, "editPersona").mockResolvedValue({
      id: "alice", name: "Alice", metadata: {},
      backstory: "x", beliefs: "x", biases: "x", how_she_answers: "x",
      raw_content: PERSONA_ALICE,
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "token", data: { text: PERSONA_ALICE } },
        { event: "done", data: { ok: true, content: PERSONA_ALICE } },
      ]),
    );

    _renderEdit("persona", "alice");
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());

    await userEvent.type(screen.getByRole("textbox"), "no change");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    const accept = await screen.findByRole("button", { name: /accept/i });
    await waitFor(() => expect(accept).toBeEnabled());

    await userEvent.click(accept);

    await waitFor(() => expect(editSpy).toHaveBeenCalledWith("alice", PERSONA_ALICE));
  });

  it("Accept stays disabled when done.ok=false", async () => {
    vi.spyOn(api, "getPersona").mockResolvedValue({
      id: "alice", name: "Alice", metadata: {},
      backstory: "x", beliefs: "x", biases: "x", how_she_answers: "x",
      raw_content: PERSONA_ALICE,
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([
        { event: "done", data: { ok: false, content: "garbage", errors: ["bad"] } },
      ]),
    );

    _renderEdit("persona", "alice");
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());

    await userEvent.type(screen.getByRole("textbox"), "x");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(screen.getByText(/bad/)).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /accept/i })).toBeDisabled();
  });

  it("Reject returns to IDLE", async () => {
    vi.spyOn(api, "getPersona").mockResolvedValue({
      id: "alice", name: "Alice", metadata: {},
      backstory: "x", beliefs: "x", biases: "x", how_she_answers: "x",
      raw_content: PERSONA_ALICE,
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      mockSseResponse([{ event: "done", data: { ok: true, content: "Y" } }]),
    );

    _renderEdit("persona", "alice");
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());

    await userEvent.type(screen.getByRole("textbox"), "x");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    const accept = await screen.findByRole("button", { name: /accept/i });
    await waitFor(() => expect(accept).toBeEnabled());

    await userEvent.click(screen.getByRole("button", { name: /reject/i }));
    expect(screen.getByRole("button", { name: /accept/i })).toBeDisabled();
  });

  it("Delete shows modal; cascade-409 disables Confirm and lists presets", async () => {
    vi.spyOn(api, "getPersona").mockResolvedValue({
      id: "alice", name: "Alice", metadata: {},
      backstory: "x", beliefs: "x", biases: "x", how_she_answers: "x",
      raw_content: PERSONA_ALICE,
    });
    const err = new api.ApiClientError(409, "in use");
    (err as api.ApiClientError & { referencedBy: string[] }).referencedBy = ["smb-saas"];
    vi.spyOn(api, "deletePersona").mockRejectedValue(err);

    _renderEdit("persona", "alice");
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /^delete$/i }));
    await userEvent.click(screen.getByRole("button", { name: /confirm delete/i }));

    await waitFor(() => expect(screen.getByText("smb-saas")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /confirm delete/i })).toBeDisabled();
  });
});
