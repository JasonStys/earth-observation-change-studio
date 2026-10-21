/** Finite environmental evidence presentation by Jason Stys.
 * Types/functions: Settings, Report, preferences, isReport, escape, display. Exact lines: docs/CODE_INDEX.md.
 */
export const cases = {
  "central-valley": "Central Valley / Sentinel-2",
  "vegetation-loss": "Synthetic vegetation loss",
  "water-gain": "Synthetic water expansion",
  "cloud-trap": "Cloud and shadow trap",
  "shifted-grid": "Shifted grid / unchanged",
  "no-change": "Unchanged control",
  "all-masked": "No comparable pixels",
  "denominator-zero": "Zero denominator",
};
export const choices = {
  metric: ["ndvi", "ndwi"],
  threshold: [10, 20, 30],
  margin: [0, 1, 2],
  minimum: [1, 4, 16],
  quality: ["strict", "unclassified"],
};
export interface Settings {
  scenario: string;
  metric: string;
  threshold: number;
  margin: number;
  minimum: number;
  quality: string;
}
export const defaults: Settings = {
  scenario: "central-valley",
  metric: "ndvi",
  threshold: 20,
  margin: 1,
  minimum: 4,
  quality: "strict",
};
export interface Region {
  id: number;
  direction: string;
  pixels: number;
  bbox_rc: number[];
  review: string;
}
export interface Report {
  schema: 1;
  id: string;
  name: string;
  settings: Settings;
  grid: { width: number; height: number; crs: string; transform: number[]; pixel_area_m2: number };
  provenance: {
    kind: string;
    attribution: string;
    ground_truth: string;
    scenes: { datetime: string }[];
  };
  method: { reference_verified: boolean; index: string };
  summary: Record<string, number | null>;
  quality: Record<string, number>;
  truth: null | Record<string, number | string | null>;
  sensitivity: { threshold: number; raw_candidate_pixels: number }[];
  regions: Region[];
  pixels: {
    before_index: (number | null)[];
    after_index: (number | null)[];
    delta: (number | null)[];
    class: number[];
    region: number[];
    before_rgb: number[];
    after_rgb: number[];
  };
  limits: string[];
}
/** Escape every external label/attribute rather than interpolating untrusted HTML. */
export function escape(value: unknown): string {
  return String(value).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!,
  );
}
/** Missing/undefined numerical evidence stays unavailable, never becomes a zero measurement. */
export function display(value: unknown, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toFixed(digits)
    : "Not available";
}
/** Recover opt-in finite preferences without type coercion, extra fields or inherited keys. */
export function preferences(text: string | null): Settings | null {
  try {
    const r = JSON.parse(text ?? "null") as Record<string, unknown>;
    if (
      !r ||
      typeof r !== "object" ||
      Object.keys(r).sort().join() !== Object.keys(defaults).sort().join() ||
      typeof r.scenario !== "string" ||
      !Object.hasOwn(cases, r.scenario)
    )
      return null;
    for (const k of ["metric", "threshold", "margin", "minimum", "quality"] as const)
      if (!(choices[k] as readonly unknown[]).includes(r[k])) return null;
    return r as unknown as Settings;
  } catch {
    return null;
  }
}
/** Validate bounded service data before allocating canvas buffers or rendering labels. */
export function isReport(value: unknown): value is Report {
  if (!value || typeof value !== "object") return false;
  const r = value as Report;
  const finite = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
  if (
    r.schema !== 1 ||
    typeof r.id !== "string" ||
    !/^[a-f0-9]{64}$/.test(r.id) ||
    typeof r.name !== "string" ||
    r.name.length > 128 ||
    !preferences(JSON.stringify(r.settings)) ||
    !r.grid ||
    ![r.grid.width, r.grid.height].every((v) => Number.isInteger(v) && v >= 1 && v <= 128) ||
    !Array.isArray(r.grid.transform) ||
    r.grid.transform.length !== 6 ||
    !r.grid.transform.every(finite) ||
    typeof r.grid.crs !== "string" ||
    !finite(r.grid.pixel_area_m2) ||
    !r.provenance ||
    typeof r.provenance.kind !== "string" ||
    typeof r.provenance.attribution !== "string" ||
    typeof r.provenance.ground_truth !== "string" ||
    !Array.isArray(r.provenance.scenes) ||
    r.provenance.scenes.length !== 2 ||
    !r.provenance.scenes.every((s) => s && typeof s.datetime === "string") ||
    r.method?.reference_verified !== true ||
    typeof r.method.index !== "string"
  )
    return false;
  const count = r.grid.width * r.grid.height;
  if (!r.pixels) return false;
  for (const k of ["before_index", "after_index", "delta"] as const)
    if (
      !Array.isArray(r.pixels[k]) ||
      r.pixels[k].length !== count ||
      !r.pixels[k].every((v) => v === null || (finite(v) && Math.abs(v) <= 2))
    )
      return false;
  for (const [k, max] of [
    ["class", 4],
    ["region", count],
    ["before_rgb", 0xffffff],
    ["after_rgb", 0xffffff],
  ] as const)
    if (
      !Array.isArray(r.pixels[k]) ||
      r.pixels[k].length !== count ||
      !r.pixels[k].every((v) => Number.isInteger(v) && v >= 0 && v <= max)
    )
      return false;
  if (
    !r.summary ||
    ![
      "pixels",
      "comparable",
      "candidate_pixels",
      "candidate_ha",
      "increase_pixels",
      "decrease_pixels",
      "filtered_pixels",
      "regions",
    ].every((k) => finite(r.summary[k])) ||
    r.summary.pixels !== count ||
    !["candidate_fraction", "mean_delta"].every(
      (k) => r.summary[k] === null || finite(r.summary[k]),
    ) ||
    !r.quality ||
    !Object.values(r.quality).every(finite) ||
    !Array.isArray(r.regions) ||
    r.regions.length > count ||
    !r.regions.every(
      (v) =>
        v &&
        Number.isInteger(v.id) &&
        v.id > 0 &&
        v.id <= count &&
        typeof v.direction === "string" &&
        Number.isInteger(v.pixels) &&
        v.pixels > 0 &&
        Array.isArray(v.bbox_rc) &&
        v.bbox_rc.length === 4 &&
        v.bbox_rc.every(finite),
    ) ||
    !Array.isArray(r.sensitivity) ||
    r.sensitivity.length !== 3 ||
    !r.sensitivity.every((v) => v && finite(v.threshold) && finite(v.raw_candidate_pixels)) ||
    !Array.isArray(r.limits) ||
    !r.limits.every((v) => typeof v === "string")
  )
    return false;
  return (
    r.truth === null ||
    (!!r.truth &&
      typeof r.truth === "object" &&
      ["precision", "recall", "iou"].every((k) => r.truth![k] === null || finite(r.truth![k])))
  );
}
/** Convert packed numerical RGB into bounded RGBA; unknown pixels use an explicit gray checker. */
export function pixelColor(
  packed: number,
  classification: number,
  x: number,
  y: number,
  change: boolean,
): number[] {
  if (classification === 0)
    return (Math.floor(x / 3) + Math.floor(y / 3)) % 2
      ? [105, 115, 106, 255]
      : [190, 198, 186, 255];
  if (change) {
    if (classification === 2) return [12, 96, 134, 255];
    if (classification === 3) return [157, 63, 47, 255];
    if (classification === 4) return [180, 141, 42, 255];
  }
  return [(packed >>> 16) & 255, (packed >>> 8) & 255, packed & 255, 255];
}
