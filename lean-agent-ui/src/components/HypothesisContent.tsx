import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { HypothesisDetail } from "@/lib/types";

import { InterviewItem } from "./InterviewItem";
import { MarkdownView } from "./MarkdownView";

interface Props {
  slug: string;
  detail: HypothesisDetail;
}

export function HypothesisContent({ slug, detail }: Props) {
  const hasRun = detail.synthesis_markdown !== null || detail.sprint_markdown !== null;

  return (
    <article className="flex flex-col gap-6">
      <header>
        <p className="font-mono text-sm text-muted-foreground">{detail.id}</p>
        <h1 className="text-xl font-semibold leading-tight">{detail.title}</h1>
      </header>

      {!hasRun && (
        <p className="text-sm text-muted-foreground">
          Not yet run. <code>lean run R1 {detail.id}</code> from the CLI to populate this hypothesis.
        </p>
      )}

      {detail.interviews.length > 0 && (
        <Collapsible defaultOpen>
          <CollapsibleTrigger className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Interviews ({detail.interviews.length})
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2 flex flex-col gap-1">
            {detail.interviews.map((meta) => (
              <InterviewItem key={meta.name} slug={slug} hid={detail.id} meta={meta} />
            ))}
          </CollapsibleContent>
        </Collapsible>
      )}

      {detail.sprint_markdown && (
        <Collapsible>
          <CollapsibleTrigger className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Sprint kit
          </CollapsibleTrigger>
          <CollapsibleContent className="mt-2">
            <MarkdownView markdown={detail.sprint_markdown} />
          </CollapsibleContent>
        </Collapsible>
      )}

      {detail.synthesis_markdown && (
        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Synthesis
          </h2>
          <MarkdownView markdown={detail.synthesis_markdown} />
        </section>
      )}
    </article>
  );
}
