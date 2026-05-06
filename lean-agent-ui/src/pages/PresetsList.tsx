import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError, listPresets } from "@/lib/api";

export default function PresetsList() {
  const { isPending, isError, data, error } = useQuery({
    queryKey: ["panel-presets"],
    queryFn: listPresets,
  });

  return (
    <main className="overflow-y-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Panel Presets</h1>
        <Link
          to="/panel-presets/new"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          + New Panel Preset
        </Link>
      </div>

      {isPending && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(20rem,1fr))] auto-rows-fr gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      )}

      {isError && (
        <p role="alert" aria-live="polite" className="text-sm text-destructive">
          Could not load — {error instanceof ApiClientError ? error.detail : "Could not load panel presets"}
        </p>
      )}

      {data && data.length === 0 && (
        <p className="text-sm text-muted-foreground">No panel presets yet. Click "+ New Panel Preset" to create one.</p>
      )}

      {data && data.length > 0 && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(20rem,1fr))] auto-rows-fr gap-4">
          {data.map((p) => (
            <Link
              key={p.name}
              to={`/panel-presets/${p.name}`}
              className="block rounded-lg border p-4 hover:bg-accent"
            >
              <h2 className="font-medium">{p.name}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{p.persona_count} {p.persona_count === 1 ? "persona" : "personas"}</p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
