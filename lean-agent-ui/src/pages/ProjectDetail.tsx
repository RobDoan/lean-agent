import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { HypothesisContent } from "@/components/HypothesisContent";
import { HypothesisListItem } from "@/components/HypothesisListItem";
import { IdeaTriage } from "@/components/IdeaTriage";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError, getHypothesis, getProject } from "@/lib/api";
import type { ProjectDetail as ProjectDetailDto } from "@/lib/types";

export default function ProjectDetail() {
  const { slug, hid } = useParams<{ slug: string; hid?: string }>();

  const projectQuery = useQuery({
    queryKey: ["projects", slug],
    queryFn: () => getProject(slug!),
    enabled: Boolean(slug),
  });

  const hypothesisQuery = useQuery({
    queryKey: ["hypotheses", slug, hid],
    queryFn: () => getHypothesis(slug!, hid!),
    enabled: Boolean(slug && hid),
  });

  if (!slug) return null;

  return (
    <div className="grid h-full grid-cols-[18rem_1fr]">
      <aside className="overflow-y-auto border-r p-4">
        <Link to="/" className="mb-4 inline-block text-sm text-muted-foreground hover:underline">
          ← back to projects
        </Link>
        {projectQuery.isPending && <Skeleton className="h-40 w-full" />}
        {projectQuery.isError && (
          <p role="alert" aria-live="polite" className="text-sm text-destructive">
            Could not load — {projectQuery.error instanceof ApiClientError ? projectQuery.error.detail : "Could not load project"}
          </p>
        )}
        {projectQuery.data && (
          <Sidebar slug={slug} project={projectQuery.data} />
        )}
      </aside>

      <main className="overflow-y-auto p-6">
        {!hid && projectQuery.data && projectQuery.data.idea_triage.length > 0 && (
          <IdeaTriage items={projectQuery.data.idea_triage} />
        )}
        {!hid && (!projectQuery.data || projectQuery.data.idea_triage.length === 0) && (
          <p className="text-sm text-muted-foreground">Select a hypothesis from the sidebar.</p>
        )}
        {hid && hypothesisQuery.isPending && <Skeleton className="h-40 w-full" />}
        {hid && hypothesisQuery.isError && (
          <p role="alert" aria-live="polite" className="text-sm text-destructive">
            Could not load — {hypothesisQuery.error instanceof ApiClientError ? hypothesisQuery.error.detail : "Could not load hypothesis"}
          </p>
        )}
        {hid && hypothesisQuery.data && (
          <HypothesisContent slug={slug} detail={hypothesisQuery.data} />
        )}
      </main>
    </div>
  );
}

function Sidebar({ slug, project }: { slug: string; project: ProjectDetailDto }) {
  const withSynthesis = project.hypotheses.filter((h) => h.has_synthesis);
  const without = project.hypotheses.filter((h) => !h.has_synthesis);

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold">{project.idea ?? project.slug}</h2>
      <p className="text-xs text-muted-foreground">{project.slug}</p>

      <Separator className="my-3" />

      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        With synthesis ({withSynthesis.length})
      </h3>
      <div className="flex flex-col">
        {withSynthesis.length === 0 ? (
          <p className="px-2 py-1 text-xs text-muted-foreground">— none —</p>
        ) : (
          withSynthesis.map((h) => <HypothesisListItem key={h.id} slug={slug} item={h} />)
        )}
      </div>

      <h3 className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        No synthesis ({without.length})
      </h3>
      <div className="flex flex-col">
        {without.length === 0 ? (
          <p className="px-2 py-1 text-xs text-muted-foreground">— none —</p>
        ) : (
          without.map((h) => <HypothesisListItem key={h.id} slug={slug} item={h} />)
        )}
      </div>
    </div>
  );
}
