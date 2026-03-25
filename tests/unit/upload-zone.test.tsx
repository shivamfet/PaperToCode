import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { UploadZone } from "@/app/components/UploadZone";

describe("UploadZone", () => {
  const mockOnFile = vi.fn();
  const mockOnRemove = vi.fn();

  beforeEach(() => {
    mockOnFile.mockClear();
    mockOnRemove.mockClear();
  });

  it("renders the drop zone when no file is selected", () => {
    render(<UploadZone file={null} onFile={mockOnFile} onRemove={mockOnRemove} />);
    expect(screen.getByTestId("upload-zone")).toBeInTheDocument();
    expect(screen.getByText(/drag.*drop.*pdf/i)).toBeInTheDocument();
  });

  it("accepts PDF files via file input", () => {
    render(<UploadZone file={null} onFile={mockOnFile} onRemove={mockOnRemove} />);
    const input = screen.getByTestId("file-input");
    expect(input).toHaveAttribute("accept", "application/pdf");
  });

  it("calls onFile when a file is selected via input", () => {
    render(<UploadZone file={null} onFile={mockOnFile} onRemove={mockOnRemove} />);
    const input = screen.getByTestId("file-input");
    const pdfFile = new File(["dummy"], "paper.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [pdfFile] } });
    expect(mockOnFile).toHaveBeenCalledWith(pdfFile);
  });

  it("shows file preview when a file is selected", () => {
    const pdfFile = new File(["dummy"], "research-paper.pdf", { type: "application/pdf" });
    render(<UploadZone file={pdfFile} onFile={mockOnFile} onRemove={mockOnRemove} />);
    expect(screen.getByText("research-paper.pdf")).toBeInTheDocument();
  });

  it("shows a remove button when a file is selected", () => {
    const pdfFile = new File(["dummy"], "paper.pdf", { type: "application/pdf" });
    render(<UploadZone file={pdfFile} onFile={mockOnFile} onRemove={mockOnRemove} />);
    const removeBtn = screen.getByTestId("remove-file");
    expect(removeBtn).toBeInTheDocument();
  });

  it("calls onRemove when remove button is clicked", () => {
    const pdfFile = new File(["dummy"], "paper.pdf", { type: "application/pdf" });
    render(<UploadZone file={pdfFile} onFile={mockOnFile} onRemove={mockOnRemove} />);
    fireEvent.click(screen.getByTestId("remove-file"));
    expect(mockOnRemove).toHaveBeenCalled();
  });

  it("rejects non-PDF files", () => {
    render(<UploadZone file={null} onFile={mockOnFile} onRemove={mockOnRemove} />);
    const input = screen.getByTestId("file-input");
    const txtFile = new File(["dummy"], "paper.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [txtFile] } });
    expect(mockOnFile).not.toHaveBeenCalled();
  });
});
