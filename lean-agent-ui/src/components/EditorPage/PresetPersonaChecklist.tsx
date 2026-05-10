import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { listPersonas } from "@/lib/api";

type PresetPersonaChecklistProps = {
  /** The raw preset content (markdown with `> desc` and `- persona-id` lines). */
  content: string;
  /** Called whenever the user changes the checked set. Receives rebuilt content. */
  onContentChange: (content: string) => void;
  /** Called when user clicks a persona slug to see details. */
  onPersonaClick: (id: string) => void;
  /** When true, checkboxes and Add button are hidden (prompt draft is showing). */
  readOnly?: boolean;
};

/** Parse preset content into description + persona ids. */
function parsePresetContent(content: string): { description: string; ids: string[] } {
  const lines = content.split("\n");
  let description = "";
  const ids: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("> ")) {
      description = trimmed.slice(2);
    } else if (trimmed.startsWith("- ")) {
      ids.push(trimmed.slice(2).trim());
    }
  }
  return { description, ids };
}

/** Rebuild preset content from description + persona ids. */
function buildPresetContent(description: string, ids: string[]): string {
  const lines: string[] = [];
  if (description) {
    lines.push(`> ${description}`);
    lines.push("");
  }
  for (const id of ids) {
    lines.push(`- ${id}`);
  }
  lines.push(""); // trailing newline
  return lines.join("\n");
}

export function PresetPersonaChecklist({
  content,
  onContentChange,
  onPersonaClick,
  readOnly = false,
}: PresetPersonaChecklistProps) {
  const parsed = useMemo(() => parsePresetContent(content), [content]);
  // Track unchecked ids (excluded). All ids are checked by default.
  const [excludedIds, setExcludedIds] = useState<Set<string>>(new Set());
  const [addedIds, setAddedIds] = useState<string[]>([]);
  const [showPicker, setShowPicker] = useState(false);

  const allIds = useMemo(
    () => [...parsed.ids, ...addedIds.filter((id) => !parsed.ids.includes(id))],
    [parsed.ids, addedIds],
  );

  const allPersonasQuery = useQuery({
    queryKey: ["personas"],
    queryFn: listPersonas,
  });

  const personaNameMap = new Map(
    (allPersonasQuery.data ?? []).map((p) => [p.id, p.name]),
  );

  const isChecked = (id: string) => !excludedIds.has(id);

  const toggle = (id: string) => {
    if (readOnly) return;
    setExcludedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      const checkedIds = allIds.filter((i) => !next.has(i));
      onContentChange(buildPresetContent(parsed.description, checkedIds));
      return next;
    });
  };

  const addPersona = (id: string) => {
    if (readOnly || allIds.includes(id)) return;
    setAddedIds((prev) => [...prev, id]);
    const updatedAll = [...allIds, id];
    const checkedIds = updatedAll.filter((i) => !excludedIds.has(i));
    onContentChange(buildPresetContent(parsed.description, checkedIds));
    setShowPicker(false);
  };

  const availableToAdd = (allPersonasQuery.data ?? []).filter(
    (p) => !allIds.includes(p.id),
  );

  return (
    <div className="space-y-4 rounded-md border p-4">
      {parsed.description && (
        <p className="text-sm text-muted-foreground italic">{parsed.description}</p>
      )}

      <div className="space-y-1">
        {allIds.map((id) => (
          <div key={id} className="flex items-center gap-2 rounded px-2 py-1 hover:bg-accent/50">
            {!readOnly && (
              <input
                type="checkbox"
                checked={isChecked(id)}
                onChange={() => toggle(id)}
                className="h-4 w-4 rounded border"
                aria-label={`Include ${id}`}
              />
            )}
            <button
              type="button"
              onClick={() => onPersonaClick(id)}
              className="flex-1 text-left text-sm hover:underline"
            >
              <span className="font-mono text-xs">{id}</span>
              {personaNameMap.has(id) && (
                <span className="ml-2 text-muted-foreground">
                  ({personaNameMap.get(id)})
                </span>
              )}
            </button>
          </div>
        ))}
      </div>

      {!readOnly && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowPicker(!showPicker)}
            className="rounded-md border px-3 py-1.5 text-sm hover:bg-accent"
          >
            + Add Persona
          </button>

          {showPicker && (
            <div className="absolute left-0 top-full z-10 mt-1 max-h-60 w-72 overflow-y-auto rounded-md border bg-background shadow-md">
              {availableToAdd.length === 0 ? (
                <p className="p-3 text-xs text-muted-foreground">
                  All personas are already in this preset.
                </p>
              ) : (
                availableToAdd.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => addPersona(p.id)}
                    className="block w-full px-3 py-2 text-left text-sm hover:bg-accent"
                  >
                    <span className="font-mono text-xs">{p.id}</span>
                    <span className="ml-2 text-muted-foreground">{p.name}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
