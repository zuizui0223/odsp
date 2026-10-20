# Cross-taxon biological generality — current state

Updated 2026-10-20. The support diagnosis and the bounded MEDGULL donor-day sensitivity are COMPLETE. The original primary test remains closed; new results are explicitly post-outcome sensitivity, not independent confirmation.

## Latest completed ecological result

Branch: `sensitivity/medgull-donor-days-20261020`.

MEDGULL 2022, Ichthyaetus melanocephalus, Zenodo 15685037, original pinned GPS source. Retaining short days for training while preserving >=50 scored records/evaluation day and >=2 evaluation days/bird gives **11 birds, 258 bird-days, 17,054 scored five-minute flight records**.

| Reference | Observed log-score gain | Exact-date permutation mean | Observed minus null mean | Holm p (two sensitivity contrasts) |
|---|---:|---:|---:|---:|
| Pooled donor records | -0.0296285 | -0.0945509 | +0.0649224 | 0.002 |
| Equal donor days within bird, equal other birds | +0.0362684 | -0.0167478 | +0.0530162 | 0.002 |

Both use 999/999 valid whole-session permutations within exact UTC dates; no unavailable draws discarded. Raw sign is not the inferential reference: even the negative pooled gain exceeds its procedure-specific null. In the balanced variant 10/11 individual point scores are positive, NOT 10 separately significant individual tests.

The balanced variant also smooths each day/cell before averaging; it differs in smoothing level as well as weighting. Do not assign the raw sign change to weights alone.

## What was and was not established

Supported within this exploratory design: identity-matched, within-day-median-centered altitude profiles retain more cross-day correspondence than exact-date relabeling in one already-examined nonbat species.

Not established: independent replication, universal cross-taxon individuality, adaptive resource partitioning, central-place causation, or separation of biological identity from tag-specific non-additive errors, sampling effort and unobserved behavioral/context differences. The date-exchangeability assumption is substantive. Holm adjustment covers only the two stated sensitivity comparisons, not the whole historical sequence of exploratory decisions.

This is shape matching, not online absolute-height prediction: heldout sessions supply their own centering median. Short training-day medians can be noisy. New n=11 eligibility does NOT rescue the original n=9 primary.

## Reproduction and verification

Original D50 pooled result reproduced exactly within numerical tolerance: **9 birds, 241 days, 15,904 records, mean gain -0.014494591842618162**. D50 balanced is +0.0555508 but remains descriptive.

New module tests: 10/10 passed locally. Independent dictionary/NumPy recomputation agrees for every bird in all four variants, maximum absolute difference 5.56e-17. Published script blob matches the executed local script: `eb0069c98218ae097a9b1310c8556d3258cc1c07`.

The existing whole-repository suite was not rerun for this standalone sensitivity. The two historical submission-readiness failures from run 39369189157 were previously reproduced on the unchanged parent in run 39370203022 and remain unresolved. Do not claim all repository tests are green.

## Durable latest evidence

On the sensitivity branch:
- `prospective/MEDGULL_DONOR_SENSITIVITY_PLAN_V1.md` — post-outcome plan fixed before this calculation; commit cdc516f04bef29be3f5a786ee78916fea90d104d.
- `prospective/medgull_sensitivity.py` — unified support/scoring and exact-date null implementation.
- `prospective/test_medgull_sensitivity.py` — synthetic and optional pinned-source integration tests.
- `prospective/MEDGULL_DONOR_SENSITIVITY_RESULT_V1.json` — results, provenance, source and complete-output hashes.
- `prospective/MEDGULL_DONOR_SENSITIVITY_REPORT_V1.md` — Japanese ecological interpretation and limitations.

Complete per-bird scores, all 999 null draws, processed session arrays and independent validation code are included in the conversation's reproducibility package.

## Preserved diagnosis and closed endpoints

MEDGULL's earlier 13-to-9 drop was NOT caused by same-date exclusion:
13 -> 11 after correcting the Counter (individual, cell) key;
11 -> 11 after excluding same-date donors;
11 -> 9 after removing short donor days.

DELTATRACK 2020 remains structurally below its unchanged minimum-10 rule: L. argentatus 6, L. fuscus 9. Its original code did not have the Counter-key defect. Schiermonnikoog 2018 had 6 with correct shared-cell matching, 4 after short-donor removal. These are sampling-support findings, not ecological negatives.

The next scientific boundary is measurement/context confounding and genuinely independent nonbat confirmation, not another threshold change to the already-viewed MEDGULL sample. Bat movement individuality and MINA breeding-component concentration remain different response variables and must not be pooled into one claimed law.
