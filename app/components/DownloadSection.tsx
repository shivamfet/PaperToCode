"use client";

import { useState } from "react";

interface DownloadSectionProps {
  visible: boolean;
  jobId: string;
}

export function DownloadSection({ visible, jobId }: DownloadSectionProps) {
  const [colabError, setColabError] = useState(false);

  if (!visible) return null;

  async function handleOpenInColab() {
    try {
      // Fetch the notebook content
      const resp = await fetch(`/api/download/${jobId}`);
      if (!resp.ok) throw new Error("Failed to download notebook");
      const content = await resp.text();

      // Create a GitHub Gist via the API
      const gistResp = await fetch("https://api.github.com/gists", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: "PaperToCode generated notebook",
          public: false,
          files: { "notebook.ipynb": { content } },
        }),
      });

      if (!gistResp.ok) throw new Error("Failed to create Gist");
      const gist = await gistResp.json();

      // Open in Colab
      window.open(
        `https://colab.research.google.com/gist/${gist.owner.login}/${gist.id}/notebook.ipynb`,
        "_blank"
      );
    } catch {
      // Fallback: just download
      setColabError(true);
    }
  }

  return (
    <div data-testid="download-section" className="flex gap-4">
      <a
        data-testid="download-button"
        href={`/api/download/${jobId}`}
        download="notebook.ipynb"
        className="flex-1 rounded-lg bg-accent px-6 py-3 font-medium text-background text-center transition-colors hover:bg-accent-hover"
      >
        Download .ipynb
      </a>
      <button
        type="button"
        data-testid="colab-button"
        onClick={handleOpenInColab}
        className="flex-1 rounded-lg border border-accent px-6 py-3 font-medium text-accent text-center transition-colors hover:bg-surface-hover"
      >
        {colabError ? "Gist failed — Download instead" : "Open in Google Colab"}
      </button>
    </div>
  );
}
