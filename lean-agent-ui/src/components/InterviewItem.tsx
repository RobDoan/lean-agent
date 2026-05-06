import { useState } from "react";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError, getInterview } from "@/lib/api";
import type { InterviewMeta } from "@/lib/types";

import { MarkdownView } from "./MarkdownView";

interface Props {
  slug: string;
  hid: string;
  meta: InterviewMeta;
}

export function InterviewItem({ slug, hid, meta }: Props) {
  const [open, setOpen] = useState(false);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleOpenChange(next: boolean) {
    setOpen(next);
    if (next && markdown === null && !loading) {
      setLoading(true);
      setError(null);
      try {
        const result = await getInterview(slug, hid, meta.name);
        setMarkdown(result.markdown);
      } catch (e) {
        const msg = e instanceof ApiClientError ? e.detail : "Failed to load interview";
        setError(msg);
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <Collapsible open={open} onOpenChange={handleOpenChange}>
      <CollapsibleTrigger className="flex w-full items-center gap-2 rounded-md px-2 py-1 text-sm hover:bg-muted/60">
        <span className="font-mono">{open ? "▾" : "▸"}</span>
        <span>{meta.name}</span>
      </CollapsibleTrigger>
      <CollapsibleContent className="border-l-2 border-muted pl-3 ml-3 mt-1">
        {loading && <Skeleton className="h-20 w-full" />}
        {error && (
          <p role="alert" aria-live="polite" className="text-sm text-destructive">
            {error}
          </p>
        )}
        {markdown && <MarkdownView markdown={markdown} />}
      </CollapsibleContent>
    </Collapsible>
  );
}
