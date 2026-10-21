/** Actual service/browser environmental review acceptance by Jason Stys; index: docs/CODE_INDEX.md.
 * Only explicit failure/hostile-response regressions mock HTTP; scientific checks use real Rasterio.
 */
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";

test("SCL selector survives report rendering and all element IDs are unique", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await expect(page.locator("#quality option")).toHaveCount(2);
  await page.locator("#quality").selectOption("unclassified");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#quality")).toHaveValue("unclassified");
  await expect(page.locator("#quality option")).toHaveCount(2);
  const duplicate = await page.locator("[id]").evaluateAll((nodes) => {
    const ids = nodes.map((n) => n.id);
    return ids.filter((id, index) => ids.indexOf(id) !== index);
  });
  expect(duplicate).toEqual([]);
});

test("public imagery provenance and genuine raster view", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await expect(page.locator("#status")).toContainText("vector and scalar indices agree");
  await expect(page.locator("#evidence")).toContainText(
    "Contains modified Copernicus Sentinel data (2020)",
  );
  await expect(page.locator("#truth")).toContainText("no independent ground truth");
  await page.locator("#layer").selectOption("change");
  await page.locator("#zoom").selectOption("2");
  await page.locator("#row").fill("64");
  await page.locator("#row").press("Tab");
  await expect(page.locator("#pixel-info")).toContainText("Cell centre");
  await page.getByRole("img", { name: /Aligned environmental imagery/ }).isVisible();
});
test("known-answer rectangle and meaningful human review", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("vegetation-loss");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#truth")).toContainText("IoU 1.000");
  await page.locator("#region").selectOption("1");
  await page.locator("#decision").selectOption("needs-context");
  await page.locator("#note").fill("Check seasonality before assigning cause.");
  await page.getByRole("button", { name: "Record in this tab", exact: true }).click();
  await expect(page.locator("#review-status")).toContainText("1 local reviews");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download review JSON", exact: true }).click();
  const saved = await download;
  const result = JSON.parse(await readFile((await saved.path())!, "utf8"));
  expect(result.regions[0].decision).toBe("needs-context");
  expect(result.report_id).toMatch(/^[a-f0-9]{64}$/);
  await page.locator("#threshold").selectOption("30");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#review-status")).toContainText("0 local reviews");
});
test("no comparable pixels are not an observed zero-change rate", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("all-masked");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator(".metrics")).toContainText("No comparable pixels");
  await expect(page.locator("#truth")).toContainText("Not available");
  await expect(page.locator("#pixel-info")).toContainText("EXCLUDED / NOT COMPARABLE");
});
test("cloud trap and water index follow supported controls", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("cloud-trap");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator(".metrics article").nth(1).locator("strong")).toHaveText("0");
  await page.locator("#scenario").selectOption("water-gain");
  await page.locator("#metric").selectOption("ndwi");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#region")).toContainText("increase");
  await expect(page.locator(".metrics article").nth(1).locator("strong")).toHaveText("192");
});
test("all export formats preserve real geospatial evidence", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("vegetation-loss");
  await expect(page.locator("#status")).toContainText("Verified");
  for (const name of ["JSON ↓", "CSV ↓", "HTML ↓", "GEOJSON ↓", "GeoTIFF ↓"]) {
    const href = await page.getByRole("link", { name, exact: true }).getAttribute("href");
    const response = await request.get(href!);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-disposition"]).toContain("attachment");
    if (name === "JSON ↓") expect((await response.json()).summary.candidate_pixels).toBe(192);
    if (name === "CSV ↓") expect(await response.text()).toContain("easting_m");
    if (name === "HTML ↓") expect(await response.text()).not.toContain("<script");
    if (name === "GEOJSON ↓")
      expect((await response.json()).features[0].properties.pixels).toBe(192);
    if (name === "GeoTIFF ↓") {
      expect(response.headers()["content-type"]).toBe("image/tiff");
      expect((await response.body()).subarray(0, 2).toString()).toBe("II");
    }
  }
});
test("preferences are opt-in and erase cleanly", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("fieldnote-controls-v1"))).toBeNull();
  await page.locator("#scenario").selectOption("no-change");
  await expect(page.locator("#status")).toContainText("Verified");
  await page.getByLabel("Remember controls on this device").check();
  await page.reload();
  await expect(page.locator("#scenario")).toHaveValue("no-change");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.getByLabel("Remember controls on this device").uncheck();
  expect(await page.evaluate(() => localStorage.getItem("fieldnote-controls-v1"))).toBeNull();
});
test("failure hides stale evidence and retries without fabricated pixels", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.route("**/api/run?**", (r) => r.fulfill({ status: 500, body: "unavailable" }));
  await page.getByRole("button", { name: "Compare dates ↗" }).click();
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  await expect(page.locator("#evidence")).toBeHidden();
  await page.unroute("**/api/run?**");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.locator("#evidence")).toBeVisible();
  await page.route("**/api/run?**", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: '{"schema":1}' }),
  );
  await page.getByRole("button", { name: "Compare dates ↗" }).click();
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});
test("hostile labels never become markup", async ({ page }) => {
  await page.route("**/api/run?**", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.provenance.attribution = '<img src=x onerror="alert(1)">';
    await route.fulfill({ response, json: body });
  });
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await expect(page.locator(".attribution")).toContainText("<img");
  await expect(page.locator("#evidence img,#evidence script")).toHaveCount(0);
});
test("mobile layout keyboard inspector and accessibility", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  const size = await page.evaluate(() => ({
    width: innerWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(size.scroll).toBeLessThanOrEqual(size.width + 1);
  await page.getByRole("region", { name: "Scrollable environmental imagery", exact: true }).focus();
  await expect(
    page.getByRole("region", { name: "Scrollable environmental imagery", exact: true }),
  ).toBeFocused();
  await page.locator("#column").fill("12");
  await page.locator("#column").press("Tab");
  await expect(page.locator("#column")).toHaveValue("12");
  expect(
    (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
      .violations,
  ).toEqual([]);
});
