"use client";

import { useState } from "react";

interface ApiKeyInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function ApiKeyInput({ value, onChange }: ApiKeyInputProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground" htmlFor="api-key">
        OpenAI API Key
      </label>
      <div className="relative">
        <input
          id="api-key"
          data-testid="api-key-input"
          type={visible ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="sk-..."
          className="w-full rounded-lg border border-border bg-surface px-4 py-3 text-foreground placeholder:text-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <button
          type="button"
          data-testid="api-key-toggle"
          onClick={() => setVisible(!visible)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-foreground transition-colors"
        >
          {visible ? "Hide" : "Show"}
        </button>
      </div>
    </div>
  );
}
