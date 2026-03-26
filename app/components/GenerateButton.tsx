"use client";

interface GenerateButtonProps {
  disabled: boolean;
  loading?: boolean;
  onClick: () => void;
}

export function GenerateButton({ disabled, loading, onClick }: GenerateButtonProps) {
  return (
    <button
      type="button"
      data-testid="generate-button"
      disabled={disabled}
      onClick={onClick}
      className="w-full rounded-lg bg-accent px-6 py-3 font-medium text-background transition-colors hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-accent"
    >
      {loading ? "Generating..." : "Generate Notebook"}
    </button>
  );
}
