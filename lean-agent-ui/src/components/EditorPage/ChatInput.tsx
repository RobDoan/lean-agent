import { useState } from "react";

type ChatInputProps = {
  onSend: (instruction: string) => void;
  disabled: boolean;
};

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  const submit = (): void => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="flex items-end gap-2">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        rows={2}
        disabled={disabled}
        placeholder="describe the change you want…"
        className="flex-1 resize-y rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2"
      />
      <button
        type="button"
        onClick={submit}
        disabled={disabled || !value.trim()}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
      >
        Send
      </button>
    </div>
  );
}
