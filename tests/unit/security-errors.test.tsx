import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Home from "@/app/page";

function setupFileAndKey() {
  render(<Home />);

  // Set API key
  const keyInput = screen.getByTestId("api-key-input");
  fireEvent.change(keyInput, { target: { value: "sk-test-key" } });

  // Upload a file
  const fileInput = screen.getByTestId("file-input");
  const file = new File(["fake pdf"], "paper.pdf", { type: "application/pdf" });
  fireEvent.change(fileInput, { target: { files: [file] } });

  return { keyInput, fileInput };
}

describe("Security Error Handling", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  describe("413 — File too large", () => {
    it("shows file too large error message", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
        ok: false,
        status: 413,
        json: async () => ({ detail: "File too large. Maximum size is 50 MB." }),
      } as Response);

      setupFileAndKey();
      fireEvent.click(screen.getByTestId("generate-button"));

      await waitFor(() => {
        expect(screen.getByTestId("status-error")).toHaveTextContent(
          "File too large. Maximum size is 50 MB."
        );
      });
    });
  });

  describe("429 — Rate limited", () => {
    it("shows rate limit error with retry message", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({ detail: "Rate limit exceeded" }),
      } as Response);

      setupFileAndKey();
      fireEvent.click(screen.getByTestId("generate-button"));

      await waitFor(() => {
        expect(screen.getByTestId("status-error")).toHaveTextContent(
          "Too many requests. Please try again in a minute."
        );
      });
    });
  });

  describe("503 — Server busy", () => {
    it("shows server busy error message", async () => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: async () => ({
          detail: "Server busy. Maximum job limit (100) reached.",
        }),
      } as Response);

      setupFileAndKey();
      fireEvent.click(screen.getByTestId("generate-button"));

      await waitFor(() => {
        expect(screen.getByTestId("status-error")).toHaveTextContent(
          "Server is busy. Please try again shortly."
        );
      });
    });
  });
});
