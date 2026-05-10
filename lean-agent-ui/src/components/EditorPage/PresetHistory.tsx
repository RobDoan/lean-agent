import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getPresetHistory, getPresetVersion } from "@/lib/api";

type PresetHistoryProps = {
  presetName: string;
};

export function PresetHistory({ presetName }: PresetHistoryProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedSha, setSelectedSha] = useState<string | null>(null);

  const historyQuery = useQuery({
    queryKey: ["panel-presets", presetName, "history"],
    queryFn: () => getPresetHistory(presetName),
    enabled: isOpen,
  });

  const versionQuery = useQuery({
    queryKey: ["panel-presets", presetName, "history", selectedSha],
    queryFn: () => getPresetVersion(presetName, selectedSha!),
    enabled: Boolean(selectedSha),
  });

  return (
    <div className="rounded-md border">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-4 py-2 text-sm font-medium hover:bg-accent/50"
      >
        <span>Version History</span>
        <span className="text-muted-foreground">{isOpen ? "\u25B2" : "\u25BC"}</span>
      </button>

      {isOpen && (
        <div className="border-t px-4 py-2">
          {historyQuery.isPending && (
            <p className="text-xs text-muted-foreground">Loading history...</p>
          )}

          {historyQuery.data && historyQuery.data.length === 0 && (
            <p className="text-xs text-muted-foreground">No version history yet.</p>
          )}

          {historyQuery.data && historyQuery.data.length > 0 && (
            <ul className="space-y-1">
              {historyQuery.data.map((entry) => (
                <li key={entry.sha}>
                  <button
                    type="button"
                    onClick={() => setSelectedSha(entry.sha === selectedSha ? null : entry.sha)}
                    className={`w-full rounded px-2 py-1 text-left text-xs hover:bg-accent/50 ${
                      selectedSha === entry.sha ? "bg-accent" : ""
                    }`}
                  >
                    <span className="font-mono text-muted-foreground">{entry.sha}</span>
                    <span className="mx-2">{entry.message}</span>
                    <span className="text-muted-foreground">
                      {new Date(entry.date).toLocaleDateString()}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {selectedSha && versionQuery.data && (
            <div className="mt-2 border-t pt-2">
              <p className="mb-1 text-xs font-medium text-muted-foreground">
                Content at {selectedSha}
              </p>
              <pre className="whitespace-pre-wrap rounded bg-muted/40 p-3 font-mono text-xs">
                {versionQuery.data.content}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
