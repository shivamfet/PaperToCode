import { test, expect } from "vitest";
import fs from "fs";
import path from "path";
import { parse } from "yaml";

const CI_PATH = path.resolve(
  __dirname,
  "../../.github/workflows/ci.yml"
);

test("ci.yml exists", () => {
  expect(fs.existsSync(CI_PATH)).toBe(true);
});

test("ci.yml is valid YAML with required structure", () => {
  const content = fs.readFileSync(CI_PATH, "utf-8");
  const ci = parse(content);

  // Triggers on push and pull_request to main
  expect(ci.on.push.branches).toContain("main");
  expect(ci.on.pull_request.branches).toContain("main");

  // Has all 4 required jobs
  const jobNames = Object.keys(ci.jobs);
  expect(jobNames).toContain("backend-tests");
  expect(jobNames).toContain("frontend-tests");
  expect(jobNames).toContain("security-scan");
  expect(jobNames).toContain("dependency-audit");
});

test("backend-tests job installs Python deps and runs pytest", () => {
  const content = fs.readFileSync(CI_PATH, "utf-8");
  const ci = parse(content);
  const job = ci.jobs["backend-tests"];

  // Runs on ubuntu
  expect(job["runs-on"]).toMatch(/ubuntu/);

  // Has steps that reference Python setup and pytest
  const stepTexts = job.steps.map((s: { run?: string; uses?: string; name?: string }) =>
    `${s.run || ""} ${s.uses || ""} ${s.name || ""}`
  ).join("\n");

  expect(stepTexts).toMatch(/python/i);
  expect(stepTexts).toMatch(/pytest/i);
  expect(stepTexts).toMatch(/requirements/i);
});

test("frontend-tests job installs Node deps and runs Playwright", () => {
  const content = fs.readFileSync(CI_PATH, "utf-8");
  const ci = parse(content);
  const job = ci.jobs["frontend-tests"];

  expect(job["runs-on"]).toMatch(/ubuntu/);

  const stepTexts = job.steps.map((s: { run?: string; uses?: string; name?: string }) =>
    `${s.run || ""} ${s.uses || ""} ${s.name || ""}`
  ).join("\n");

  expect(stepTexts).toMatch(/node/i);
  expect(stepTexts).toMatch(/playwright/i);
});

test("security-scan job runs semgrep on backend", () => {
  const content = fs.readFileSync(CI_PATH, "utf-8");
  const ci = parse(content);
  const job = ci.jobs["security-scan"];

  const stepTexts = job.steps.map((s: { run?: string; uses?: string; name?: string }) =>
    `${s.run || ""} ${s.uses || ""} ${s.name || ""}`
  ).join("\n");

  expect(stepTexts).toMatch(/semgrep/i);
  expect(stepTexts).toMatch(/backend/i);
});

test("dependency-audit job runs pip-audit", () => {
  const content = fs.readFileSync(CI_PATH, "utf-8");
  const ci = parse(content);
  const job = ci.jobs["dependency-audit"];

  const stepTexts = job.steps.map((s: { run?: string; uses?: string; name?: string }) =>
    `${s.run || ""} ${s.uses || ""} ${s.name || ""}`
  ).join("\n");

  expect(stepTexts).toMatch(/pip-audit/i);
  expect(stepTexts).toMatch(/requirements/i);
});
