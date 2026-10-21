# Local input, API and evidence contracts

Author: Jason Stys. The application has no remote-data fetch, login, upload, arbitrary-code execution or device API. All HTTP routes are read-only and loopback-only.

## CLI manifest

The small UTF-8 JSON manifest must contain exactly `schema`, `name`, `before`, `after`, `attribution`. Schema is integer 1, not a boolean. Name is 1..48 lowercase alphanumeric/hyphen characters, starting alphanumeric. Attribution is a nonempty string at most 240 characters. Duplicate object keys, invalid UTF-8, excessive nesting and files over 8 KiB are rejected.

Each date object contains exactly `file`, `sha256`, `datetime`:

- `file`: same-directory filename matching `[a-z0-9][a-z0-9-]{0,60}.tif`, with no URL, slash, traversal or symlink file.
- `sha256`: 64 lowercase hexadecimal characters matching the complete TIFF bytes.
- `datetime`: real UTC date/time in `20YY-MM-DDTHH:MM:SSZ` form; before must be strictly earlier than after. Local time, timezone ambiguity and inferred dates are not accepted.

The checked-in [real sample manifest](../eostudio/resources/sentinel/central-valley.json) is an executable example. For your own pair, create normalized files and compute their hashes, for example `Get-FileHash -Algorithm SHA256 your-file.tif`. Do not merely rename ordinary RGB imagery as a supported multispectral TIFF.

Each TIFF is local GTiff, at most 16 MiB encoded, exactly five **float32** bands in order red, green, blue, NIR reflectance, then SCL. It requires a supported north-up WGS84 UTM metre grid, 1..128 pixels per axis, positive x resolution 1..1000 m, negative y resolution −1000..−1 m, no rotation, bounded easting/northing extent, and a CRS in EPSG:32601–32660 or 32701–32760. Reflectance normalization must already have been applied **once**. Band meanings are a declared contract, not automatically inferred from arbitrary file descriptions.

Finite reflectance outside [0,1.5], nonfinite reflectance and nodata are excluded, not clamped into valid observations. SCL must be integer 0..11 where present; malformed SCL values are rejected. Native parsing is not a hostile-file sandbox. Only process reviewed/trusted local files; arbitrary internet/user uploads are out of scope.

For `export --input`, the manifest name, dates, rasters and grids define the actual pair. The recorded finite `settings.scenario` is an unused preset for imports; it does not replace those source files. Metric, threshold, margin, minimum-region and quality controls still apply. Paths never appear in report provenance.

## HTTP selectors

| Key         | Exact allowed values                 | Default          |
| ----------- | ------------------------------------ | ---------------- |
| `scenario`  | Eight keys exposed by `/api/catalog` | `central-valley` |
| `metric`    | `ndvi`, `ndwi`                       | `ndvi`           |
| `threshold` | integer 10,20,30 (hundredths)        | 20               |
| `margin`    | integer 0,1,2 target pixels          | 1                |
| `minimum`   | integer 1,4,16 pixels                | 4                |
| `quality`   | `strict`, `unclassified`             | `strict`         |

| Route                                                  | Result                                                                        |
| ------------------------------------------------------ | ----------------------------------------------------------------------------- |
| `GET /api/health`                                      | Local educational-service readiness, not a substitute for successful analysis |
| `GET /api/catalog`                                     | Finite scenarios, selectors and defaults                                      |
| `GET /api/run?...`                                     | Complete verified JSON report                                                 |
| `GET /api/report?...&format=json/csv/html/geojson/tif` | Fixed-name download in the selected format                                    |
| `GET /`, `/index.html`, `/assets/<built-name>`         | Confined production assets only                                               |

At most eight query fields and a 1,024-character request target; duplicates/unknown keys and unsupported combinations are rejected. Exact loopback Host and allowed Origin/Fetch Metadata are checked. No CORS allowance. Unsupported selectors/formats return 400, origin failures 403, absent paths 404, forbidden HTTP mutations 405, oversized targets 414, local resource/analysis failure 500. Diagnostics do not echo user inputs or local file paths. Browser state hides stale results and provides explicit retry after failure.

## Report identity and arrays

JSON includes schema, case name, selected settings, reference grid, both source-grid/date/hash provenance, method, limitations, disjoint quality accounting, summary, threshold sensitivity, regions and complete pixel arrays. All arrays are row-major and have `width*height` elements. Packed RGB integers contain 8-bit red/green/blue display channels, not reflectance. Ratio/delta arrays contain finite values or null. Class codes are documented in [MODEL](MODEL.md); region 0 means no retained component. Before/after indices can exist where QA excludes a comparison; only a nonnull `delta` is a comparable difference.

SHA-256 is computed over canonical sorted ASCII finite JSON excluding its own `id`. It identifies evidence content; it is **not a cryptographic signature or universal cross-platform hash guarantee**. Indices are quantized after analysis. Source TIFF byte hashes identify exact inputs; metadata/processing interpretation still matters.

## Geospatial and review exports

CSV contains row/column, projected cell-centre easting/northing metres, indices, comparable delta, class and region ID. All fields are fixed numeric columns; missing indices are blank. HTML is escaped static complete evidence, with no scripts or external resources. GeoTIFF has two uint16 bands, class and region, in the reference UTM grid, nodata 0 and report-id/meaning tags. In the region band, 0 includes comparable below-threshold pixels without a retained region; it is not a statement that the class band is unknown.

GeoJSON contains actual four-connected retained-pixel polygons, including geometry holes when present, transformed to WGS84 longitude/latitude. It does not export a bounding rectangle as though it were the actual footprint. Properties include report identity, region ID/direction/pixel count, unreviewed status and a candidate-not-confirmed warning. Areas remain the explicitly nominal source-grid calculation, not a new WGS84 degree-area calculation.

Browser review JSON contains schema 1, the report hash and **every** region ID with a local human disposition/note (default unreviewed). Notes are at most 280 characters. These decisions stay in memory until an explicit file download and clear on new analysis. Server-generated GeoJSON is not secretly modified by browser review; join a review export by report hash + region ID. No review data is sent back to the service or an account operator.

## Optional history

CLI `--history` inserts the full hash-verified report using bound SQL and a transaction. Repeated identities are idempotent. Updates/deletes are blocked by triggers; a 101st distinct report fails without pruning. Connection closure is explicit. The file is unencrypted and not protected from other OS users. History does not create an HTTP write route, account, review database or resume/checkpoint mechanism.
