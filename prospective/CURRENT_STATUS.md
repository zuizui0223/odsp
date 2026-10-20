# Cross-taxon biological generality — current state

Updated 2026-10-20. Latest completed step: a prospectively fixed external tracking-study test in DELTATRACK 2021. Prior MEDGULL exploratory results and unavailable original endpoints remain unchanged.

## Latest external-study result

Branch: `prospective/deltatrack-2021-identity-20261020`.

Using the unchanged MEDGULL D1 balanced estimator, **Larus fuscus: 40 individuals, 899 bird-days and 66,811 scored five-minute flight records** retain individual-label-associated cross-day centered altitude shape beyond exact-date session relabeling.

- Observed mean log-score gain: +0.0456739261.
- Null mean: -0.0278862764.
- Observed minus null: +0.0735602025 nats/record.
- 999/999 valid permutations; none at least as large as observed.
- One-sided Monte Carlo p=0.001; Holm p=0.002 across the TWO prespecified species.
- 37/40 positive individual point scores, not 37 significant individual tests.
- Null eligible birds 49–59 versus observed 40; full support re-estimation and this difference are retained.

Larus argentatus: 14 individuals had valid flight heights but only 1 individual / 7 bird-days / 449 records passed the full comparison support. Its endpoint is **unavailable**, not a negative biological result. It stays in the multiplicity family with placeholder p=1; no biological p-value is reported.

The dataset is an external study relative to MEDGULL, not an independent study for each DELTATRACK year. The two species share site/instrument context. The supported external result is one species, not two successful independent species.

## Frozen design and execution

Source DOI 10.5281/zenodo.22102508; DELTATRACK-gps-2021.csv.gz; MD5 1a3145234cccd1a48b280b0fb485d679. Target two-species raw count 3,637,037; valid thinned height count 216,407.

Plan saved before this 2021 height analysis: commit abd6416013cf8aedf0acff9b91782964ce947228. Successful run 39375585874, execution commit 089194d368ca43554d3ea681d008d01e5ce51008, artifact 12242743398.

First attempt failed at Numba cache loading after parsing heights but before emitting an identity statistic. The error was reproduced with synthetic data; only the production cache directory was separated. No year, model, threshold, seed, source or numerical kernel changed.

Durable report and receipt on the external-test branch:
- prospective/DELTATRACK_2021_IDENTITY_REPORT_V1.md
- prospective/DELTATRACK_2021_IDENTITY_RECEIPT_V1.json
- prospective/DELTATRACK_2021_IDENTITY_PLAN_V1.md
- prospective/DELTATRACK_2021_RUNTIME_RECOVERY_V1.json
- prospective/deltatrack_2021_identity.py
- prospective/test_deltatrack_2021_identity.py

The complete result JSON, all 999 null draws, all per-bird comparisons and executable code are saved in the verified run artifact and the conversation reproducibility package.

## Interpretation and remaining scientific boundary

Evidence now extends from the post-outcome MEDGULL discovery to a pre-specified test in a different gull study/species. The safest claim concerns **individual-label-associated vertical-use shape**, not biological personality or adaptive specialization free from instrumentation.

Tag-specific non-additive altitude errors, effort, unobserved behavioral mixtures, within-cell routes and the substantive exact-date exchangeability assumption remain limitations. Day medians use the heldout session itself; this is shape matching, not online absolute-height prediction. Do not compare raw calibrated-score magnitudes as directly comparable biological strengths across datasets.

No inference of resource partitioning, central-place causation or universal mammal–bird equivalence. MINA penguin breeding-component concentration is a different response variable; do not combine the two into one demonstrated law.

Next scientific boundary: measurement/context attribution and extension beyond a narrow colonial-flying comparison. Do not continue changing thresholds on already-viewed MEDGULL or treat the excluded L. argentatus panel as a biological negative.

## Preserved MEDGULL sensitivity

Branch sensitivity/medgull-donor-days-20261020. MEDGULL 2022 I. melanocephalus: 11 birds, 258 bird-days, 17,054 records under D1. D1 pooled observed -0.0296285 vs null -0.0945509; D1 balanced +0.0362684 vs null -0.0167478. Both Holm p=0.002 across those two exploratory comparisons. This remains post-outcome sensitivity, not an independent confirmation. Balanced uses different smoothing level as well as weighting.

Original D50 pooled reproduced: 9 birds, 241 days, 15,904 records, gain -0.014494591842618162. Its original minimum-10 primary stays closed as unavailable.

## Preserved structural diagnosis

MEDGULL 13 -> 11 after correcting the individual/cell Counter key; 11 -> 11 after same-date exclusion; 11 -> 9 after removing short donor days. Earlier attribution solely to same-date exclusion was wrong.

DELTATRACK 2020 stays below its original minimum-10 rule: L. argentatus 6, L. fuscus 9. Its code did not have the Counter-key defect. Schiermonnikoog 2018 had 6 correct shared-cell candidates, 4 after short-donor-day removal. These are support findings, not ecological negatives.

## Verification closeout

New and reused module tests: 15 passed, 1 optional source integration test skipped. Independent dictionary reference agrees in 96 irregular synthetic cases; max score difference 6.67e-16. Saved real-data individual aggregates, full null means/tail counts/p values and Holm adjustment rechecked independently; artifact file hashes verified.

Full default repository suite rerun in 39374955129: 1,514 passed, 2 failed, 1 skipped, 0 errors. The two unresolved historical failures are test_final_receipt_rebuilds_manuscript_and_anonymous_bundle and test_closed_empirical_workflows_are_path_filtered. They had previously been reproduced on the unchanged parent. Scientific job success does not mean the entire repository suite is green.
