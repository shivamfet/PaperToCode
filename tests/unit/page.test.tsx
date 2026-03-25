import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home page", () => {
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
});
