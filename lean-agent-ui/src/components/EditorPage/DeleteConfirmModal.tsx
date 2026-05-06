type DeleteConfirmModalProps = {
  open: boolean;
  targetName: string;
  cascadeBlockedBy?: string[];
  onConfirm: () => void;
  onCancel: () => void;
};

export function DeleteConfirmModal({
  open, targetName, cascadeBlockedBy, onConfirm, onCancel,
}: DeleteConfirmModalProps) {
  if (!open) return null;

  const isBlocked = (cascadeBlockedBy?.length ?? 0) > 0;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
    >
      <div className="w-full max-w-md rounded-lg bg-background p-6 shadow-lg">
        <h2 className="text-lg font-semibold">Delete {targetName}?</h2>
        {isBlocked ? (
          <>
            <p className="mt-2 text-sm text-destructive">
              Cannot delete — referenced by these panel preset(s):
            </p>
            <ul className="mt-2 list-disc pl-6 text-sm">
              {cascadeBlockedBy!.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-muted-foreground">
              Remove this id from the listed presets first, then try again.
            </p>
          </>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">This cannot be undone.</p>
        )}
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border px-3 py-1.5 text-sm"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isBlocked}
            className="rounded-md bg-destructive px-3 py-1.5 text-sm text-destructive-foreground disabled:opacity-50"
          >
            Confirm delete
          </button>
        </div>
      </div>
    </div>
  );
}
