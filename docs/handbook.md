# Earth Observation Change Studio handbook

By Jason Stys.

Inspect environmental change candidates, review immediate neighboring context and export GeoJSON in the 1.1 portable workflow.

Inspect environmental change candidates, review immediate neighboring context and export GeoJSON in the 1.1 portable workflow.

Carries the frozen geospatial runtime and source identity with the reviewer, so region context and actual exports remain inspectable after downloading and extracting the app.

## Read the documentation

| Edition                                                      | Audience and contents                                                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| [project-guide.docx](reports/project-guide.docx)             | User and developer guide: purpose, current usage, design, boundaries and source references.                        |
| [validation-review.docx](reports/validation-review.docx)     | Reviewer edition: exact tested baseline, observed workflows, dated local results and remaining limits.             |
| [validation-evidence.xlsx](reports/validation-evidence.xlsx) | Two filterable Excel Tables for observed workflows and test-source inventory, with recalculating outcome formulas. |

The editable Markdown remains the maintenance source. The Word files are readable editions. The workbook is an evidence index rather than a test runner. See [publication identities and review](reports/publications.json) and the [documentation refresh record](reports/documentation-refresh-2026-11-09.md).

## Current usage and help

[README quick start](../README.md) is the entry point. Use the project-specific guides below before changing inputs, operating modes or deployment assumptions.

### Usage and operations

- [RELEASE](RELEASE.md)
- [USER GUIDE](USER_GUIDE.md)

### Design and contracts

- [API](API.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [MODEL](MODEL.md)

### Security and validation

- [VALIDATION](VALIDATION.md)

## Historical results and reproduction

The reviewed source is [`e63d4d111512a36d1ffb19a04059b4d8965ac5d2`](https://github.com/JasonStys/earth-observation-change-studio/tree/e63d4d111512a36d1ffb19a04059b4d8965ac5d2). The observed functional workflow baseline is `e63d4d111512a36d1ffb19a04059b4d8965ac5d2`; those observations are recorded at `2026-11-10T05:25:40.628667+00:00`. They do not certify an unrun later revision.

- [Detailed recorded validation](reports/PORTABLE_RELEASE_20261109.md)
- [Current Actions](https://github.com/JasonStys/earth-observation-change-studio/actions) records later integration checks separately.
- Preserve dated measurements and follow the existing testing guide to reproduce them; a test-source inventory alone does not establish execution.

## Practical boundaries

- Four-neighbor availability describes local raster context, not environmental cause, registration accuracy or verified ground truth.
- Uses bounded synthetic/frozen public environmental imagery; no identifying surveillance or targeting capability.
- Unsigned portable desktop packages; no signed installer, public accounts, native mobile installation or environmental certification.

## Maintaining these editions

Update the editable usage/design/test documents first. Rebuild and visually review every Word page and workbook tab before replacing an edition; verify the exact binary digests and evidence source in publications.json. Keep account data, logs with secrets, installed-app state and private test stores out of documentation. Source and release assets retain their existing security and licensing boundaries.
