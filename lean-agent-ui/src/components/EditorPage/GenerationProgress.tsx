type GenerationProgressProps = {
  createdPersonas: { slug: string; name: string }[];
  phase: "generating" | "composing";
  onPersonaClick?: (id: string) => void;
};

export function GenerationProgress({ createdPersonas, phase, onPersonaClick }: GenerationProgressProps) {
  return (
    <div className="space-y-3 rounded-md border p-4">
      <h3 className="text-sm font-medium">
        {phase === "composing" ? "Composing preset..." : "Generating personas..."}
      </h3>
      {createdPersonas.length > 0 && (
        <ul className="space-y-1 text-sm">
          {createdPersonas.map((p) => (
            <li key={p.slug} className="flex items-center gap-2">
              <span className="text-green-600">&#10003;</span>
              {onPersonaClick ? (
                <button
                  type="button"
                  onClick={() => onPersonaClick(p.slug)}
                  className="text-left hover:underline"
                >
                  <span className="font-mono text-xs">{p.slug}</span>
                  <span className="ml-1 text-muted-foreground">({p.name})</span>
                </button>
              ) : (
                <>
                  <span className="font-mono text-xs">{p.slug}</span>
                  <span className="text-muted-foreground">({p.name})</span>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      {phase === "generating" && (
        <p className="animate-pulse text-xs text-muted-foreground">Generating...</p>
      )}
      {phase === "composing" && (
        <p className="animate-pulse text-xs text-muted-foreground">Assembling preset from all personas...</p>
      )}
    </div>
  );
}
