# Spectral model and interpretation

Prepared by Jason Stys. This is a transparent environmental-review baseline, not a flood/damage classifier or operational monitoring service.

## Inputs and geospatial alignment

Each scene contains four surface-reflectance bands in the order **red, green, blue, NIR**, plus a Sentinel-style SCL class band. Reflectance is already normalized, not raw digital numbers. Runtime files are float32 five-band GeoTIFFs; computation converts to float64. Only WGS84 UTM metre CRS EPSG:32601–32660 and 32701–32760 are accepted, with north-up 1..1000 m pixel axes, bounded UTM extents and at most 128 pixels per axis. Pixel-centre coordinates use `x=c+(column+0.5)*a`, `y=f+(row+0.5)*e` from affine `[a,0,c,0,e,f]`.

The first scene defines output extent/resolution/CRS. The second scene is warped to it by nearest neighbour, including its independent coverage mask and SCL. Uncovered target cells remain invalid. Equal shapes do not imply equal geography. This is coordinate-grid alignment, **not image-feature registration**; no subpixel accuracy or registration confidence is inferred. Both source grids are retained in provenance.

## Indices and quality stages

- NDVI = `(NIR-red)/(NIR+red)`.
- Green/NIR NDWI = `(green-NIR)/(green+NIR)`, not the NIR/SWIR index also sometimes called NDWI.
- Valid reflectance is finite in [0,1.5] for all four bands. This envelope is an input policy, not a claim that every physical surface has that reflectance range.
- A denominator must exceed `1e-6`; otherwise the index is unavailable. Missing values are null in JSON/blank in CSV, never invented zeros.
- Strict quality retains SCL **4 vegetation, 5 not-vegetated, 6 water**. The explicit cautious alternative also retains **7 unclassified**. All other classes—including nodata, defective/saturated, dark/cast shadow, cloud shadow, cloud, cirrus and snow/ice—are excluded.

The disjoint accounting stages are: (1) invalid data/footprint; (2) remaining SCL exclusions; (3) remaining invalid denominators; (4) remaining quality-margin exclusions; (5) comparable pixels. Counts must sum exactly to the reference grid's N pixels. The optional margin is a Chebyshev/square dilation radius of 0,1,2 target pixels around any incomparable pixel. Outside the crop counts as unknown, so a margin also excludes border cells. This is conservative morphology, not an estimated cloud-edge uncertainty distribution.

## Candidate classes and regions

On comparable pixels, `delta=after_index-before_index`. Changes use unrounded values:

| Code | Meaning                                            |
| ---- | -------------------------------------------------- |
| 0    | Excluded / not comparable                          |
| 1    | `abs(delta) < threshold`                           |
| 2    | `delta >= threshold`, retained increase candidate  |
| 3    | `delta <= -threshold`, retained decrease candidate |
| 4    | Above threshold but removed by minimum-region size |

Threshold choices are 0.10, 0.20 and 0.30, represented in settings as integer hundredths. Same-direction raw candidates are grouped with **four-connectivity**, not diagonal connectivity. Groups below 1,4,16 pixels are marked code 4. IDs of retained groups follow row-major discovery order; bounding boxes use `[min_row,min_column,exclusive_max_row,exclusive_max_column]`. A pixel/region membership gate verifies retained cells equal the sum of retained region sizes.

Nominal candidate area = candidate pixels × `abs(a*e)/10000` hectares. This is projected-grid area, not a geodesic/survey area. Candidate fraction divides by **comparable** pixels, not total pixels. With no comparable pixels, candidate fraction and mean delta are unavailable; zero detected cells does not demonstrate an unchanged environment.

Sensitivity reports raw comparable-pixel counts at threshold−0.05, threshold and threshold+0.05 **before** minimum-region filtering. These are heuristic sensitivity values, not confidence intervals or event probabilities. RGB display applies the same linear reflectance [0,0.35] stretch to both dates; display clipping does not alter the analysis.

## Verification, not environmental validation

An independently structured scalar implementation recomputes per-pixel ratios, SCL eligibility, margin decisions and raw candidate classes. Index values must agree within relative/absolute `1e-12`; raw classes must match exactly. It uses the same Rasterio-warped inputs, so agreement does not independently validate GDAL transforms or geolocation. Known integer translations have hand-derived expected column offsets; GeoTIFF and GeoJSON roundtrips check grid/coordinate consistency.

Synthetic cases define known changed rectangles or unchanged scenes. Precision, recall and intersection-over-union are computed **only on comparable synthetic pixels**. Undefined denominators yield unavailable scores, not 100% accuracy. Real public imagery has no supplied independent labels and receives no accuracy score. Reports quantize displayed indices to six decimals **after** classification; summary benchmarks use absolute `1e-6` / relative `1e-8` tolerances. Cross-platform full report byte identity is not promised.

## Important limitations

Two dates and one small crop cannot establish cause. Seasonality, planting/harvest, illumination, atmospheric correction, mixed pixels and residual clouds can shift an index. SCL itself can be wrong. Small changes can vanish under nearest resampling or minimum-region filtering; no calibration, uncertainty propagation, feature registration, terrain correction, land-cover training, causal inference or event-alerting system is implemented. Review acceptance is a human disposition, not independently established ground truth.

References: [USGS NDVI](https://www.usgs.gov/landsat-missions/landsat-normalized-difference-vegetation-index), [Copernicus Sentinel-2 processing](https://sentiwiki.copernicus.eu/web/s2-processing), [Rasterio reprojection](https://rasterio.readthedocs.io/en/stable/topics/reproject.html), [Rasterio nodata masks](https://rasterio.readthedocs.io/en/stable/topics/masks.html). These provide scientific/library context, not endorsement or validation of this application's results.
