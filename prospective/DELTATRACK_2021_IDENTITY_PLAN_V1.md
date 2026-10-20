# DELTATRACK 2021: prospective transfer of the MEDGULL shape-identity test

Locked on 2026-10-20 BEFORE opening the 2021 GPS altitude values or identity scores in this extension. This follows an explicitly post-outcome MEDGULL sensitivity; it does not rewrite that study's primary or any 2020 structural failure.

## Question and independence

Do centered flight-altitude profiles retain individual identity in a different archived tracking study and two non-MEDGULL gull species under exactly the completed D1 balanced estimator?

Source: DELTATRACK corrected v5, Zenodo DOI 10.5281/zenodo.22102508. Fixed input DELTATRACK-gps-2021.csv.gz, published MD5 1a3145234cccd1a48b280b0fb485d679. The year is selected from already-read deployment metadata, not altitude outcomes: May–July 2021 potentially includes 66 Larus fuscus and 14 Larus argentatus. These are upper bounds, not actual admissible flight cohorts. Both taxa are retained in the reporting denominator. The 2020 support-only result (6/9 eligible birds) stays unchanged. This is an external study relative to MEDGULL, not an independent replicate of every other DELTATRACK year. The two species share site, instruments and environmental context and are not two fully independent studies.

## Fixed estimand and preprocessing

- Analyze Larus argentatus and Larus fuscus separately; never use one species as the other's comparator.
- Year 2021, May–July UTC; provider outliers excluded.
- Ground speed 5–55 m/s is a flight proxy, not a validated state label.
- Retain the earliest eligible moving fix in each bird × UTC five-minute bin BEFORE numeric altitude QC. A missing earliest height never licenses taking a later height from that bin.
- EPSG:32631, 5000-m cells. Native height-above-msl in meters; finite values in [-300,3000]. Per-species valid-height fraction >=0.8.
- Each retained bird-day is centered on its own median. Ten bins: [-inf,-200,-100,-50,-25,0,25,50,100,200,inf]. This estimates within-session shape identity, not online absolute-height prediction.
- D1 donors: all nonempty valid-height days. Evaluation: >=50 scorable five-minute records/day and >=2 evaluation days/bird. At least 10 eligible biological individuals per species for inferential reporting.
- Donors exclude the evaluation calendar date for both the focal bird and other birds. A target cell requires >=10 own-other-day and >=10 other-individual-other-day records. One common kernel computes support AND values.
- Primary estimator: completed MEDGULL D1 balanced implementation, unchanged. Smooth each donor-day/cell with Jeffreys 0.5/bin, average days equally within each bird, average other birds equally, evaluate identical target records for self and other; aggregate days equally then birds equally.
- Pooled-record estimate is descriptive sensitivity only; no third/fourth search for a favorable primary. D50 remains a support/score diagnostic, not a substitute endpoint.

## Fixed calibration

999 whole-session identity permutations within exact UTC date, seed 20261021 independently per taxon. Each session's x-y and centered z histogram moves intact. Individual date-presence sets and number of sessions are preserved. Recompute support in every draw.

Unavailable draws are never silently dropped: report the full tail p interval [(1+b)/(1000),(1+b+unavailable)/(1000)]. Require >=950 valid draws and observed >=10 eligible birds. Holm correction over the TWO prespecified taxon tests, with unavailable taxa assigned p=1. Support requires positive observed-minus-valid-null-mean and Holm upper p<0.05. Failing data/null gates is unavailable, not a biological null.

The exact-date exchangeability assumption remains a substantive observational assumption; preserving dates does not eliminate horizontal-route, effort or tag-specific confounding. Report observed and permuted eligible-bird ranges.

## Required outputs and boundaries

Save source MD5/SHA256, code hash, per-species counts, all bird scores, all 999 null draws, admission counts, full p interval and Holm upper p, plus short outcome report. Preserve unfavorable and unavailable species.

Even a positive result supports only individual-label-associated cross-day centered altitude shape under this sampling/null design. It does NOT prove adaptive specialization, resource partitioning, central-place causation, instrument-error-free biological identity, or universal mammal/bird convergence. A negative or unavailable result is retained without changing year, donor rule, grid, bins, speed or minimum sample size.

## Execution and testing

Reuse prospective/medgull_sensitivity.py from the completed sensitivity branch without editing its numerical kernel. Add only a source-specific adapter and runner. Before real 2021 data run: synthetic tests verify species separation, pre-QC thinning, altitude zero-offset invariance, single-bird exclusion, source hash guard, and equality of preflight/scoring support. Run existing MEDGULL module tests and the new adapter tests. Preserve the known historical repository-wide submission-readiness failures rather than claiming a green entire repository.
