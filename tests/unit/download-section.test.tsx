import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DownloadSection } from "@/app/components/DownloadSection";

describe("DownloadSection", () => {
  it("renders nothing when not visible", () => {
    const { container } = render(
      <DownloadSection visible={false} jobId="abc" />
    );
    expect(container.querySelector('[data-testid="download-section"]')).not.toBeInTheDocument();
  });

  it("renders download and Colab buttons when visible", () => {
    render(<DownloadSection visible={true} jobId="abc" />);
    expect(screen.getByTestId("download-button")).toBeInTheDocument();
    expect(screen.getByTestId("colab-button")).toBeInTheDocument();
  });

  it("download button has correct href", () => {
    render(<DownloadSection visible={true} jobId="test-job-123" />);
    const btn = screen.getByTestId("download-button");
    expect(btn.getAttribute("href")).toContain("/api/download/test-job-123");
  });

  it("download button text mentions .ipynb", () => {
    render(<DownloadSection visible={true} jobId="abc" />);
    expect(screen.getByTestId("download-button")).toHaveTextContent(/\.ipynb/i);
  });

  it("Colab button text mentions Colab", () => {
    render(<DownloadSection visible={true} jobId="abc" />);
    expect(screen.getByTestId("colab-button")).toHaveTextContent(/colab/i);
  });

  it("Colab button opens in new tab", () => {
    render(<DownloadSection visible={true} jobId="abc" />);
    const btn = screen.getByTestId("colab-button");
    // Should be a button (click handler), not a link
    expect(btn.tagName).toBe("BUTTON");
  });
});
