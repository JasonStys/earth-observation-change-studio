# Release and local operations runbook

Maintained by Jason Stys. This ships an offline desktop scientific-review application, not a production hosted service.

## Pre-release gates

1. Inspect live Actions artifacts and the available billing quota. Distinguish current bytes, billing accumulation and the separate cache allowance. Report concerns; do not delete or archive account data without fresh approval and verified private backups.
2. Review source changes, supported input limits, scientific claims, provenance, licenses and dependencies. Regenerate the code/file inventories after formatting. Do not refresh reference results merely to silence a failure.
3. Run README checks and actual browser QA. Inspect numerical/quality oracles, GeoTIFF/GeoJSON roundtrips, errors, opt-in review/preference behavior and mobile accessibility. Keep tests' warnings as errors; fix leaks rather than hiding warnings.
4. Require all **eight Validation jobs** and both **CodeQL analyses** on the exact reviewed commit. Separately query open CodeQL findings; successful analysis is not proof of no findings. Unfinished jobs/account failures are not passes.

## Draft build and publish

Manually dispatch **Portable release** on `main` with a fresh digits.digits.digits version. Preparation checks successful exact-SHA Validation and CodeQL runs and creates a **draft only**. Three OS jobs build the production web UI, package locked native geospatial dependencies/notices, execute actual frozen-app/SQL/geospatial/HTTP smoke checks and upload ZIP/checksum pairs directly to that draft. No Actions artifacts/caches are uploaded. Existing published assets are never overwritten.

Download all six new draft assets into a new task-owned directory. Compare ZIP SHA-256 with the checksum file and GitHub asset-digest metadata. Inspect ZIP CRCs and required files/notices. Execute only the newly built, reviewed downloaded Windows app—not archived Actions evidence. Test public and custom local inputs, scientific/quality gates, geospatial exports, local history and all browser flows against the downloaded service. Keep synthetic test outputs/private paths outside Git.

Record exact source SHA, completed job links/counts, coverage/audits, download digests, actual executable/browser checks and known limitations in release notes. Publish the existing draft after verification, then confirm public release/tag/main/accepted checks align. Do not claim signing, notarization, mobile installation or environmental accuracy certification.

## Operation, teardown and rollback

The server binds only `127.0.0.1`; no cloud accounts, remote fetch, AI API or telemetry. A tab can close while its server remains running: stop its own console with Ctrl+C. During development, use a task-owned port/process, check readiness, inspect the actual UI and capture an unmodified screenshot. Stop only the owned preview/test processes at teardown; do not kill broad process-name/port sets or unrelated apps.

If a release fails digest, data provenance, numerical gates or key user flows, stop distribution, identify the affected version and preserve evidence. Do not silently replace public assets. Correct source and release a new version through the same gates. Removing an extracted application after closing it does not authorize deletion of separate user exports/history. No background updater or automatic retention cleanup exists.

Local SQL/history and review files are unencrypted and user-owned. Copy them privately for backups; never upload them to GitHub issues or public releases. Larger/untrusted inputs or public deployment require a different architecture, isolation and review. Native-library and provider changes require fresh dependency/data provenance validation, not relaxed tests.
