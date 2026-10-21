/** Pure bounded presentation contracts by Jason Stys. Functions/fixtures: docs/CODE_INDEX.md. */
import { describe, expect, it } from "vitest";
import { defaults, display, escape, isReport, pixelColor, preferences } from "./contracts";
/** Minimal numerical service envelope for defensive UI shape validation, not a physical test oracle. */
function valid() {
  return {
    schema: 1,
    id: "a".repeat(64),
    name: "test",
    settings: { ...defaults },
    grid: {
      width: 1,
      height: 1,
      crs: "EPSG:32610",
      transform: [10, 0, 700000, 0, -10, 4000000],
      pixel_area_m2: 100,
    },
    provenance: {
      kind: "synthetic",
      attribution: "fixture",
      ground_truth: "known",
      scenes: [{ datetime: "2020-01-01" }, { datetime: "2020-01-02" }],
    },
    method: { reference_verified: true, index: "ratio" },
    summary: {
      pixels: 1,
      comparable: 1,
      candidate_pixels: 0,
      candidate_ha: 0,
      increase_pixels: 0,
      decrease_pixels: 0,
      filtered_pixels: 0,
      regions: 0,
      candidate_fraction: 0,
      mean_delta: 0,
    },
    quality: { comparable: 1 },
    truth: null,
    sensitivity: [
      { threshold: 0.15, raw_candidate_pixels: 0 },
      { threshold: 0.2, raw_candidate_pixels: 0 },
      { threshold: 0.25, raw_candidate_pixels: 0 },
    ],
    regions: [],
    pixels: {
      before_index: [0.5],
      after_index: [0.5],
      delta: [0],
      class: [1],
      region: [0],
      before_rgb: [0x112233],
      after_rgb: [0x445566],
    },
    limits: ["synthetic"],
  };
}
describe("honest presentation", () => {
  it("escapes HTML metacharacters", () =>
    expect(escape('<img a="x">&\'')).toBe("&lt;img a=&quot;x&quot;&gt;&amp;&#39;"));
  it("does not turn missing values into zero", () => {
    for (const v of [null, undefined, NaN, Infinity, "0"]) expect(display(v)).toBe("Not available");
    expect(display(0)).toBe("0.00");
  });
  it("roundtrips exact settings", () =>
    expect(preferences(JSON.stringify(defaults))).toEqual(defaults));
  it("rejects bad storage", () => {
    for (const v of [
      "{}",
      "null",
      "[]",
      "invalid",
      JSON.stringify({ ...defaults, margin: true }),
      JSON.stringify({ ...defaults, threshold: "20" }),
      JSON.stringify({ ...defaults, scenario: "__proto__" }),
      JSON.stringify({ ...defaults, other: 1 }),
    ])
      expect(preferences(v)).toBeNull();
  });
  it("accepts complete evidence", () => expect(isReport(valid())).toBe(true));
  it("rejects missing fields and impossible raster allocation", () => {
    expect(isReport(null)).toBe(false);
    expect(isReport({ schema: 1 })).toBe(false);
    expect(isReport({ ...valid(), grid: { ...valid().grid, width: 129 } })).toBe(false);
  });
  it("rejects wrong-length or nonfinite index arrays", () => {
    for (const values of [[NaN], [Infinity], [], [0.5, 0.5], [3]])
      expect(isReport({ ...valid(), pixels: { ...valid().pixels, delta: values } })).toBe(false);
  });
  it("retains explicit unknowns", () =>
    expect(
      isReport({
        ...valid(),
        pixels: { ...valid().pixels, delta: [null], class: [0] },
        summary: { ...valid().summary, candidate_fraction: null, mean_delta: null, comparable: 0 },
      }),
    ).toBe(true));
  it("requires verification and bounded colors", () => {
    expect(isReport({ ...valid(), method: { reference_verified: false } })).toBe(false);
    expect(isReport({ ...valid(), pixels: { ...valid().pixels, before_rgb: [0x1000000] } })).toBe(
      false,
    );
  });
  it("decodes packed colors without HTML or geometry interpolation", () =>
    expect(pixelColor(0x112233, 1, 0, 0, false)).toEqual([17, 34, 51, 255]));
  it("unknown is visually distinct from unchanged", () =>
    expect(pixelColor(0x112233, 0, 0, 0, false)).not.toEqual(pixelColor(0x112233, 1, 0, 0, false)));
  it("shows directional and filtered candidates explicitly", () => {
    expect(pixelColor(0, 2, 0, 0, true)).toEqual([12, 96, 134, 255]);
    expect(pixelColor(0, 3, 0, 0, true)).toEqual([157, 63, 47, 255]);
    expect(pixelColor(0, 4, 0, 0, true)).toEqual([180, 141, 42, 255]);
  });
});
