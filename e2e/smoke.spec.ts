import { test, expect } from "@playwright/test";

test.describe("Smoke tests", () => {
  test("homepage loads with correct title and key elements", async ({ page }) => {
    await page.goto("/");

    // Verify the page title
    await expect(page).toHaveTitle(/PaperToCode/i);

    // Verify key UI elements are present
    await expect(page.getByTestId("api-key-input")).toBeVisible();
    await expect(page.getByTestId("upload-zone")).toBeVisible();
    await expect(page.getByTestId("generate-button")).toBeVisible();

    // Verify the heading text
    await expect(page.getByRole("heading", { name: /PaperToCode/i })).toBeVisible();

    // Generate button should be disabled initially (no API key, no file)
    await expect(page.getByTestId("generate-button")).toBeDisabled();
  });

  test("backend health endpoint is reachable", async ({ request }) => {
    const response = await request.get("http://localhost:8000/health");
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body.status).toBe("ok");
  });
});
