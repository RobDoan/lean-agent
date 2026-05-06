import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const HEADING_DEMOTE: Components = {
  h1: "h2",
  h2: "h3",
  h3: "h4",
};

export function MarkdownView({ markdown }: { markdown: string }) {
  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={HEADING_DEMOTE}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
