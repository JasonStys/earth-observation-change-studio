# Validation evidence and strategy

Prepared by Jason Stys. Software verification is distinct from environmental event accuracy, sensor calibration or operational qualification.

## Executed local results

Windows x64, Python 3.14.6, Node 24.18.1, Rasterio 1.5.2 / bundled GDAL 3.12.2, NumPy 2.5.4:

| Check                                     | Executed result                                                                                    |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------- |
| pytest                                    | **999 passed**, with warnings treated as errors                                                    |
| Python combined statement/branch coverage | **99.72%**, enforced minimum 90%                                                                   |
| Full finite analysis controls             | All **864 combinations** verified against the scalar reference                                     |
| Generated spectra                         | One Hypothesis test with **100 generated examples**, not 100 separately counted pytest cases       |
| Ruff / strict mypy                        | Passed; eight runtime modules checked                                                              |
| TypeScript unit tests / production build  | **12 passed**; strict TypeScript and Vite build passed                                             |
| Browser integration                       | **30 passed** across Chromium, Firefox and WebKit, including mobile/keyboard/axe checks            |
| Dependency audits                         | Hash-pinned Python development graph and npm graph: no known vulnerabilities reported at execution |
| Numerical benchmark                       | All eight reviewed case summaries matched declared tolerances                                      |

The recorded development benchmark measured approximately **753 ms median** with Python allocation tracing enabled and approximately **9.61 MB traced Python peak** for the default public-crop workload, including Rasterio I/O, scalar/reference verification, arrays and JSON-report construction. This is not native/GDAL RSS, total process memory, a hard latency guarantee or a fair cross-machine speed comparison. The benchmark command prints fresh measurements while checking [reviewed numerical summaries](reports/benchmark.json); it does not rewrite those contracts during normal checks.

## Oracles and coverage

- Hand-derived constant spectral ratios and a 12×16 changed rectangle establish 192 retained cells, one region and 1.92 nominal hectares. A water-like rectangle tests NDWI direction independently of NDVI sign.
- Every ratio/raw classification is compared with an independently structured scalar implementation, using `1e-12` relative/absolute ratio tolerance and exact class agreement. Component filtering has independent four-connectivity, sign-separation and size tests.
- Analytic integer translation checks map column `j` to source `j−2`, including uncovered edges. Rasterio's coordinate machinery is not falsely claimed independently physically validated by reusing the same warp in both ratio implementations.
- Nodata, SCL 0..11, class-7 policy, zero denominators, quality-margin crop edges, same/opposite signs, small-region suppression, all-masked inputs, and monotonic threshold sensitivity are exercised.
- Real GeoTIFF roundtrips preserve CRS, grid, class/region pixels and report tags. Real GeoJSON exports preserve candidate membership and WGS84 coordinate ranges. CSV retains dimensioned cell centres; HTML hostile text remains escaped.
- Strict local file/manifest tests reject malformed fields, duplicates, encoding/nesting/size errors, checksum mismatches, non-UTC/reversed dates, unsupported drivers/bands/dtypes/CRSs, excessive dimensions, invalid radiometry and fractional SCL values. These checks do not make native GDAL a malicious-file sandbox.
- HTTP/CLI/SQL tests cover finite routes, Host/Origin/Fetch Metadata, traversal/path confinement, no mutation routes, binary MIME, safe errors, immutable hash-verified history, idempotence, 100-entry limits, concurrent inserts, explicit connection closure and create-only exports.
- Browser tests use the actual geospatial service except explicit failure/hostile-response regressions. They exercise public/synthetic distinctions, imagery/pixel inspection, real export formats, local human-review downloads/reset, opt-in preference removal, stale-evidence retry, hostile labels, unique IDs and persistent SCL controls, mobile width, keyboard and axe checks. Accessibility automation does not replace user testing.

## Findings and fixes

| Finding                                                    | Cause and correction                                                                                                                                                                                        | Regression/evidence                                                                        |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Search-box intersection did not imply crop-centre coverage | Initial acquisition centre lay below the selected source tile. Moved the explicitly documented public crop north within that tile and added full-window source bounds rejection; no padding/fabricated data | Retained exact crop windows/transforms/hashes and real source-load checks                  |
| SCL selector overwritten by summary                        | Duplicate `quality` IDs let a summary write target a selector. Renamed the output ID; did not remove the policy control                                                                                     | Actual three-engine regression checks selector options/value and every DOM ID's uniqueness |
| Local test infrastructure restrictions                     | A sandbox temporary directory was not writable. Used a task-owned TEMP/TMP and uv cache directory, without changing host protections                                                                        | Complete rerun of actual tests; no tests/coverage gates waived                             |
| SQL test-fixture connection warnings                       | SQLite transaction context managers do not close connections. Test fixtures now explicitly use `closing`, as production already did                                                                         | Fresh strict-warning suite passes without leaking test connections                         |

An early HTTP-test import alias shadowed `http.client`; the harness import was corrected rather than changing correct service behavior. The default image fit was adjusted after visual inspection to show the whole crop before zooming. No warning/coverage suppression was added to obtain a pass.

## Hosted and release evidence

The [Validation workflow](https://github.com/JasonStys/earth-observation-change-studio/actions/workflows/validate.yml) defines eight jobs: four model OS/Python combinations, one three-browser integration job, and three actual portable-app jobs. [CodeQL](https://github.com/JasonStys/earth-observation-change-studio/actions/workflows/codeql.yml) analyzes Python and JavaScript/TypeScript. Successful analysis is not the same as zero findings, so open alerts are reviewed separately.

The [manual release workflow](https://github.com/JasonStys/earth-observation-change-studio/actions/workflows/release.yml) requires successful exact-commit Validation and CodeQL runs, then builds/smoke-tests each OS before direct draft upload. Release notes record the accepted SHA, completed run links, audits, download SHA-256/CRC/notice checks and actual downloaded-app tests. Workflow definitions alone are not execution evidence; never claim pending jobs passed. No Actions artifacts or caches are uploaded.

## Explicit gaps

The public crop has **no independent ground truth and no accuracy score**. No event cause, calibrated uncertainty, subpixel registration, cross-sensor harmonization, large-area generalization, feature registration or trained classifier is validated. SCL can miss clouds/shadows and spectra can change seasonally. Nominal UTM areas are not survey-grade geodesic measurements. No multiuser hosting, hostile-file sandbox, hardware integration, automatic alerting, signing/notarization or mobile installer is implemented. Synthetic agreement proves only the stated synthetic/software contracts.
