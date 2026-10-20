# Cross-taxon biological generality — current state

Updated 2026-10-20. One active objective: reconcile sampling support with the actual self-versus-other comparison before extending biological claims.

## Completed

The pending DELTATRACK 2020 structural run 39219324200 succeeded operationally but admitted only 6 L. argentatus and 9 L. fuscus under its unchanged minimum-10 rule. It did not test altitude individuality.

A root-cause diagnostic on branch `diagnostic/gull-support-20261020` processed 2,369,570 GPS rows from three already-used immutable files without reading altitude. Five new regression tests passed locally and on GitHub. All three diagnostic data jobs succeeded (run 39369189157; implementation SHA 6b8608904ad75cd313dbd39f687b311230dcb16a).

## Correction to the previous status note

The earlier explanation in ACTUAL_EVIDENCE_STATUS_2026-10-19.md attributing MEDGULL's 13-to-9 change to excluding other birds on the same date is incorrect.

Measured decomposition for MEDGULL 2022:

- Legacy structural screen: 13 animals / 290 days.
- Correct the other-individual Counter key: 11 / 258.
- Exclude same-date other birds: still 11 / 258.
- Remove short (<50-bin) donor days as the biological loader does: 9 / 241.

The legacy screen stored counts by (individual, cell) but subtracted a nonexistent individual-only key, so it failed to remove the focal individual's records. The corrected diagnostic uses the proper key. The frozen legacy files remain provenance, not a recommended implementation for new admission.

Short-donor-day removal is a separate modelling choice, not automatically a software bug. Its omission from the structural check caused additional admission mismatch.

## Current source support

| Panel | Flight IDs | >=2 days of >=50 bins | Correct shared-cell IDs | With short donor days removed |
|---|---:|---:|---:|---:|
| MEDGULL 2022 | 14 | 14 | 11 | 9 |
| LBBG Schiermonnikoog 2018 | 21 | 11 | 6 | 4 |
| DELTATRACK 2020 L. argentatus | 25 | 11 | 6 | 3 |
| DELTATRACK 2020 L. fuscus | 25 | 24 | 9 | 7 |

All values are structural diagnostics, not vertical biological outcomes. The original DELTATRACK code did not have the Counter-key bug; its 6/9 result is reproduced.

## Claim boundary

The original MEDGULL n=9 biological endpoint stays closed as unavailable under its original design. Do not treat its uncalibrated score as an ecological negative. Do not relabel corrected structural support n=11 as successful independent biological replication. The test has not established whether bat vertical individuality is taxonomically general.

## Next execution target

Unify donor/evaluation support checks with the actual scorer. Explicitly separate requirements for evaluation days from requirements for donor days and specify individual/session weighting. Validate this design on synthetic data before additional ecological outcomes. Applying changed donor rules to already-viewed MEDGULL is a post-outcome sensitivity, not a fresh confirmatory experiment. Do not restart species hunting or relax the old minimum-10 gate merely to obtain a pass.

## Durable evidence

Detailed Japanese report and machine-readable receipt live on the diagnostic branch:

- prospective/GULL_SUPPORT_DIAGNOSTIC_2026-10-20.md
- prospective/GULL_SUPPORT_DIAGNOSTIC_RESULT_V1.json
- prospective/gull_support_diagnostic_v1.py
- prospective/test_gull_support_diagnostic_v1.py

Report: https://github.com/zuizui0223/odsp/blob/diagnostic/gull-support-20261020/prospective/GULL_SUPPORT_DIAGNOSTIC_2026-10-20.md

Receipt: https://github.com/zuizui0223/odsp/blob/diagnostic/gull-support-20261020/prospective/GULL_SUPPORT_DIAGNOSTIC_RESULT_V1.json

The default repository-wide test suite was still running when this status was written. No all-suite-pass claim is made.
