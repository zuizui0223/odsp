# MEDGULL donor-day sensitivity v1

2026-10-20. Status: POST-OUTCOME SENSITIVITY, not preregistration, not a new independent replication. The source and original n=9 result have already been examined. Original primary eligibility and inferential status remain unchanged.

## Purpose

Determine whether retaining short training days changes the descriptive repeatability of centered flight-altitude shape, and whether donor weighting drives the result. Stop searching for more species merely to pass an arbitrary sample-size gate.

## Fixed source and preprocessing

Use only MEDGULL_ANTWERPEN-gps-2022.csv.gz from Zenodo 15685037. MD5 aea4ac8900f553e105e797e0553d84e7; SHA256 ab2949f0fd09b3fe938ad3aea1bcba0fe897fd39d501b30d9480de5aa601c3f3. Retain original May-July UTC window, provider-outlier exclusion, source speed 5-55 m/s, earliest eligible fix per bird/UTC-five-minute-bin, EPSG:32631 5-km cells, finite native MSL height -300 to 3000 m. No replacement of a selected bin whose height fails QC.

All valid days receive their own median subtraction. Original ten bins: -inf,-200,-100,-50,-25,0,25,50,100,200,inf. Centering uses the test day's own median: this is shape matching, NOT online absolute-altitude forecasting. Short-day medians are noisy; this is specifically a sensitivity, not an assertion that including them is superior.

## Finite comparison family

Two donor policies: D50 retains only days with >=50 valid five-minute bins; D1 retains every day with at least one valid bin. Evaluation always requires >=50 scored bins/day and >=2 scored days/bird. A target cell always needs >=10 same-bird other-day donor events and >=10 other-bird other-date donor events. Source support is recomputed by the exact same function used by the scorer.

Two weighting policies:
- pooled: aggregate donor events within each reference, with Jeffreys 0.5/bin. D50 pooled must reproduce original 9 birds, 241 days and -0.014494591842618162 mean gain within numerical tolerance.
- balanced: smooth each observed donor-day/cell profile with 0.5/bin, average days equally within each donor bird, then average other donor birds equally. This changes both weighting and the level at which smoothing is applied; do not claim it isolates weights alone. Missing bird/cell profiles are not filled with uniform prior-only birds.

Report all four descriptive estimates and per-bird/day counts. Average target fixes within day, days within bird, then birds equally. D50 rows remain descriptive because the original minimum-10 gate was not met. Do not lower it.

## Exploratory calibration for the two D1 variants

Use 999 independent uniformly sampled permutations of whole bird-day sessions WITHIN EACH EXACT UTC DATE, seed 20261020. This preserves each bird's date-presence schedule and bird/month session counts, keeps within-session x-y-height structure intact, and avoids approximate swap-chain mixing. It is a NEW, more time-restricted exploratory null, not the original month-restricted primary null. Same-date sessions never train their own evaluation date.

Recalculate support and the complete statistic for every permutation. Require observed >=10 eligible birds and at least 950/999 null draws with >=10 birds; otherwise calibration unavailable. Never silently discard unavailable draws: report a p-value interval with denominator 1000, treating unusable null draws as non-exceedances for the lower bound and exceedances for the upper bound. Use the upper bound for interpretation. Apply Holm adjustment across the two D1 exploratory contrasts. Null means/excess gains are descriptive calibration quantities, not mutual information or causal effects.

Exchangeability within date is an assumption and does not remove individual-specific sensor variance, fine-scale horizontal fidelity, age/sex or unmeasured behavioral-state differences. Label null rejection cannot uniquely identify behavioral individuality.

## Verification and execution

1. Write failing synthetic tests for unified support, self-exclusion, donor/evaluation separation and weighting.
2. Verify deterministic synthetic persistent-shape and no-identity fixtures, exact within-date permutation constraints and additive-shift invariance.
3. Validate the original D50 pooled estimate against the archived result, without changing its terminal status.
4. Run the fixed four-row comparison, both D1 nulls and save complete randomization summaries, per-bird values, code hashes and source hashes.
5. Report actual biological implications and limitations. No threshold/bin/year retuning after seeing these outcomes. Save results and executable code; do not describe checks alone as biological progress.

No new central-place, resource-partitioning or cross-taxon universality claim follows from this single already-examined species.
