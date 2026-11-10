# Reviewed Office package boundary — November 10, 2026

The development-time publication reader now rejects any member whose path contains `/embeddings/`, case-insensitively, alongside its existing macro-member rejection. This covers both reviewed Word editions and the reviewed Excel evidence workbook. The reader retains its single opened descriptor, compressed/member/expansion budgets, strict XML/relationship decoding and unknown-file rejection. No Office content is executed.

Four independent real-ZIP regressions exercise a macro member, a Word embedded object, mixed-case embedded paths and an Excel embedded object. The previous named-edition, malformed-package, UTF-8 and expansion cases remain. Approved published Office documents contain no such payload; their exact bytes, manifests and historical validation baselines remain unchanged.

This is a source-maintenance/privacy boundary change. It does not change the simulation, application runtime, installed user data, version or released portable archives. Full original local gates and fresh hosted PR/main validation remain required; actual results are recorded below after execution.

## Actual local validation

1103 Python tests passed with 99.74% combined runtime statement/branch coverage, retaining the existing coverage floor. This includes all twelve actual-ZIP publication-reader cases. 12 TypeScript tests, strict Python/TypeScript types, Ruff/format and production UI build also passed. Existing security/coverage gates are unchanged. Generated source/file indexes and full repository formatting were checked after this report was added. Fresh hosted PR/main checks remain separate and required.
