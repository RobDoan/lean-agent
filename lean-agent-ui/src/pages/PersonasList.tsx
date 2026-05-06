import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError, listPersonas } from "@/lib/api";

export default function PersonasList() {
  const { isPending, isError, data, error } = useQuery({
    queryKey: ["personas"],
    queryFn: listPersonas,
  });

  return (
    <main className="overflow-y-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Personas</h1>
        <Link
          to="/personas/new"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          + New Persona
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
          Could not load — {error instanceof ApiClientError ? error.detail : "Could not load personas"}
        </p>
      )}

      {data && data.length === 0 && (
        <p className="text-sm text-muted-foreground">No personas yet. Click "+ New Persona" to create one.</p>
      )}

      {data && data.length > 0 && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(20rem,1fr))] auto-rows-fr gap-4">
          {data.map((p) => (
            <Link
              key={p.id}
              to={`/personas/${p.id}`}
              className="block rounded-lg border p-4 hover:bg-accent"
            >
              <h2 className="font-medium">{p.name}</h2>
              <p className="text-xs text-muted-foreground">{p.id}</p>
              {p.role && <p className="mt-2 text-sm">{p.role}</p>}
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
