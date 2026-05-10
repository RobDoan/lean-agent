import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ChatInput } from "@/components/EditorPage/ChatInput";
import { DeleteConfirmModal } from "@/components/EditorPage/DeleteConfirmModal";
import { DiffView } from "@/components/EditorPage/DiffView";
import { EditorHeader } from "@/components/EditorPage/EditorHeader";
import { GenerationProgress } from "@/components/EditorPage/GenerationProgress";
import { PersonaDetailPanel } from "@/components/EditorPage/PersonaDetailPanel";
import { PlanReview } from "@/components/EditorPage/PlanReview";
import { PresetHistory } from "@/components/EditorPage/PresetHistory";
import { PresetPersonaChecklist } from "@/components/EditorPage/PresetPersonaChecklist";
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

/**
 * For preset editing, two mutually exclusive modes:
 * - "prompt": user is editing via AI prompt (standard draft flow)
 * - "manual": user is editing via UI checkboxes / Add Persona
 * - null: neither (idle, no edits yet)
 */
type PresetEditMode = "prompt" | "manual" | null;

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

  // Accept button inline error
  const [acceptError, setAcceptError] = useState<string | null>(null);

  // Side panel for persona details
  const [sidePanelPersonaId, setSidePanelPersonaId] = useState<string | null>(null);

  // Preset edit mode tracking
  const [presetEditMode, setPresetEditMode] = useState<PresetEditMode>(null);

  // Manual-edit content (for preset manual mode)
  const [manualContent, setManualContent] = useState<string | null>(null);

  const isPreset = target === "preset";
  const isManualMode = isPreset && presetEditMode === "manual";
  const isPromptMode = isPreset && presetEditMode === "prompt";
  const hasManualChanges = isManualMode && manualContent !== null;

  // Commit mutation
  const commit = useMutation({
    mutationFn: async () => {
      // Decide which content to commit
      const content = isManualMode ? (manualContent ?? "") : draft.proposedText;
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
      setAcceptError(null);
      setPresetEditMode(null);
      setManualContent(null);
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

  const sendDisabled = draft.state === "streaming" || draft.state === "analyzing"
    || draft.state === "generating" || draft.state === "composing"
    || draft.state === "plan_ready" || commit.isPending || isManualMode;

  // v0.3.2: for preset create-mode, use auto-gen flow (unless refining a done_ok draft)
  const useAutoGen = target === "preset" && mode === "create";

  const handleSend = (instruction: string): void => {
    setAcceptError(null);
    setPresetEditMode("prompt");
    setManualContent(null);
    if (draft.state === "done_ok") {
      // Iterative refinement: always use standard single-shot edit (Q4-a)
      draft.send(instruction, draft.proposedText);
    } else if (useAutoGen) {
      draft.sendAutoGen(instruction);
    } else {
      draft.send(instruction);
    }
  };

  const handleConfirm = (): void => {
    draft.confirmPlan();
  };

  const handlePersonaClick = (id: string): void => {
    setSidePanelPersonaId(id);
  };

  // Manual edit: user changed checkboxes or added personas
  const handleManualContentChange = (content: string): void => {
    if (isPromptMode) return; // Block manual edits when prompt draft is showing
    setPresetEditMode("manual");
    setManualContent(content);
    setAcceptError(null);
  };

  // Manual save
  const handleManualSave = (): void => {
    if (mode === "create" && !newIdValid) {
      setAcceptError("A valid ID is required. Enter a slug-id above.");
      return;
    }
    setAcceptError(null);
    commit.mutate();
  };

  // Manual cancel
  const handleManualCancel = (): void => {
    setPresetEditMode(null);
    setManualContent(null);
    setAcceptError(null);
  };

  // Prompt accept
  const handleAccept = (): void => {
    if (draft.state !== "done_ok") {
      setAcceptError("No draft ready to accept. Send a prompt first.");
      return;
    }
    if (mode === "create" && !newIdValid) {
      setAcceptError("A valid ID is required before accepting. Enter a slug-id above.");
      return;
    }
    setAcceptError(null);
    commit.mutate();
  };

  // Prompt reject
  const handleReject = (): void => {
    setAcceptError(null);
    setPresetEditMode(null);
    draft.reset();
  };

  // Content area rendering
  const renderContent = () => {
    if (mode === "edit" && detailQuery.isPending) {
      return <Skeleton className="h-64 w-full" />;
    }
    if (mode === "edit" && detailQuery.isError) {
      return (
        <p role="alert" aria-live="polite" className="text-sm text-destructive">
          Could not load -- {detailQuery.error instanceof ApiClientError ? detailQuery.error.detail : "Could not load content"}
        </p>
      );
    }
    if (mode === "edit" && !detailQuery.data) return null;

    // v0.3.2 auto-gen states
    if (draft.state === "analyzing") {
      return (
        <div className="flex items-center gap-2 rounded-md border p-4">
          <span className="animate-pulse text-sm text-muted-foreground">Analyzing panel requirements...</span>
        </div>
      );
    }

    if (draft.state === "plan_ready" && draft.plan) {
      return (
        <PlanReview
          plan={draft.plan}
          onConfirm={handleConfirm}
          onCancel={() => { setPresetEditMode(null); draft.reset(); }}
          onPersonaClick={handlePersonaClick}
        />
      );
    }

    if (draft.state === "generating" || draft.state === "composing") {
      return (
        <GenerationProgress
          createdPersonas={draft.createdPersonas}
          phase={draft.state}
          onPersonaClick={handlePersonaClick}
        />
      );
    }

    // Preset: prompt draft result (done_ok from prompt) -- read-only checklist
    if (isPreset && isPromptMode && (draft.state === "done_ok" || draft.state === "done_err")) {
      return (
        <PresetPersonaChecklist
          content={draft.proposedText}
          onContentChange={() => {}}
          onPersonaClick={handlePersonaClick}
          readOnly
        />
      );
    }

    // Preset idle or manual mode: editable checklist
    if (isPreset && !isPromptMode && mode === "edit" && (detailQuery.data?.raw || manualContent)) {
      return (
        <PresetPersonaChecklist
          content={manualContent ?? detailQuery.data?.raw ?? ""}
          onContentChange={handleManualContentChange}
          onPersonaClick={handlePersonaClick}
        />
      );
    }

    // Preset create mode, idle: show empty state with prompt hint
    if (isPreset && !isPromptMode && mode === "create" && draft.state === "idle") {
      return (
        <div className="flex items-center justify-center rounded-md border border-dashed p-8">
          <p className="text-sm text-muted-foreground">
            Describe the panel you want to create using the prompt below.
          </p>
        </div>
      );
    }

    // Preset streaming: show spinner instead of diff
    if (isPreset && draft.state === "streaming") {
      return (
        <div className="flex items-center gap-2 rounded-md border p-4">
          <span className="animate-pulse text-sm text-muted-foreground">Generating preset draft...</span>
        </div>
      );
    }

    // Standard states (persona)
    if (draft.state === "idle") {
      return (
        <pre className="not-prose whitespace-pre-wrap rounded-md border bg-muted/40 p-4 font-mono text-sm">
          {detailQuery.data?.raw ?? ""}
        </pre>
      );
    }

    // Persona diff view (only for personas)
    return <DiffView left={detailQuery.data?.raw ?? ""} right={draft.proposedText} />;
  };

  // Bottom bar: choose between manual vs prompt controls
  const renderBottomBar = () => {
    if (isManualMode && hasManualChanges) {
      // Manual editing mode: warning replaces prompt, Save / Cancel buttons
      return (
        <div className="border-t bg-muted/30 px-6 py-3">
          <div className="grid grid-cols-[1fr_auto_auto] items-end gap-2">
            <p className="rounded-md border border-destructive bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
              You have unsaved manual edits. Save this version before using the prompt editor.
            </p>
            <button
              type="button"
              onClick={handleManualCancel}
              disabled={commit.isPending}
              className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleManualSave}
              disabled={commit.isPending}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {commit.isPending ? "Saving\u2026" : "Save"}
            </button>
          </div>
          {acceptError && (
            <p role="alert" aria-live="polite" className="mt-2 text-sm text-destructive">
              {acceptError}
            </p>
          )}
          {commit.isError && (
            <p role="alert" aria-live="polite" className="mt-2 text-sm text-destructive">
              Save failed -- {commit.error instanceof ApiClientError ? commit.error.detail : String(commit.error)}
            </p>
          )}
        </div>
      );
    }

    // Default: prompt mode controls
    return (
      <div className="border-t bg-muted/30 px-6 py-3">
        <div className="grid grid-cols-[1fr_auto_auto] items-end gap-2">
          <ChatInput onSend={handleSend} disabled={sendDisabled} />
          <button
            type="button"
            onClick={handleReject}
            disabled={draft.state === "idle" || commit.isPending}
            className="rounded-md border px-3 py-2 text-sm disabled:opacity-50"
          >
            Reject
          </button>
          <button
            type="button"
            onClick={handleAccept}
            disabled={commit.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {commit.isPending ? "Saving\u2026" : "Accept"}
          </button>
        </div>
        {acceptError && (
          <p role="alert" aria-live="polite" className="mt-2 text-sm text-destructive">
            {acceptError}
          </p>
        )}
        {commit.isError && (
          <p role="alert" aria-live="polite" className="mt-2 text-sm text-destructive">
            Save failed -- {commit.error instanceof ApiClientError ? commit.error.detail : String(commit.error)}
          </p>
        )}
      </div>
    );
  };

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
        {renderContent()}
        {draft.errors.length > 0 && (
          <p role="alert" aria-live="polite" className="mt-2 text-sm text-destructive">
            {draft.errors.join("; ")}
          </p>
        )}
        {/* Version history for preset edit mode */}
        {target === "preset" && mode === "edit" && targetId && (
          <div className="mt-4">
            <PresetHistory presetName={targetId} />
          </div>
        )}
      </div>

      {renderBottomBar()}

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

      {/* Persona detail side panel */}
      {sidePanelPersonaId && (
        <PersonaDetailPanel
          personaId={sidePanelPersonaId}
          onClose={() => setSidePanelPersonaId(null)}
        />
      )}
    </div>
  );
}
