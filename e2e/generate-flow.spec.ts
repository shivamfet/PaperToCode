import { test, expect } from "@playwright/test";
import path from "path";

const TEST_PDF = path.resolve(__dirname, "fixtures/test-paper.pdf");
const SCREENSHOT_DIR = path.resolve(__dirname, "../tests/screenshots");

// Mock job responses for simulating the backend pipeline
const MOCK_JOB_ID = "test-job-123";

function mockConvertSuccess(page: import("@playwright/test").Page) {
  return page.route("**/api/convert", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ job_id: MOCK_JOB_ID }),
    });
  });
}

function mockStatusSequence(page: import("@playwright/test").Page) {
  let callCount = 0;
  const statusResponses = [
    {
      job_id: MOCK_JOB_ID,
      status: "processing",
      messages: ["Extracting text from PDF..."],
      error: null,
    },
    {
      job_id: MOCK_JOB_ID,
      status: "processing",
      messages: [
        "Extracting text from PDF...",
        "Extracted text from 15 pages.",
        "Analyzing paper with GPT-5.4...",
      ],
      error: null,
    },
    {
      job_id: MOCK_JOB_ID,
      status: "completed",
      messages: [
        "Extracting text from PDF...",
        "Extracted text from 15 pages.",
        "Analyzing paper with GPT-5.4...",
        "Identified 3 algorithms to implement.",
        "Building research notebook...",
        "Notebook ready — 12 cells, 6 code blocks.",
      ],
      error: null,
    },
  ];

  return page.route(`**/api/status/${MOCK_JOB_ID}`, async (route) => {
    const response = statusResponses[Math.min(callCount, statusResponses.length - 1)];
    callCount++;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });
}

function mockDownload(page: import("@playwright/test").Page) {
  return page.route(`**/api/download/${MOCK_JOB_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/octet-stream",
      headers: {
        "Content-Disposition": 'attachment; filename="notebook.ipynb"',
      },
      body: JSON.stringify({
        nbformat: 4,
        nbformat_minor: 5,
        metadata: {},
        cells: [{ cell_type: "code", source: "print('hello')", metadata: {}, outputs: [] }],
      }),
    });
  });
}

test.describe("Generate flow — full user journey", () => {
  test("happy path: API key → upload PDF → generate → status → download", async ({
    page,
  }) => {
    // Setup mocks
    await mockConvertSuccess(page);
    await mockStatusSequence(page);
    await mockDownload(page);

    // Step 1: Load the page
    await page.goto("/");
    await expect(page.getByTestId("generate-button")).toBeDisabled();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-01-initial-page.png`,
    });

    // Step 2: Enter API key
    await page.getByTestId("api-key-input").fill("sk-test-key-1234567890");
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-02-api-key-entered.png`,
    });

    // Step 3: Upload PDF
    const fileInput = page.getByTestId("file-input");
    await fileInput.setInputFiles(TEST_PDF);
    await expect(page.getByTestId("upload-zone")).toContainText("test-paper.pdf");
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-03-file-uploaded.png`,
    });

    // Step 4: Generate button should be enabled
    await expect(page.getByTestId("generate-button")).toBeEnabled();

    // Step 5: Click Generate
    await page.getByTestId("generate-button").click();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-04-generating.png`,
    });

    // Step 6: Wait for status feed to appear with messages
    await expect(page.getByTestId("status-feed")).toBeVisible({ timeout: 5000 });
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-05-status-messages.png`,
    });

    // Step 7: Wait for completion — download section appears
    await expect(page.getByTestId("download-section")).toBeVisible({ timeout: 10000 });
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-06-complete-with-download.png`,
    });

    // Verify final status messages
    const statusMessages = page.getByTestId("status-message");
    await expect(statusMessages).toHaveCount(6);
    await expect(statusMessages.first()).toContainText("Extracting text from PDF");
    await expect(statusMessages.last()).toContainText("Notebook ready");

    // Verify download button is present
    await expect(page.getByTestId("download-button")).toBeVisible();
    await expect(page.getByTestId("colab-button")).toBeVisible();
  });

  test("error path: missing API key shows generate disabled", async ({ page }) => {
    await page.goto("/");

    // Upload a file without entering API key
    const fileInput = page.getByTestId("file-input");
    await fileInput.setInputFiles(TEST_PDF);
    await expect(page.getByTestId("upload-zone")).toContainText("test-paper.pdf");

    // Generate button should remain disabled (no API key)
    await expect(page.getByTestId("generate-button")).toBeDisabled();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-07-no-api-key-disabled.png`,
    });
  });

  test("error path: invalid file type is rejected by upload zone", async ({ page }) => {
    await page.goto("/");

    // Enter API key
    await page.getByTestId("api-key-input").fill("sk-test-key-1234567890");

    // Try uploading a non-PDF file — the input has accept="application/pdf"
    // and the component checks file.type !== "application/pdf"
    // Playwright setInputFiles with a .txt file won't match the accept attribute
    const txtFile = path.resolve(__dirname, "fixtures/not-a-pdf.txt");
    // Create the text file inline
    const fs = await import("fs");
    fs.writeFileSync(txtFile, "This is not a PDF file");

    await page.getByTestId("file-input").setInputFiles(txtFile);

    // The file should NOT be accepted — upload zone should still show the drop prompt
    await expect(page.getByTestId("upload-zone")).toContainText("Drag & drop");

    // Generate button should remain disabled
    await expect(page.getByTestId("generate-button")).toBeDisabled();
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-08-invalid-file-rejected.png`,
    });

    // Cleanup
    fs.unlinkSync(txtFile);
  });

  test("error path: backend returns 401 for missing API key header", async ({ page }) => {
    // Mock convert to return 401
    await page.route("**/api/convert", async (route) => {
      await route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "Missing API key. Provide it via the X-API-Key header.",
        }),
      });
    });

    await page.goto("/");
    await page.getByTestId("api-key-input").fill("sk-invalid-key");
    await page.getByTestId("file-input").setInputFiles(TEST_PDF);
    await page.getByTestId("generate-button").click();

    // Should show error in status feed
    await expect(page.getByTestId("status-error")).toBeVisible({ timeout: 5000 });
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-09-api-error.png`,
    });
  });

  test("error path: backend returns 429 rate limit", async ({ page }) => {
    await page.route("**/api/convert", async (route) => {
      await route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Rate limit exceeded" }),
      });
    });

    await page.goto("/");
    await page.getByTestId("api-key-input").fill("sk-test-key");
    await page.getByTestId("file-input").setInputFiles(TEST_PDF);
    await page.getByTestId("generate-button").click();

    await expect(page.getByTestId("status-error")).toBeVisible({ timeout: 5000 });
    await expect(page.getByTestId("status-error")).toContainText("Too many requests");
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/task2-10-rate-limited.png`,
    });
  });
});
