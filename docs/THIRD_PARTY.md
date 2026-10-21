# Notices and references

Maintained by Jason Stys. Project-authored source is MIT licensed; imagery and third-party software retain their own terms. No affiliation or endorsement is implied.

## Data

**Contains modified Copernicus Sentinel data (2020)**, processed by Jason Stys, with original COGs supplied by Element 84. [DATA](DATA.md) records source identities, acquisition URLs, hashes, scaling, transformations, attribution and official terms. Project MIT licensing does not relicense this data. Synthetic fixtures are original deterministic arrays, not copied satellite labels or measured accuracy results.

## Runtime and portable bundle

| Component                               | Retained notices                                                                                                |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Project                                 | `_internal/licenses/project/LICENSE`                                                                            |
| CPython and its distributed components  | `_internal/licenses/python/PYTHON.txt` from the interpreter distribution                                        |
| PyInstaller bootloader/runtime          | `_internal/licenses/pyinstaller/COPYING.txt`, copied from the locked distribution                               |
| Vite-generated runtime                  | `_internal/licenses/vite/LICENSE.md`, actual locked Vite core and bundled notices                               |
| Rasterio/NumPy and runtime dependencies | Actual package `.dist-info` metadata/license trees, retained through recursive runtime metadata copying         |
| GDAL/OGR                                | Actual bundled `rasterio/gdal_data/LICENSE.TXT` and `copyright`                                                 |
| PROJ                                    | Actual bundled `rasterio/proj_data/copyright` and accompanying coordinate data                                  |
| Collected GCC runtime on Linux          | Actual Ubuntu/Debian libstdc++/libgcc package copyright files and GPL-3 text under `licenses/compiler-runtime/` |

NumPy's distributed license tree includes notices for bundled numerical components. Rasterio collects native geospatial libraries and coordinate resources, not just Python source; packaging retains those supplied notice/data files and smoke-tests real coordinate exports. Exact binary contents differ by OS and locked wheel. PyInstaller's COPYING includes its bootloader exception; Linux runtime notices include their respective exceptions/terms. These summaries are not replacements for the actual notices or legal advice. Bundles are unsigned/unnotarized console applications, not Electron or mobile installers.

Development dependencies (pytest, Hypothesis, Ruff, mypy, audit/build tools, TypeScript, Vitest, Playwright, axe and Prettier) are pinned with hashes/integrities. They are not all indiscriminately shipped as application dependencies. Universal Python locks were generated with uv 0.13.4 for Python 3.12 compatibility; releases install exact hash-checked distributions. Changing dependencies requires license/audit and cross-platform packaging review again.

Scientific/library context: [USGS NDVI](https://www.usgs.gov/landsat-missions/landsat-normalized-difference-vegetation-index), [Copernicus Sentinel-2 processing](https://sentiwiki.copernicus.eu/web/s2-processing), [Rasterio documentation](https://rasterio.readthedocs.io/en/stable/). No page prose, logos or provider application software was copied into the UI. Application screenshots show the attributed public crop or original synthetic tests.
