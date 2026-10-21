/** FIELDNOTE environmental review UI by Jason Stys; source/definition/variable index: docs/CODE_INDEX.md.
 * Real report arrays drive every pixel; client review is opt-in local memory, never an automatic decision.
 */
import "./style.css";
import {
  cases,
  choices,
  defaults,
  display,
  escape,
  isReport,
  pixelColor,
  preferences,
  type Report,
  type Settings,
} from "./contracts";
const storageKey = "fieldnote-controls-v1";
let remember = false,
  settings = { ...defaults };
try {
  const saved = preferences(localStorage.getItem(storageKey));
  if (saved) {
    settings = saved;
    remember = true;
  }
} catch {
  /* Storage is optional. */
}
let report: Report | null = null,
  controller: AbortController | null = null,
  selected = 0,
  blend = 50,
  layer = "swipe",
  zoom = 1;
const decisions = new Map<number, { decision: string; note: string }>();
document.querySelector<HTMLDivElement>("#app")!.innerHTML = /* HTML */ `<header>
    <a class="brand" href="#workspace"
      ><span class="mark" aria-hidden="true">◈</span> FIELDNOTE
      <small>EARTH OBSERVATION STUDIO</small></a
    >
    <nav aria-label="Project">
      <a href="#method">Method & limits</a
      ><a href="https://github.com/JasonStys/earth-observation-change-studio">Source ↗</a
      ><a href="https://github.com/JasonStys">Jason Stys ↗</a>
    </nav>
  </header>
  <main id="workspace">
    <section class="hero">
      <div>
        <p class="eyebrow">01 / TWO DATES · ONE SHARED GRID</p>
        <h1>Notice the change.<br /><em>Question the cause.</em></h1>
        <p class="intro">
          Compare environmental imagery, inspect what was excluded, and turn spectral differences
          into a traceable review—not a premature conclusion.
        </p>
      </div>
      <aside>
        <span class="tag">OFFLINE / SOURCE-TRACEABLE</span>
        <p>From image to evidence.</p>
        <small>Python · NumPy · Rasterio<br />Independent scalar verification</small>
      </aside>
    </section>
    <section class="settings" aria-label="Analysis controls">
      <div id="controls"></div>
      <label class="remember"
        ><input id="remember" type="checkbox" />Remember controls on this device</label
      >
    </section>
    <p id="status" role="status" aria-live="polite">Loading imagery…</p>
    <div id="evidence" hidden></div>
    <section class="method" id="method">
      <p class="eyebrow">METHOD / WHAT THESE COLORS CAN'T TELL YOU</p>
      <h2>A difference is an observation.<br /><em>Its cause is a separate question.</em></h2>
      <div class="method-grid">
        <article>
          <h3>01 · Make pixels comparable</h3>
          <p>
            The second date is aligned to the first UTM grid by nearest neighbour. Cloud, shadow,
            snow, nodata and small denominators are excluded; a conservative margin expands those
            exclusions.
          </p>
        </article>
        <article>
          <h3>02 · Expose the decisions</h3>
          <p>
            NDVI and green/NIR NDWI are ratios, not event classifiers. Thresholds and
            connected-region filters select candidates. Sensitivity is not a probability or
            confidence interval.
          </p>
        </article>
        <article>
          <h3>03 · Keep a human in the loop</h3>
          <p>
            Seasonality, illumination, crop management and residual cloud can change an index.
            Accepting a candidate records your review—not a verified flood, damage or land-cover
            label.
          </p>
        </article>
      </div>
      <p>
        <a
          href="https://github.com/JasonStys/earth-observation-change-studio/blob/main/docs/USER_GUIDE.md"
          >User guide ↗</a
        >
        ·
        <a href="https://github.com/JasonStys/earth-observation-change-studio/issues"
          >Help / report an issue ↗</a
        >
      </p>
    </section>
  </main>
  <footer>
    <span>Designed and engineered by <a href="https://github.com/JasonStys">Jason Stys</a></span
    ><small>CIVILIAN ENVIRONMENTAL REVIEW · NO AFFILIATION OR ENDORSEMENT</small>
  </footer>`;
const evidence = document.querySelector<HTMLDivElement>("#evidence")!,
  status = document.querySelector<HTMLParagraphElement>("#status")!;
/** Render finite selectors with explicit units; the controls remain stable across result refreshes. */
function controls(): void {
  document.querySelector("#controls")!.innerHTML =
    [
      ["scenario", "Case", Object.entries(cases)],
      [
        "metric",
        "Spectral index",
        [
          ["ndvi", "NDVI / vegetation"],
          ["ndwi", "NDWI / green–NIR"],
        ],
      ],
      ["threshold", "Change threshold", choices.threshold.map((v) => [v, display(v / 100)])],
      ["margin", "Quality margin / pixels", choices.margin.map((v) => [v, v])],
      ["minimum", "Minimum region / pixels", choices.minimum.map((v) => [v, v])],
      [
        "quality",
        "SCL policy",
        [
          ["strict", "Strict / classes 4, 5, 6"],
          ["unclassified", "Also class 7 / caution"],
        ],
      ],
    ]
      .map(
        ([key, label, items]) =>
          `<label>${label}<select id="${key}">${(items as (string | number)[][]).map(([value, text]) => `<option value="${value}" ${String(settings[key as keyof Settings]) === String(value) ? "selected" : ""}>${text}</option>`).join("")}</select></label>`,
      )
      .join("") + `<button id="run">Compare dates ↗</button>`;
  for (const key of Object.keys(defaults) as (keyof Settings)[])
    document.querySelector<HTMLSelectElement>("#" + key)!.addEventListener("change", (e) => {
      const value = (e.target as HTMLSelectElement).value;
      settings = {
        ...settings,
        [key]: ["threshold", "margin", "minimum"].includes(key) ? Number(value) : value,
      };
      void load();
    });
  document.querySelector("#run")!.addEventListener("click", () => void load());
}
/** Abort superseded work, hide stale evidence, and never fabricate a successful analysis on errors. */
async function load(): Promise<void> {
  controller?.abort();
  const current = new AbortController();
  controller = current;
  report = null;
  evidence.hidden = true;
  status.textContent = "Aligning imagery and checking every comparable pixel…";
  decisions.clear();
  if (remember)
    try {
      localStorage.setItem(storageKey, JSON.stringify(settings));
    } catch {
      /* Optional storage. */
    }
  try {
    const query = new URLSearchParams(Object.entries(settings).map(([k, v]) => [k, String(v)]));
    const response = await fetch(`/api/run?${query}`, {
      signal: current.signal,
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Unavailable");
    const value: unknown = await response.json();
    if (!isReport(value)) throw new Error("Invalid evidence");
    if (controller !== current) return;
    report = value;
    selected =
      Math.floor(value.grid.height / 2) * value.grid.width + Math.floor(value.grid.width / 2);
    evidence.hidden = false;
    render();
    status.textContent = "Verified: vector and scalar indices agree. Pixel accounting passed.";
  } catch {
    if (current.signal.aborted || controller !== current) return;
    status.innerHTML = /* HTML */ `Could not verify imagery. <button id="retry">Try again</button>`;
    document.querySelector("#retry")!.addEventListener("click", () => void load());
  }
}
/** Present observed/synthetic provenance, denominator-aware metrics, actual imagery and review/export tools. */
function render(): void {
  if (!report) return;
  const r = report,
    s = r.summary,
    g = r.grid;
  const query = new URLSearchParams(Object.entries(r.settings).map(([k, v]) => [k, String(v)]));
  evidence.innerHTML = /* HTML */ `<div class="metrics">
      <article>
        <p>COMPARABLE PIXELS</p>
        <strong>${escape(s.comparable)}</strong
        ><small>of ${escape(s.pixels)} on the reference grid</small>
      </article>
      <article>
        <p>RETAINED CANDIDATES</p>
        <strong>${escape(s.candidate_pixels)}</strong
        ><small
          >${s.candidate_fraction === null ? "No comparable pixels" : display(Number(s.candidate_fraction) * 100, 1) + "% of comparable pixels"}</small
        >
      </article>
      <article>
        <p>NOMINAL CANDIDATE AREA</p>
        <strong>${display(s.candidate_ha)}</strong
        ><small>hectares / UTM grid, not survey area</small>
      </article>
      <article>
        <p>REVIEW REGIONS</p>
        <strong>${escape(s.regions)}</strong><small>four-connected / same direction</small>
      </article>
    </div>
    <section class="panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">02 / REGISTER · COMPARE · INSPECT</p>
          <h2>The same place. A different moment.</h2>
        </div>
        <span class="tag"
          >${r.provenance.kind === "synthetic" ? "SYNTHETIC / KNOWN ANSWER" : "PUBLIC OBSERVATIONS / NO GROUND TRUTH"}</span
        >
      </div>
      <p class="attribution">${escape(r.provenance.attribution)}</p>
      <div class="image-controls">
        <label
          >View<select id="layer">
            <option value="swipe">Before / after swipe</option>
            <option value="before">Before image</option>
            <option value="after">After image</option>
            <option value="change">Candidate overlay</option>
          </select></label
        ><label
          >Compare split / %<input
            id="blend"
            type="range"
            min="0"
            max="100"
            value="${blend}" /></label
        ><label
          >Zoom<select id="zoom">
            <option value="1">1×</option>
            <option value="2">2×</option>
            <option value="4">4×</option>
          </select></label
        >
      </div>
      <div
        class="image-frame"
        tabindex="0"
        role="region"
        aria-label="Scrollable environmental imagery"
      >
        <canvas
          id="map"
          width="${g.width}"
          height="${g.height}"
          role="img"
          aria-label="Aligned environmental imagery; use row and column controls or CSV for exact pixel evidence"
        ></canvas>
        <div class="image-caption">
          <span>${escape(r.provenance.scenes[0]!.datetime.slice(0, 10))} / before</span
          ><span>N ↑ · ${escape(g.crs)} · ${g.width} × ${g.height}</span
          ><span>${escape(r.provenance.scenes[1]!.datetime.slice(0, 10))} / after</span>
        </div>
      </div>
      <div class="legend">
        <span class="inc">Index increase</span><span class="dec">Index decrease</span
        ><span class="filtered">Below minimum region</span
        ><span class="unknown">Excluded / unknown</span>
      </div>
      <p>
        Identical 0–0.35 reflectance display stretch on both dates. Cloud/quality exclusions are
        gray—not unchanged land. Click a pixel or use the keyboard controls below. Nearest-grid
        alignment is not a guarantee of subpixel registration.
      </p>
      <div class="inspector">
        <div class="pixel-controls">
          <label
            >Pixel row (zero-based)<input
              id="row"
              type="number"
              min="0"
              max="${g.height - 1}" /></label
          ><label
            >Pixel column (zero-based)<input id="column" type="number" min="0" max="${g.width - 1}"
          /></label>
        </div>
        <div id="pixel-info"></div>
      </div>
    </section>
    <section class="panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">03 / QUALITY BEFORE QUANTITY</p>
          <h2>Unknown isn't unchanged.</h2>
        </div>
        <span class="tag">DISJOINT PIXEL ACCOUNTING</span>
      </div>
      <div class="quality-grid">
        <div id="quality-breakdown"></div>
        <div>
          <h3>Threshold sensitivity</h3>
          <p>
            Raw candidate counts before minimum-region filtering. Not uncertainty probabilities.
          </p>
          <div id="sensitivity"></div>
        </div>
      </div>
      <p id="truth"></p>
    </section>
    <section class="panel">
      <p class="eyebrow">04 / HUMAN REVIEW</p>
      <h2>Keep the interpretation explicit.</h2>
      <p>
        Review is held only in this page's memory. It clears when analysis changes or the tab
        closes. A review decision does not establish environmental ground truth.
      </p>
      <label
        >Candidate region<select id="region">
          <option value="0">Select a region</option>
          ${r.regions
            .slice(0, 100)
            .map(
              (v) =>
                `<option value="${v.id}">Region ${v.id} / ${escape(v.direction)} / ${v.pixels} pixels</option>`,
            )
            .join("")}
        </select></label
      >${r.regions.length > 100 ? "<p>First 100 regions shown. All region IDs and footprints remain in JSON/CSV/GeoJSON exports.</p>" : ""}
      <div id="review-form" hidden>
        <p id="region-info"></p>
        <label
          >Disposition<select id="decision">
            <option value="unreviewed">Unreviewed</option>
            <option value="accept-candidate">Accept as a candidate for investigation</option>
            <option value="reject-candidate">Reject candidate</option>
            <option value="needs-context">Needs more context</option>
          </select></label
        ><label
          >Review note / no personal or sensitive data<textarea
            id="note"
            maxlength="280"
            rows="3"
          ></textarea></label
        ><button id="save-review">Record in this tab</button>
      </div>
      <p id="review-status" role="status">0 local reviews recorded</p>
      <button id="download-review">Download review JSON</button>
    </section>
    <section class="panel">
      <p class="eyebrow">05 / REPRODUCIBLE EVIDENCE</p>
      <h2>The exclusions travel with the result.</h2>
      <p>
        All retained GeoJSON footprints are exported in WGS84 longitude/latitude. GeoTIFF retains
        the reference UTM grid and two bands: class and region ID. No export turns a candidate into
        a confirmed event.
      </p>
      <div class="downloads">
        ${["json", "csv", "html", "geojson", "tif"].map((format) => `<a href="/api/report?${query}&format=${format}" download>${format === "tif" ? "GeoTIFF" : format.toUpperCase()} ↓</a>`).join("")}
      </div>
      <p class="digest">REPORT SHA-256<br />${escape(r.id)}</p>
      <details>
        <summary>Source grids, method and limitations</summary>
        <pre>
${escape(JSON.stringify({ grid: r.grid, source: r.provenance, method: r.method }, null, 2))}</pre>
        <ul>
          ${r.limits.map((v) => `<li>${escape(v)}</li>`).join("")}
        </ul>
      </details>
    </section>`;
  const layerSelect = document.querySelector<HTMLSelectElement>("#layer")!;
  layerSelect.value = layer;
  layerSelect.addEventListener("change", () => {
    layer = layerSelect.value;
    draw();
  });
  document.querySelector<HTMLInputElement>("#blend")!.addEventListener("input", (e) => {
    blend = Number((e.target as HTMLInputElement).value);
    draw();
  });
  const z = document.querySelector<HTMLSelectElement>("#zoom")!;
  z.value = String(zoom);
  z.addEventListener("change", () => {
    zoom = Number(z.value);
    draw();
  });
  for (const field of ["row", "column"])
    document.querySelector<HTMLInputElement>("#" + field)!.addEventListener("change", () => {
      const y = Number(document.querySelector<HTMLInputElement>("#row")!.value),
        x = Number(document.querySelector<HTMLInputElement>("#column")!.value);
      selected =
        Math.max(0, Math.min(g.height - 1, Math.trunc(Number.isFinite(y) ? y : 0))) * g.width +
        Math.max(0, Math.min(g.width - 1, Math.trunc(Number.isFinite(x) ? x : 0)));
      inspect();
      draw();
    });
  document.querySelector<HTMLCanvasElement>("#map")!.addEventListener("click", (e) => {
    const canvas = e.currentTarget as HTMLCanvasElement,
      box = canvas.getBoundingClientRect();
    selected =
      Math.max(
        0,
        Math.min(g.height - 1, Math.floor(((e.clientY - box.top) / box.height) * g.height)),
      ) *
        g.width +
      Math.max(
        0,
        Math.min(g.width - 1, Math.floor(((e.clientX - box.left) / box.width) * g.width)),
      );
    inspect();
    draw();
  });
  document.querySelector("#quality-breakdown")!.innerHTML = /* HTML */ `<h3>
      Every grid pixel has a place
    </h3>
    <dl>
      ${Object.entries(r.quality)
        .map(([k, v]) => `<div><dt>${escape(k.replaceAll("_", " "))}</dt><dd>${v}</dd></div>`)
        .join("")}
    </dl>`;
  document.querySelector("#sensitivity")!.innerHTML = r.sensitivity
    .map(
      (v) =>
        `<div class="sensitivity"><span>|Δ| ≥ ${display(v.threshold)}</span><meter min="0" max="${Math.max(1, Number(s.comparable))}" value="${v.raw_candidate_pixels}" aria-label="Raw candidates at threshold ${v.threshold}"></meter><strong>${v.raw_candidate_pixels}</strong></div>`,
    )
    .join("");
  document.querySelector("#truth")!.textContent = r.truth
    ? `Synthetic-only check: precision ${display(r.truth.precision, 3)}, recall ${display(r.truth.recall, 3)}, IoU ${display(r.truth.iou, 3)}. Evaluated only on comparable synthetic pixels; not public-image accuracy.`
    : "Public observations: no independent ground truth or accuracy score. Human context is required.";
  document.querySelector("#region")!.addEventListener("change", reviewForm);
  document.querySelector("#save-review")!.addEventListener("click", () => {
    const id = Number(document.querySelector<HTMLSelectElement>("#region")!.value);
    if (!r.regions.some((v) => v.id === id)) return;
    decisions.set(id, {
      decision: document.querySelector<HTMLSelectElement>("#decision")!.value,
      note: document.querySelector<HTMLTextAreaElement>("#note")!.value.slice(0, 280),
    });
    document.querySelector("#review-status")!.textContent =
      `${decisions.size} local reviews recorded`;
  });
  document.querySelector("#download-review")!.addEventListener("click", () => {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            schema: 1,
            report_id: r.id,
            authoring: "Local human review; not environmental ground truth",
            regions: r.regions.map((v) => ({
              id: v.id,
              ...(decisions.get(v.id) ?? { decision: "unreviewed", note: "" }),
            })),
          },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob),
      link = document.createElement("a");
    link.href = url;
    link.download = "fieldnote-review.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  inspect();
  draw();
}
/** Rasterize the actual bounded arrays; overlays and swipe never change the numerical evidence. */
function draw(): void {
  if (!report) return;
  const r = report,
    c = document.querySelector<HTMLCanvasElement>("#map")!,
    context = c.getContext("2d");
  if (!context) return;
  const image = context.createImageData(r.grid.width, r.grid.height);
  for (let i = 0; i < r.summary.pixels!; i++) {
    const x = i % r.grid.width,
      y = Math.floor(i / r.grid.width),
      before = layer === "before" || (layer === "swipe" && x / r.grid.width < blend / 100);
    image.data.set(
      pixelColor(
        (before ? r.pixels.before_rgb : r.pixels.after_rgb)[i]!,
        r.pixels.class[i]!,
        x,
        y,
        layer === "change",
      ),
      i * 4,
    );
  }
  context.putImageData(image, 0, 0);
  context.strokeStyle = "#fff";
  context.lineWidth = 0.5;
  context.strokeRect(
    (selected % r.grid.width) + 0.1,
    Math.floor(selected / r.grid.width) + 0.1,
    0.8,
    0.8,
  );
  c.style.width = `${zoom * Math.min(c.parentElement!.clientWidth, 560)}px`;
  c.style.margin = "auto";
  c.style.maxWidth = "none";
}
/** Show exact selected grid-cell evidence with missing/quality exclusions explicitly distinguished. */
function inspect(): void {
  if (!report) return;
  const r = report,
    y = Math.floor(selected / r.grid.width),
    x = selected % r.grid.width,
    t = r.grid.transform;
  document.querySelector<HTMLInputElement>("#row")!.value = String(y);
  document.querySelector<HTMLInputElement>("#column")!.value = String(x);
  document.querySelector("#pixel-info")!.innerHTML = /* HTML */ `<p class="eyebrow">
      ${["EXCLUDED / NOT COMPARABLE", "BELOW THRESHOLD", "INDEX INCREASE", "INDEX DECREASE", "FILTERED / SMALL REGION"][r.pixels.class[selected]!]}
    </p>
    <div class="pixel-values">
      <span>Before <strong>${display(r.pixels.before_index[selected], 4)}</strong></span
      ><span>After <strong>${display(r.pixels.after_index[selected], 4)}</strong></span
      ><span>Comparable Δ <strong>${display(r.pixels.delta[selected], 4)}</strong></span>
    </div>
    <small
      >Cell centre: ${display(t[2]! + (x + 0.5) * t[0]!, 1)} m E ·
      ${display(t[5]! + (y + 0.5) * t[4]!, 1)} m N · Region ${r.pixels.region[selected]}</small
    >`;
}
/** Load one region's local review without reflecting note text as HTML. */
function reviewForm(): void {
  if (!report) return;
  const id = Number(document.querySelector<HTMLSelectElement>("#region")!.value),
    region = report.regions.find((v) => v.id === id);
  document.querySelector<HTMLDivElement>("#review-form")!.hidden = !region;
  if (!region) return;
  const saved = decisions.get(id);
  document.querySelector("#region-info")!.textContent =
    `Region ${id}: ${region.direction}, ${region.pixels} pixels. Pixel bounds: ${region.bbox_rc.join(", ")}.`;
  document.querySelector<HTMLSelectElement>("#decision")!.value = saved?.decision ?? "unreviewed";
  document.querySelector<HTMLTextAreaElement>("#note")!.value = saved?.note ?? "";
}
controls();
document.querySelector<HTMLInputElement>("#remember")!.checked = remember;
document.querySelector("#remember")!.addEventListener("change", (e) => {
  remember = (e.target as HTMLInputElement).checked;
  try {
    if (remember) localStorage.setItem(storageKey, JSON.stringify(settings));
    else localStorage.removeItem(storageKey);
  } catch {
    /* Optional storage. */
  }
});
void load();
