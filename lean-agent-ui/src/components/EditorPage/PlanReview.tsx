import type { PresetPlan } from "@/lib/types";

type PlanReviewProps = {
  plan: PresetPlan;
  onConfirm: () => void;
  onCancel: () => void;
  onPersonaClick?: (id: string) => void;
};

export function PlanReview({ plan, onConfirm, onCancel, onPersonaClick }: PlanReviewProps) {
  return (
    <div className="space-y-4 rounded-md border p-4">
      <h3 className="text-sm font-medium">Panel Plan</h3>
      {plan.description && (
        <p className="text-sm text-muted-foreground">{plan.description}</p>
      )}
      {plan.reuse.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Reusing {plan.reuse.length} existing persona{plan.reuse.length !== 1 ? "s" : ""}
          </p>
          <ul className="mt-1 space-y-0.5 text-sm">
            {plan.reuse.map((id) => (
              <li key={id}>
                {onPersonaClick ? (
                  <button
                    type="button"
                    onClick={() => onPersonaClick(id)}
                    className="font-mono text-xs hover:underline"
                  >
                    {id}
                  </button>
                ) : (
                  <span className="font-mono text-xs">{id}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      {plan.create.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase text-muted-foreground">
            Creating {plan.create.length} new persona{plan.create.length !== 1 ? "s" : ""}
          </p>
          <ul className="mt-1 space-y-1 text-sm">
            {plan.create.map((p) => (
              <li key={p.slug}>
                <span className="font-mono text-xs">{p.slug}</span>
                <span className="mx-1 text-muted-foreground">--</span>
                <span className="text-muted-foreground">{p.description}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onConfirm}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Confirm &amp; Generate
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border px-3 py-2 text-sm"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
