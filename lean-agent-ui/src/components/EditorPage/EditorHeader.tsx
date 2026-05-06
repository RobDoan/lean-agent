type EditorHeaderProps = {
  mode: "edit" | "create";
  title: string;
  subtitle: string;
  onDelete: () => void;
  onIdChange: (id: string) => void;
  idValue: string;
  idValid: boolean;
};

export function EditorHeader({
  mode, title, subtitle, onDelete, onIdChange, idValue, idValid,
}: EditorHeaderProps) {
  if (mode === "edit") {
    return (
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div>
          <h2 className="font-semibold">{title}</h2>
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <button
          type="button"
          onClick={onDelete}
          className="rounded-md border border-destructive px-3 py-1.5 text-sm text-destructive hover:bg-destructive hover:text-destructive-foreground"
        >
          Delete
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between border-b px-6 py-3">
      <div className="flex flex-col gap-1">
        <input
          value={idValue}
          onChange={(e) => onIdChange(e.target.value)}
          placeholder="id (e.g. alice-pm)"
          className="rounded-md border bg-background px-2 py-1 text-sm"
          aria-invalid={!idValid && idValue !== ""}
        />
        {!idValid && idValue !== "" && (
          <p className="text-xs text-destructive">id must be lowercase letters, digits, and hyphens; 2–64 chars; no leading/trailing hyphen</p>
        )}
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </div>
    </div>
  );
}
