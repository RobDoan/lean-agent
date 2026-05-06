interface Props {
  items: string[];
}

export function IdeaTriage({ items }: Props) {
  return (
    <section>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Section 1
      </p>
      <h2 className="mt-1 text-xl font-semibold">Idea Triage</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Adjacent angles to consider before diving into hypotheses.
      </p>

      <div className="mt-4 flex flex-col gap-2.5">
        {items.map((text, i) => (
          <div
            key={i}
            className="flex items-start gap-2.5 rounded-md border bg-muted/30 px-3 py-2.5"
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-primary/10 text-xs font-semibold text-primary">
              {i + 1}
            </span>
            <span className="text-sm leading-relaxed">{text}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
