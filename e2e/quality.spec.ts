import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

const SCREENSHOT_DIR = path.resolve(__dirname, "../tests/screenshots");

// PDF path configurable via env var, with a sensible default
const TEST_PDF =
  process.env.QUALITY_TEST_PDF ||
  path.resolve(__dirname, "../NIPS-2017-attention-is-all-you-need-Paper.pdf");

// Timeout for the full generation (up to 5 minutes)
const GENERATION_TIMEOUT = 300_000;

test.describe("Quality test — real API, visible browser", () => {
  test.beforeAll(() => {
    if (!fs.existsSync(TEST_PDF)) {
      throw new Error(
        `Test PDF not found at: ${TEST_PDF}\n` +
          `Set QUALITY_TEST_PDF env var to the path of "Attention Is All You Need" PDF.`
      );
    }
  });

  test("full generation flow with notebook validation", async ({ page }) => {
    // Increase test timeout for real API calls
    test.setTimeout(GENERATION_TIMEOUT);

    // Step 1: Navigate to the app
    await page.goto("/");
    await expect(page.getByTestId("generate-button")).toBeVisible();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task3-01-initial-page.png`,
    });

    // Step 2: Prompt user to enter their OpenAI API key
    // Use page.pause() alternative — a dialog prompt
    const apiKey = await page.evaluate(() => {
      return window.prompt(
        "Enter your OpenAI API key for the quality test.\n" +
          "This key will be used to make a real API call to generate a notebook."
      );
    });

    if (!apiKey || !apiKey.trim()) {
      test.skip(true, "No API key provided — skipping quality test");
      return;
    }

    await page.getByTestId("api-key-input").fill(apiKey);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task3-02-api-key-entered.png`,
    });

    // Step 3: Upload the "Attention Is All You Need" PDF
    const fileInput = page.getByTestId("file-input");
    await fileInput.setInputFiles(TEST_PDF);
    await expect(page.getByTestId("upload-zone")).toContainText(".pdf", {
      ignoreCase: true,
    });
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task3-03-file-uploaded.png`,
    });

    // Step 4: Click Generate
    await expect(page.getByTestId("generate-button")).toBeEnabled();
    await page.getByTestId("generate-button").click();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task3-04-generating-started.png`,
    });

    // Step 5: Wait for status feed to appear
    await expect(page.getByTestId("status-feed")).toBeVisible({
      timeout: 10_000,
    });
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task3-05-status-feed-visible.png`,
    });

    // Step 6: Wait for completion — download section appears
    // This is the long wait (up to 5 minutes for real API call)
    await expect(page.getByTestId("download-section")).toBeVisible({
      timeout: GENERATION_TIMEOUT,
    });
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task3-06-generation-complete.png`,
    });

    // Step 7: Download and validate the notebook
    const downloadButton = page.getByTestId("download-button");
    await expect(downloadButton).toBeVisible();

    // Intercept the download
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      downloadButton.click(),
    ]);

    const downloadPath = path.resolve(
      SCREENSHOT_DIR,
      "task3-generated-notebook.ipynb"
    );
    await download.saveAs(downloadPath);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task3-07-notebook-downloaded.png`,
    });

    // Step 8: Validate the notebook
    const notebookContent = fs.readFileSync(downloadPath, "utf-8");

    // 8a: Valid JSON
    let notebook: {
      cells: Array<{
        cell_type: string;
        source: string | string[];
      }>;
    };
    try {
      notebook = JSON.parse(notebookContent);
    } catch {
      throw new Error("Downloaded notebook is not valid JSON");
    }

    // 8b: Has 8+ cells (sections)
    expect(notebook.cells.length).toBeGreaterThanOrEqual(8);

    // 8c: Contains valid Python code cells
    const codeCells = notebook.cells.filter((c) => c.cell_type === "code");
    expect(codeCells.length).toBeGreaterThan(0);

    // Verify code cells have non-empty source
    for (const cell of codeCells) {
      const source = Array.isArray(cell.source)
        ? cell.source.join("")
        : cell.source;
      expect(source.trim().length).toBeGreaterThan(0);
    }

    // 8d: Contains a safety/disclaimer cell
    const allText = notebook.cells
      .map((c) => {
        const src = Array.isArray(c.source)
          ? c.source.join("")
          : c.source;
        return src.toLowerCase();
      })
      .join("\n");

    const hasDisclaimer =
      allText.includes("disclaimer") ||
      allText.includes("safety") ||
      allText.includes("caution") ||
      allText.includes("warning") ||
      allText.includes("note:");

    expect(hasDisclaimer).toBeTruthy();

    // Summary log
    const markdownCells = notebook.cells.filter(
      (c) => c.cell_type === "markdown"
    );
    console.log(
      `\nNotebook validation passed:\n` +
        `  Total cells: ${notebook.cells.length}\n` +
        `  Code cells: ${codeCells.length}\n` +
        `  Markdown cells: ${markdownCells.length}\n` +
        `  Has disclaimer: ${hasDisclaimer}\n`
    );
  });
});
