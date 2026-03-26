"use client";

import { useEffect, useRef } from "react";

interface StatusFeedProps {
  messages: string[];
  error?: string | null;
}

export function StatusFeed({ messages, error }: StatusFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === "function") {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);

  return (
    <div
      data-testid="status-feed"
      className="font-mono rounded-lg bg-surface border border-border p-4 max-h-64 overflow-y-auto text-sm"
    >
      {messages.map((msg, i) => (
        <div
          key={i}
          data-testid="status-message"
          className="py-1 text-muted leading-relaxed"
        >
          <span className="text-accent mr-2">›</span>
          {msg}
        </div>
      ))}
      {error && (
        <div
          data-testid="status-error"
          className="py-1 text-red-400 leading-relaxed"
        >
          <span className="mr-2">✕</span>
          {error}
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
