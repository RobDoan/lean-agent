import { useQuery } from "@tanstack/react-query";

import { getPersona } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { MarkdownView } from "@/components/MarkdownView";

type PersonaDetailPanelProps = {
  personaId: string;
  onClose: () => void;
};

export function PersonaDetailPanel({ personaId, onClose }: PersonaDetailPanelProps) {
  const { data, isPending, isError } = useQuery({
    queryKey: ["personas", personaId],
    queryFn: () => getPersona(personaId),
  });

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-96 flex-col border-l bg-background shadow-lg">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold">{data?.name ?? personaId}</h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
          aria-label="Close panel"
        >
          &#10005;
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 text-sm">
        {isPending && <Skeleton className="h-64 w-full" />}
        {isError && (
          <p className="text-sm text-destructive">Could not load persona details.</p>
        )}
        {data && (
          <div className="space-y-4">
            {Object.keys(data.metadata).length > 0 && (
              <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
                {Object.entries(data.metadata).map(([k, v]) => (
                  <div key={k} className="contents">
                    <dt className="font-medium text-muted-foreground">{k}</dt>
                    <dd>{v}</dd>
                  </div>
                ))}
              </dl>
            )}

            <section>
              <h4 className="mb-1 text-xs font-medium uppercase text-muted-foreground">Backstory</h4>
              <MarkdownView markdown={data.backstory} />
            </section>

            <section>
              <h4 className="mb-1 text-xs font-medium uppercase text-muted-foreground">Beliefs</h4>
              <MarkdownView markdown={data.beliefs} />
            </section>

            <section>
              <h4 className="mb-1 text-xs font-medium uppercase text-muted-foreground">Biases</h4>
              <MarkdownView markdown={data.biases} />
            </section>

            <section>
              <h4 className="mb-1 text-xs font-medium uppercase text-muted-foreground">How they answer</h4>
              <MarkdownView markdown={data.how_she_answers} />
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
