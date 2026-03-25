import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

describe("ARC-inspired theme setup", () => {
  const globalsCss = fs.readFileSync(
    path.resolve(__dirname, "../../app/globals.css"),
    "utf-8"
  );

  it("sets dark background color #0a0a0a", () => {
    expect(globalsCss).toContain("#0a0a0a");
  });

  it("sets light foreground text color", () => {
    expect(globalsCss).toContain("--foreground");
    expect(globalsCss).toContain("#e5e5e5");
  });

  it("includes Tailwind directives", () => {
    expect(globalsCss).toContain("@tailwind base");
    expect(globalsCss).toContain("@tailwind components");
    expect(globalsCss).toContain("@tailwind utilities");
  });

  it("sets Inter font family", () => {
    expect(globalsCss).toContain("Inter");
  });

  it("defines CSS variables for the theme palette", () => {
    expect(globalsCss).toContain("--accent");
    expect(globalsCss).toContain("--muted");
    expect(globalsCss).toContain("--surface");
    expect(globalsCss).toContain("--border");
  });
});

describe("Tailwind config", () => {
  it("tailwind.config.ts exists", () => {
    const exists = fs.existsSync(
      path.resolve(__dirname, "../../tailwind.config.ts")
    );
    expect(exists).toBe(true);
  });
});

describe("Layout", () => {
  const layout = fs.readFileSync(
    path.resolve(__dirname, "../../app/layout.tsx"),
    "utf-8"
  );

  it("has centered single-column structure", () => {
    expect(layout).toContain("max-w-2xl");
    expect(layout).toContain("items-center");
  });

  it("imports globals.css", () => {
    expect(layout).toContain("./globals.css");
  });
});
