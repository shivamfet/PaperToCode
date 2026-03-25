import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Home from "@/app/page";

describe("Home page", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("renders the PaperToCode heading", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /papertocode/i })
    ).toBeInTheDocument();
  });

  it("renders the description text", () => {
    render(<Home />);
    const matches = screen.getAllByText(/upload a research paper/i);
    expect(matches.length).toBeGreaterThan(0);
  });

  it("renders all three main components", () => {
    render(<Home />);
    expect(screen.getByTestId("api-key-input")).toBeInTheDocument();
    expect(screen.getByTestId("upload-zone")).toBeInTheDocument();
    expect(screen.getByTestId("generate-button")).toBeInTheDocument();
  });

  it("has generate button disabled when both fields are empty", () => {
    render(<Home />);
    expect(screen.getByTestId("generate-button")).toBeDisabled();
  });

  it("has generate button disabled when only API key is filled", () => {
    render(<Home />);
    fireEvent.change(screen.getByTestId("api-key-input"), {
      target: { value: "sk-test-key" },
    });
    expect(screen.getByTestId("generate-button")).toBeDisabled();
  });

  it("enables generate button when both API key and file are provided", () => {
    render(<Home />);
    fireEvent.change(screen.getByTestId("api-key-input"), {
      target: { value: "sk-test-key" },
    });
    const fileInput = screen.getByTestId("file-input");
    const pdfFile = new File(["dummy"], "paper.pdf", { type: "application/pdf" });
    fireEvent.change(fileInput, { target: { files: [pdfFile] } });
    expect(screen.getByTestId("generate-button")).not.toBeDisabled();
  });

  it("persists API key to sessionStorage", () => {
    render(<Home />);
    fireEvent.change(screen.getByTestId("api-key-input"), {
      target: { value: "sk-stored-key" },
    });
    expect(sessionStorage.getItem("openai_api_key")).toBe("sk-stored-key");
  });

  it("restores API key from sessionStorage on mount", () => {
    sessionStorage.setItem("openai_api_key", "sk-restored-key");
    render(<Home />);
    expect(screen.getByTestId("api-key-input")).toHaveValue("sk-restored-key");
  });
});
