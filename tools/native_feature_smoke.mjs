/**
 * Frozen geospatial region/context acceptance by Jason Stys.
 * Function: runNativeJourney callback; variables: known rectangle, fringe and actual GeoJSON.
 * Uses owned synthetic pixels, not live imagery or identifying surveillance.
 * Symbol locations: docs/CODE_INDEX.md.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { expect } from "@playwright/test";
import { runNativeJourney } from "./native_browser.mjs";

await runNativeJourney(async ({ page, request }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("vegetation-loss");
  await expect(page.locator("#truth")).toContainText("IoU 1.000");
  await page.locator("#region").selectOption("1");
  await expect(page.locator("#region-info")).toContainText("Four-neighbor context");
  await expect(page.locator("#region-info")).toContainText("not a confirmed environmental cause");
  const response = await request.get("/api/run?scenario=vegetation-loss");
  assert.equal(response.status(), 200);
  const report = await response.json();
  const region = report.regions[0];
  assert.equal(report.regions.length, 1);
  assert.equal(region.pixels, 192);
  const [top, left, bottom, right] = region.bbox_rc;
  assert.equal((bottom - top) * (right - left), 192);
  // A standalone filled rectangle has two exterior neighbors per row and column.
  assert.equal(region.context.neighbor_pixels, 2 * (bottom - top + right - left));
  assert.equal(region.context.excluded_neighbors, 0);
  assert.equal(region.context.crop_edge_sides, 0);
  assert.equal(region.context.complete_four_neighbor_context, true);
  const pending = page.waitForEvent("download");
  await page.getByRole("link", { name: "GEOJSON ↓", exact: true }).click();
  const downloaded = await pending;
  const geojson = JSON.parse(await readFile(await downloaded.path(), "utf8"));
  assert.equal(geojson.features.length, 1);
  assert.deepEqual(geojson.features[0].properties.context, region.context);
});
