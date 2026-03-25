import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ApiKeyInput } from "@/app/components/ApiKeyInput";

describe("ApiKeyInput", () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
    sessionStorage.clear();
  });

  it("renders an input for the API key", () => {
    render(<ApiKeyInput value="" onChange={mockOnChange} />);
    expect(screen.getByTestId("api-key-input")).toBeInTheDocument();
  });

  it("renders with password type by default (hidden)", () => {
    render(<ApiKeyInput value="sk-test-123" onChange={mockOnChange} />);
    const input = screen.getByTestId("api-key-input");
    expect(input).toHaveAttribute("type", "password");
  });

  it("toggles visibility when show/hide button is clicked", () => {
    render(<ApiKeyInput value="sk-test-123" onChange={mockOnChange} />);
    const toggleBtn = screen.getByTestId("api-key-toggle");
    const input = screen.getByTestId("api-key-input");

    fireEvent.click(toggleBtn);
    expect(input).toHaveAttribute("type", "text");

    fireEvent.click(toggleBtn);
    expect(input).toHaveAttribute("type", "password");
  });

  it("calls onChange when user types", () => {
    render(<ApiKeyInput value="" onChange={mockOnChange} />);
    const input = screen.getByTestId("api-key-input");
    fireEvent.change(input, { target: { value: "sk-new-key" } });
    expect(mockOnChange).toHaveBeenCalledWith("sk-new-key");
  });

  it("displays the provided value", () => {
    render(<ApiKeyInput value="sk-existing" onChange={mockOnChange} />);
    const input = screen.getByTestId("api-key-input");
    expect(input).toHaveValue("sk-existing");
  });

  it("has a placeholder text", () => {
    render(<ApiKeyInput value="" onChange={mockOnChange} />);
    const input = screen.getByTestId("api-key-input");
    expect(input).toHaveAttribute("placeholder");
  });
});
