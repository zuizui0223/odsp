# Cross-taxon biological generality — current state

Updated 2026-10-20. Active objective: make sampling-support checks identical to the actual self-versus-other comparison before extending biological claims.

## Completed and verified

DELTATRACK 2020 structural run 39219324200 completed: 6 L. argentatus and 9 L. fuscus under the unchanged minimum-10 rule. No altitude individuality test was opened for DELTATRACK.

Diagnostic run 39369189157 processed 2,369,570 GPS rows from three already-used immutable files without reading altitude. Five new regression tests passed locally and on GitHub. All three diagnostic data jobs succeeded. Implementation SHA: 6b8608904ad75cd313dbd39f687b311230dcb16a.

## Correction to previous interpretation

The earlier explanation in ACTUAL_EVIDENCE_STATUS_2026-10-19.md attributing MEDGULL's 13-to-9 change to same-date exclusion is incorrect.

Measured MEDGULL 2022 decomposition:

- Legacy structural screen: 13 animals / 290 days.
- Correct other-individual Counter key: 11 / 258.
- Exclude same-date other birds: still 11 / 258.
- Remove short (<50-bin) donor days as the biological loader does: 9 / 241.

The legacy screen stored counts by (individual, cell) but subtracted a nonexistent individual-only key. Thus it failed to subtract the focal individual's records. The new diagnostic uses the correct key and retains the legacy formula solely for comparison.

Short-donor-day removal is a separate modelling choice, not automatically a bug. Its absence from the preflight caused an additional support mismatch. Frozen legacy files remain provenance, not the recommended implementation for new admission.

## Measured support (numbers of animals)

| Panel | Flight IDs | >=2 days of >=50 bins | Correct shared-cell support | With short donor days removed |
|---|---:|---:|---:|---:|
| MEDGULL 2022 | 14 | 14 | 11 | 9 |
| LBBG Schiermonnikoog 2018 | 21 | 11 | 6 | 4 |
| DELTATRACK 2020 L. argentatus | 25 | 11 | 6 | 3 |
| DELTATRACK 2020 L. fuscus | 25 | 24 | 9 | 7 |

These are structural diagnostics, not new ecological outcomes. The last column applies the MEDGULL donor-day rule diagnostically; it does not change DELTATRACK's original endpoint. DELTATRACK's original code did not contain the Counter-key bug, and its 6/9 result was reproduced.

## Verification closeout

The full default repository test suite completed: 1,514 passed, 2 failed, 1 skipped (counts from the preserved pytest progress output). Both failures were reproduced on the unchanged parent 199501251d2c49b73569f491816a45bc98f380c7 in run 39370203022. They predate this diagnostic work:

1. test_final_receipt_rebuilds_manuscript_and_anonymous_bundle — historical anonymous-review ZIP hash differs from its frozen receipt.
2. test_closed_empirical_workflows_are_path_filtered — historical readiness test expects paths: in a closed empirical workflow.

No closed empirical workflow was re-enabled. These submission-package checks remain unresolved and are separate from the successful new regression and data diagnostics. Do not claim all repository tests pass.

## Scientific boundary and next execution target

Original MEDGULL n=9 remains closed as unavailable under its original design. Its uncalibrated score is not a supported ecological negative. Corrected structural n=11 is not successful independent biological replication. The minimum-10 threshold is a design gate, not a mathematical prohibition on inference with nine individuals.

Next: explicitly separate donor-day and evaluation-day requirements; fix individual/session weighting; ensure the same support function is used in both preflight and the scorer. Validate that design on synthetic data before further ecological outcomes. Applying changed donor rules to already-viewed MEDGULL is post-outcome sensitivity, not a fresh confirmatory experiment. Do not keep searching species solely to obtain a pass.

The question of whether bat vertical individuality is taxonomically general remains open. Shared-space selection cannot itself establish absence of ecological individuality in excluded birds.

## Durable evidence

Branch: diagnostic/gull-support-20261020

- prospective/GULL_SUPPORT_DIAGNOSTIC_2026-10-20.md — detailed diagnosis; its original test-progress paragraph is superseded by the final verification below.
- prospective/GULL_SUPPORT_DIAGNOSTIC_RESULT_V1.json — data counts and source hashes.
- prospective/GULL_SUPPORT_VERIFICATION_FINAL_V1.json — completed tests and parent reproduction.
- prospective/gull_support_diagnostic_v1.py — corrected diagnostic implementation.
- prospective/test_gull_support_diagnostic_v1.py — regression tests.

Report: https://github.com/zuizui0223/odsp/blob/diagnostic/gull-support-20261020/prospective/GULL_SUPPORT_DIAGNOSTIC_2026-10-20.md
Final verification: https://github.com/zuizui0223/odsp/blob/diagnostic/gull-support-20261020/prospective/GULL_SUPPORT_VERIFICATION_FINAL_V1.json
