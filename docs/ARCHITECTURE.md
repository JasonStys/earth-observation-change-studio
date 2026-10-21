# Architecture and decisions

Author: Jason Stys. Purpose: bounded, offline civilian environmental change review, with scientific provenance and human interpretation kept separate.

```text
Finite browser controls -> read-only protected loopback API
Explicit CLI manifest -> same-directory local five-band GeoTIFFs
  -> validate grids, bands, dates, byte hashes and dimensions
  -> align second scene to first UTM grid by nearest neighbour
  -> vectorized spectral ratios and disjoint quality exclusions
  -> independently structured scalar ratio/classification oracle
  -> four-connected same-sign regions and pixel-accounting gate
  -> complete report / geospatial exports / opt-in local SQL history
Browser-only review -> in-memory dispositions -> explicit review JSON download
```

## Decisions and trade-offs

| Choice                               | Reason                                                                                             | Boundary/cost                                                                                        |
| ------------------------------------ | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| NumPy + Rasterio/GDAL                | Native geospatial and vector array operations suit rasters, coordinate transforms and TIFFs        | Compiled wheels/native notices and portable-build testing; not a malicious-file sandbox              |
| Independent scalar oracle            | Verify ratios, quality margins and raw candidate classes without calling production vector helpers | Extra CPU; both implementations still share the specification and warped input                       |
| First scene is the reference         | Explicit grid/extent, reproducible pixel centres and unchanged output geometry                     | No automatic mosaic, optimum resolution selection, subpixel registration or alignment-error estimate |
| Nearest resampling                   | Preserve categorical SCL and avoid mixed spectra across invalid pixels                             | Aliasing and positional error remain; not a scientific guarantee of co-registration                  |
| Simple threshold + connected regions | Transparent, testable baseline without a trained-model confidence fiction                          | Heuristic candidates, not event labels; cause/accuracy needs external evidence                       |
| Read-only local server               | No auth, remote fetch, uploads or server-side review mutation surface                              | Not a public multiuser service or hostile-local-client quota system                                  |
| Opt-in SQLite evidence               | Content identity, immutable entries and explicit local persistence                                 | Unencrypted local files, no automatic retention/pruning or tenant isolation                          |

## Trust boundaries

The runtime never fetches satellite data. Its public samples are stored with hashes and provenance. `tools/acquire_sample.py` is an explicit development-only network tool with fixed provider IDs and a fixed allowed data host; tests, launches and releases do not run it. CLI imports cannot select an executable, driver, URL or arbitrary projection pipeline. Paths in the small manifest are simple same-directory filenames. TIFFs are limited in encoded bytes and decoded dimensions before array reads. Rasterio/native GDAL still parses headers: supply only reviewed/trusted local imagery, not hostile uploads.

The API exposes only finite settings. Host, Origin and Fetch Metadata checks protect loopback browser use; paths are confined to built assets; reports are escaped/inert. UI inputs are bounded and received reports are shape-checked before canvas allocation. Personal information and review notes are neither requested by the service nor sent to an operator. Optional local storage contains control preferences only. Closing a browser tab does not stop the server.

## Work and storage bounds

Let N be reference pixels (at most 128×128), K be retained regions, and R be the quality margin (0..2). Fixed-band alignment, indices and serialization are O(N); square dilation and scalar validation are O(N(2R+1)²), thus O(N) within the supported fixed controls. Four-neighbour flood-fill marks each candidate once: O(N) time and O(N) arrays/queue/region cells. Each component's bounding-box scans together visit at most N cells. Region count K≤N. GeoJSON polygon generation is linear in grid/boundary output size for these bounded grids; its byte size can grow significantly on fragmented patterns. SQL caps reports at 100, not at a claimed fixed megabyte count.

The browser holds complete bounded arrays and redraws O(N) pixels. Review menus show the first 100 regions with an explicit notice when more exist; JSON/CSV/GeoJSON retain all IDs/footprints. No detection is silently removed because it is absent from the menu. Browser review decisions refer to report hash + region ID, and reset after every new analysis.

## Growth and non-goals

Large scenes need tiled/windowed processing, memory quotas, background jobs and appropriate storage. Public hosting would need authentication, TLS, isolation, input quarantine and a different service architecture. Scientifically stronger event classification would require calibrated labels, independent temporal/geographical holdouts, registration/error analysis and domain review. PostGIS could support a future multi-scene spatial catalog; SQLite is appropriate for this deliberately small offline evidence store. No such future capability is claimed implemented.
