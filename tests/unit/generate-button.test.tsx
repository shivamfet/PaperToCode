import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GenerateButton } from "@/app/components/GenerateButton";

describe("GenerateButton", () => {
  it("renders the generate button", () => {
    render(<GenerateButton disabled={false} onClick={vi.fn()} />);
    expect(screen.getByTestId("generate-button")).toBeInTheDocument();
    expect(screen.getByText(/generate notebook/i)).toBeInTheDocument();
  });

  it("is disabled when disabled prop is true", () => {
    render(<GenerateButton disabled={true} onClick={vi.fn()} />);
    expect(screen.getByTestId("generate-button")).toBeDisabled();
  });

  it("is enabled when disabled prop is false", () => {
    render(<GenerateButton disabled={false} onClick={vi.fn()} />);
    expect(screen.getByTestId("generate-button")).not.toBeDisabled();
  });

  it("calls onClick when clicked and enabled", () => {
    const mockClick = vi.fn();
    render(<GenerateButton disabled={false} onClick={mockClick} />);
    fireEvent.click(screen.getByTestId("generate-button"));
    expect(mockClick).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick when clicked and disabled", () => {
    const mockClick = vi.fn();
    render(<GenerateButton disabled={true} onClick={mockClick} />);
    fireEvent.click(screen.getByTestId("generate-button"));
    expect(mockClick).not.toHaveBeenCalled();
  });
});
