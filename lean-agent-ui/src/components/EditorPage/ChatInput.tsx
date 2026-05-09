import { useEffect, useRef, useState } from "react";

type ChatInputProps = {
  onSend: (instruction: string) => void;
  disabled: boolean;
};

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus when enabled (IDLE state or after Reject)
  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const submit = (): void => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="chat-input" className="text-xs font-medium text-muted-foreground">
        Describe the change
      </label>
      <div className="flex items-end gap-2">
        <textarea
          id="chat-input"
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          rows={2}
          disabled={disabled}
          placeholder="e.g. Make her more skeptical about AI hype..."
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
    </div>
  );
}
