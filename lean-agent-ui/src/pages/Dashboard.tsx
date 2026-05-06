import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { ProjectCard } from "@/components/ProjectCard";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError, listProjects } from "@/lib/api";

export default function Dashboard() {
  const { isPending, isError, data, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
  });

  return (
    <main className="overflow-y-auto p-6">
      <h1 className="mb-6 text-2xl font-semibold">Projects</h1>

      {isPending && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(20rem,1fr))] auto-rows-fr gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      )}

      {isError && (
        <p role="alert" aria-live="polite" className="text-sm text-destructive">
          Could not load — {error instanceof ApiClientError ? error.detail : "Could not load projects"}
        </p>
      )}

      {data && data.length === 0 && (
        <p className="text-sm text-muted-foreground">No projects yet.</p>
      )}

      {data && data.length > 0 && (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(20rem,1fr))] auto-rows-fr gap-4">
          {data.map((project) => (
            <Link key={project.slug} to={`/p/${project.slug}`} className="h-full">
              <ProjectCard project={project} />
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
