import { Link, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { HypothesisListItem as Item } from "@/lib/types";

export function HypothesisListItem({ slug, item }: { slug: string; item: Item }) {
  const { hid } = useParams<{ hid?: string }>();
  const isActive = hid === item.id;
  return (
    <Link
      to={`/p/${slug}/h/${item.id}`}
      className={cn(
        "flex flex-col gap-1 rounded-md px-2 py-2 text-sm hover:bg-muted/60",
        isActive && "bg-muted",
      )}
    >
      <span className="flex items-center gap-2">
        <span className="font-mono font-semibold">{item.id}</span>
        {!item.has_run && (
          <Badge variant="secondary" className="text-xs opacity-70">
            not run
          </Badge>
        )}
      </span>
      <span className="line-clamp-2 text-muted-foreground">{item.title}</span>
    </Link>
  );
}
