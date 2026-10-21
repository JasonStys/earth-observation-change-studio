# Security policy

Created by Jason Stys. This is a local-only civilian environmental review application. It is not an authenticated hosted platform, malicious-file sandbox, operational surveillance service or automated event-decision system.

## Boundaries

The HTTP service binds IPv4 loopback only, checks exact Host and relevant Origin/Fetch Metadata, offers no CORS allowance, confines static paths and exposes no upload/mutation/database-write APIs. Queries and decoded arrays are bounded. CSP blocks external scripts/resources, frames, plugins and external connections; labels/static HTML are escaped. Browser reports are shape-checked before canvas allocation. There are no advertisements, analytics, accounts, cookies, external fonts, satellite API calls or AI providers in the runtime.

CLI local imagery is limited to a narrow manifest, simple same-directory filenames, fixed GTiff driver, dimensions, bands, UTM CRSs, dates and byte identities. Sidecar discovery is disabled. These checks do **not** sandbox GDAL/native TIFF parsing or protect against every malformed-file exploit. Process only reviewed/trusted files; there is no arbitrary internet/user upload feature. Keep native dependencies patched and rerun audits/tests when changing locks. The explicit acquisition developer tool uses fixed public HTTPS sources with TLS validation intact, and never runs automatically in the app/tests/releases.

Review dispositions/notes remain in tab memory until explicit local JSON download, and clear on new analysis. Optional browser storage contains finite controls only and is removable. SQL history uses bound parameters, transactions, verified hashes and immutable triggers, but is **unencrypted**. Other OS users, administrators, backup software and browser extensions with relevant access are outside this application's privacy boundary. There is no operator receiving local imagery or notes.

Workflows use pinned actions, least-privilege tokens and no persisted checkout credentials or secret-dependent PR execution. No Actions artifact/cache upload. Manual release packaging requires successful exact-commit checks; publication follows independent download/digest review. No signing/notarization is claimed. Verify checksums and respect OS policy; never disable protection to run the app.

The loopback development service is not designed to withstand malicious local administrators or unlimited local concurrent requests. Public reverse proxies, tenant accounts, hardware connections and automatic environmental alerts are outside supported use. Scalar/vector agreement and synthetic scores verify software, not real-world event truth or geolocation accuracy.

## Reporting

Use private vulnerability reporting if the repository offers it, or contact [Jason Stys through the profile](https://github.com/JasonStys) to arrange a private channel. Public issues should include only synthetic reproductions, affected version and non-sensitive diagnostics. Never include personal information, private imagery, credentials or local history/review files. A report does not authorize testing unrelated systems.
