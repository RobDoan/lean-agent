import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ChatInput } from "@/components/EditorPage/ChatInput";
import { DeleteConfirmModal } from "@/components/EditorPage/DeleteConfirmModal";
import { DiffView } from "@/components/EditorPage/DiffView";
import { EditorHeader } from "@/components/EditorPage/EditorHeader";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ApiClientError,
  createPersona,
  createPreset,
  deletePersona,
  deletePreset,
  editPersona,
  editPreset,
  getPersona,
  getPreset,
} from "@/lib/api";
import { useDraftStream } from "@/lib/useDraftStream";

const SLUG_RE = /^[a-z0-9][a-z0-9-]*[a-z0-9]$/;

type EditorPageProps = {
  target: "persona" | "preset";
  mode: "create" | "edit";
};

export default function EditorPage({ target, mode }: EditorPageProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const params = useParams<{ id?: string; name?: string }>();
  const targetId = mode === "edit" ? (target === "persona" ? params.id ?? null : params.name ?? null) : null;

  // Current content (edit mode only)
  const detailQuery = useQuery({
    queryKey: target === "persona" ? ["personas", targetId] : ["panel-presets", targetId],
    queryFn: () =>
      target === "persona"
        ? getPersona(targetId!).then((d) => ({ raw: d.raw_content, name: d.name }))
        : getPreset(targetId!).then((d) => ({ raw: d.raw_content, name: d.name })),
    enabled: mode === "edit" && Boolean(targetId),
  });

  // Streaming hook
  const draft = useDraftStream(target, targetId);

  // Create-mode id input
  const [newId, setNewId] = useState("");
  const newIdValid = SLUG_RE.test(newId);

  // Commit mutation
  const commit = useMutation({
    mutationFn: async () => {
      const content = draft.proposedText;
      if (mode === "create") {
        if (target === "persona") {
          return createPersona({ id: newId, content });
        }
        return createPreset({ name: newId, content });
      }
      if (target === "persona") {
        return editPersona(targetId!, content);
      }
      return editPreset(targetId!, content);
    },
    onSuccess: async () => {
      const queryKey = target === "persona" ? ["personas"] : ["panel-presets"];
      await queryClient.invalidateQueries({ queryKey });
      if (mode === "edit") {
        await queryClient.invalidateQueries({ queryKey: [...queryKey, targetId] });
      }
      const nextId = mode === "create" ? newId : targetId;
      navigate(target === "persona" ? `/personas/${nextId}` : `/panel-presets/${nextId}`);
    },
  });

  // Delete mutation + modal
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [cascadeBlockedBy, setCascadeBlockedBy] = useState<string[] | undefined>(undefined);
  const del = useMutation({
    mutationFn: () =>
      target === "persona" ? deletePersona(targetId!) : deletePreset(targetId!),
    onError: (err: unknown) => {
      if (err instanceof ApiClientError && err.status === 409) {
        const refs = (err as ApiClientError & { referencedBy?: string[] }).referencedBy;
        if (refs) setCascadeBlockedBy(refs);
      }
    },
    onSuccess: async () => {
      const queryKey = target === "persona" ? ["personas"] : ["panel-presets"];
      await queryClient.invalidateQueries({ queryKey });
      navigate(target === "persona" ? "/personas" : "/panel-presets");
    },
  });

  const onConfirmDelete = (): void => {
    setCascadeBlockedBy(undefined);
    del.mutate();
  };

  const sendDisabled = draft.state === "streaming" || commit.isPending;
  const acceptEnabled = draft.state === "done_ok";

  // Render
  return (
    <div className="grid h-full grid-rows-[auto_1fr_auto]">
      <EditorHeader
        mode={mode}
        title={mode === "edit" ? detailQuery.data?.name ?? "" : ""}
        subtitle={mode === "edit" ? targetId ?? "" : "New " + (target === "persona" ? "persona" : "panel preset")}
        onDelete={() => setConfirmOpen(true)}
        onIdChange={setNewId}
        idValue={newId}
        idValid={newIdValid || newId === ""}
      />

      <div className="overflow-y-auto px-6 py-4">
        {mode === "edit" && detailQuery.isPending && <Skeleton className="h-64 w-full" />}
        {mode === "edit" && detailQuery.isError && (
          <p role="alert" aria-live="polite" className="text-sm text-destructive">
            Could not load — {detailQuery.error instanceof ApiClientError ? detailQuery.error.detail : "Could not load content"}
          </p>
        )}
        {(mode === "create" || detailQuery.data) && (
          draft.state === "idle" ? (
            <pre className="not-prose whitespace-pre-wrap rounded-md border bg-muted/40 p-4 font-mono text-sm">
              {detailQuery.data?.raw ?? ""}
            </pre>
          ) : (
            <DiffView left={detailQuery.data?.raw ?? ""} right={draft.proposedText} />
          )
        )}
        {draft.errors.length > 0 && (
          <p role="alert" aria-live="polite" className="mt-2 text-sm text-destructive">
            {draft.errors.join("; ")}
          </p>
        )}
      </div>

      <div className="border-t bg-background px-6 py-3">
        <div className="grid grid-cols-[1fr_auto_auto] items-end gap-2">
          <ChatInput onSend={draft.send} disabled={sendDisabled} />
          <button
            type="button"
            onClick={draft.reset}
            disabled={draft.state === "idle" || commit.isPending}
            className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
          >
            Reject
          </button>
          <button
            type="button"
            onClick={() => commit.mutate()}
            disabled={!acceptEnabled || commit.isPending || (mode === "create" && !newIdValid)}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {commit.isPending ? "Saving…" : "Accept"}
          </button>
        </div>
        {commit.isError && (
          <p role="alert" aria-live="polite" className="mt-2 text-sm text-destructive">
            Save failed — {commit.error instanceof ApiClientError ? commit.error.detail : String(commit.error)}
          </p>
        )}
      </div>

      <DeleteConfirmModal
        open={confirmOpen}
        targetName={targetId ?? ""}
        cascadeBlockedBy={cascadeBlockedBy}
        onConfirm={onConfirmDelete}
        onCancel={() => {
          setConfirmOpen(false);
          setCascadeBlockedBy(undefined);
        }}
      />
    </div>
  );
}
