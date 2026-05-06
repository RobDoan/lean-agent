import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ProjectSummary } from "@/lib/types";

export function ProjectCard({ project }: { project: ProjectSummary }) {
  return (
    <Card className="h-full transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle className="line-clamp-2">{project.idea ?? project.slug}</CardTitle>
        {project.idea != null && <CardDescription>{project.slug}</CardDescription>}
      </CardHeader>
      <CardContent className="text-sm text-muted-foreground">
        <p>
          {project.hypothesis_count} hypotheses · {project.run_count} run ·{" "}
          {project.with_synthesis_count} with synthesis
        </p>
      </CardContent>
    </Card>
  );
}
