"use client";

import { useState, useEffect } from "react";
import { ApiKeyInput } from "./components/ApiKeyInput";
import { UploadZone } from "./components/UploadZone";
import { GenerateButton } from "./components/GenerateButton";

const SESSION_KEY = "openai_api_key";

export default function Home() {
  const [apiKey, setApiKey] = useState("");
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) setApiKey(stored);
  }, []);

  function handleApiKeyChange(value: string) {
    setApiKey(value);
    sessionStorage.setItem(SESSION_KEY, value);
  }

  function handleGenerate() {
    // Will be implemented in Task 7/8
  }

  const canGenerate = apiKey.trim().length > 0 && file !== null;

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          PaperToCode
        </h1>
        <p className="text-muted text-lg leading-relaxed">
          Upload a research paper and get a research-grade Colab notebook with
          implementations, visualizations, and exercises.
        </p>
      </header>

      <div className="space-y-6">
        <ApiKeyInput value={apiKey} onChange={handleApiKeyChange} />
        <UploadZone
          file={file}
          onFile={setFile}
          onRemove={() => setFile(null)}
        />
        <GenerateButton disabled={!canGenerate} onClick={handleGenerate} />
      </div>
    </div>
  );
}
