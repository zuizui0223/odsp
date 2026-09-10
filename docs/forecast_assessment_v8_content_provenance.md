# Forecast Assessment v8: exact-content provenance gate

Forecast Assessment v8 composes the frozen Forecast Assessment v7 path with the independently validated exact-content provenance audit.

The caller may provide one SHA-256 digest for the final evaluation artifact and a stage-indexed ledger of SHA-256 digests consulted before the final evaluation. If the final digest appears in any declared pre-final stage, v8 reports `final_evaluation_content_leakage` and does not run the full downstream v7 path. This prevents a byte-identical copy from bypassing the artifact-ID gate merely because it was assigned another identifier.

The execution order is therefore:

1. exact-content provenance;
2. artifact-ID access provenance;
3. selection/final-validation provenance;
4. per-refit training/final-validation provenance;
5. held-out row alignment;
6. refit-scheme statistical sensitivity.

A selection-, artifact-access- and scheme-omitted v7 result remains available as base evidence. Content leakage is a provenance blocker, not statistical uncertainty, and does not manufacture downstream statistical failure reasons.

If content provenance is omitted, ordinary v7 behavior is preserved. If the supplied digest ledger is clean, v8 delegates to v7 unchanged and inherits its certification, operational status, provenance blockers, statistical blockers and warnings.

## Scope boundary

The content audit only compares caller-supplied SHA-256 digests. It does not hash files automatically and does not infer a complete access history. A clean ledger cannot rule out re-encoded, reformatted, cropped, screenshot, transcribed, summarized or otherwise semantically equivalent versions whose bytes differ. It also does not prove genuine predeclaration, identify the correct model, add a statistical estimand, identify biological mechanism, or guarantee future distribution-shift performance.

The frozen Forecast Assessment v7 contract, frozen N2-MEE v4 submission artifacts and closed empirical endpoints are not rewritten or reopened.
