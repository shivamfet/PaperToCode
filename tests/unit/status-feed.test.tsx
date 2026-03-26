import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusFeed } from "@/app/components/StatusFeed";

describe("StatusFeed", () => {
  it("renders nothing when messages array is empty", () => {
    const { container } = render(<StatusFeed messages={[]} />);
    expect(container.querySelector('[data-testid="status-feed"]')).toBeInTheDocument();
  });

  it("renders all messages", () => {
    const messages = [
      "Extracting text from PDF...",
      "Extracted text from 12 pages.",
      "Analyzing paper with GPT-5.4...",
    ];
    render(<StatusFeed messages={messages} />);
    for (const msg of messages) {
      expect(screen.getByText(msg)).toBeInTheDocument();
    }
  });

  it("displays messages in order", () => {
    const messages = ["First message", "Second message", "Third message"];
    render(<StatusFeed messages={messages} />);
    const items = screen.getAllByTestId("status-message");
    expect(items[0]).toHaveTextContent("First message");
    expect(items[1]).toHaveTextContent("Second message");
    expect(items[2]).toHaveTextContent("Third message");
  });

  it("has terminal-like styling with monospace font", () => {
    render(<StatusFeed messages={["test"]} />);
    const feed = screen.getByTestId("status-feed");
    expect(feed.className).toMatch(/font-mono/);
  });

  it("shows error state when error is provided", () => {
    render(<StatusFeed messages={["step 1"]} error="Something went wrong" />);
    expect(screen.getByTestId("status-error")).toHaveTextContent("Something went wrong");
  });

  it("does not show error element when no error", () => {
    render(<StatusFeed messages={["step 1"]} />);
    expect(screen.queryByTestId("status-error")).not.toBeInTheDocument();
  });
});
