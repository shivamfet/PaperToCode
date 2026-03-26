"use client";

import { useRef, useState } from "react";

interface UploadZoneProps {
  file: File | null;
  onFile: (file: File) => void;
  onRemove: () => void;
}

export function UploadZone({ file, onFile, onRemove }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  function handleFileChange(files: FileList | null) {
    if (!files || files.length === 0) return;
    const selected = files[0];
    if (selected.type !== "application/pdf") return;
    onFile(selected);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    handleFileChange(e.dataTransfer.files);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(true);
  }

  function handleDragLeave() {
    setDragOver(false);
  }

  if (file) {
    return (
      <div
        data-testid="upload-zone"
        className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-accent text-lg shrink-0">PDF</span>
          <span className="text-foreground truncate">{file.name}</span>
          <span className="text-muted text-sm shrink-0">
            {(file.size / 1024).toFixed(0)} KB
          </span>
        </div>
        <button
          type="button"
          data-testid="remove-file"
          onClick={onRemove}
          className="text-muted hover:text-foreground transition-colors ml-2 shrink-0"
        >
          Remove
        </button>
      </div>
    );
  }

  return (
    <div
      data-testid="upload-zone"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => inputRef.current?.click()}
      className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 sm:px-6 py-8 sm:py-10 cursor-pointer transition-colors ${
        dragOver
          ? "border-accent bg-surface-hover"
          : "border-border hover:border-muted"
      }`}
    >
      <p className="text-muted text-center">
        Drag & drop a PDF here, or{" "}
        <span className="text-accent underline">browse</span>
      </p>
      <p className="text-muted text-sm mt-1">PDF files up to 50 MB</p>
      <input
        ref={inputRef}
        data-testid="file-input"
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => handleFileChange(e.target.files)}
      />
    </div>
  );
}
