"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { ApiKeyInput } from "./components/ApiKeyInput";
import { UploadZone } from "./components/UploadZone";
import { GenerateButton } from "./components/GenerateButton";
import { StatusFeed } from "./components/StatusFeed";
import { DownloadSection } from "./components/DownloadSection";

const SESSION_KEY = "openai_api_key";
const POLL_INTERVAL = 1000;

export default function Home() {
  const [apiKey, setApiKey] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) setApiKey(stored);
  }, []);

  function handleApiKeyChange(value: string) {
    setApiKey(value);
    sessionStorage.setItem(SESSION_KEY, value);
  }

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollStatus = useCallback(
    (id: string) => {
      pollRef.current = setInterval(async () => {
        try {
          const resp = await fetch(`/api/status/${id}`);
          if (!resp.ok) return;
          const data = await resp.json();

          setMessages(data.messages || []);

          if (data.status === "completed") {
            stopPolling();
            setIsGenerating(false);
            setIsComplete(true);
          } else if (data.status === "failed") {
            stopPolling();
            setIsGenerating(false);
            const errMsg = data.error?.startsWith("AUTH:")
              ? "Invalid API key. Please check and try again."
              : data.error || "Generation failed.";
            setError(errMsg);
          }
        } catch {
          // Network error — keep polling
        }
      }, POLL_INTERVAL);
    },
    [stopPolling]
  );

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  async function handleGenerate() {
    if (!file || !apiKey.trim()) return;

    // Reset state
    setJobId(null);
    setMessages([]);
    setError(null);
    setIsComplete(false);
    setIsGenerating(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const resp = await fetch("/api/convert", {
        method: "POST",
        headers: { "X-API-Key": apiKey },
        body: formData,
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        let errMsg = data.detail || "Failed to start conversion.";
        if (resp.status === 413) {
          errMsg = "File too large. Maximum size is 50 MB.";
        } else if (resp.status === 429) {
          errMsg = "Too many requests. Please try again in a minute.";
        } else if (resp.status === 503) {
          errMsg = "Server is busy. Please try again shortly.";
        }
        setError(errMsg);
        setIsGenerating(false);
        return;
      }

      const { job_id } = await resp.json();
      setJobId(job_id);
      setMessages(["Starting conversion..."]);
      pollStatus(job_id);
    } catch {
      setError("Network error. Is the backend running?");
      setIsGenerating(false);
    }
  }

  const canGenerate = apiKey.trim().length > 0 && file !== null && !isGenerating;

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-foreground">
          PaperToCode
        </h1>
        <p className="text-muted text-base sm:text-lg leading-relaxed">
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
        <GenerateButton
          disabled={!canGenerate}
          loading={isGenerating}
          onClick={handleGenerate}
        />
      </div>

      {(messages.length > 0 || error) && (
        <StatusFeed messages={messages} error={error} />
      )}

      {isComplete && jobId && (
        <DownloadSection visible={true} jobId={jobId} />
      )}
    </div>
  );
}
