# Swiss red-kite 2022: exact four-negative rank resolution and majority benchmark

## Status: deterministic source-free audit of an already inspected cohort

Merged [PR #298](https://github.com/zuizui0223/odsp/pull/298) scored **96 fixed R `ranger` forests** at predeclared 2020/2021/2022 calendar cutoffs. Training years strictly preceded testing years, and the bird-purged arm shared **zero source bird-ID strings** across training and testing. The 2020 and primary 2021 panels retained strong within-source ranking performance. The 2022 panels instead had AUCs below 0.5, despite high apparent accuracy. Critically, there were only **32 test seasons / 32 source bird IDs, with 28 positives and just 4 negatives for each of HR and nest**.

This analysis is explicitly **a source-free interpretation diagnostic, not a new model or observation**. The original #298 first-results JSON, ZIP/member SHA256 hashes, outputs and historical BOP status are unchanged; no original prepared RDS, labels, model predictions, individual/year IDs or GPS are opened. The exact method/output contract was separately frozen at **`9e335670c28f49f3fc5f52d9495d159daa263916`** in `research/BOP_SWISS_2022_RANK_RESOLUTION_V1_CONTRACT.json`.

## Finite rank resolution conditional on 28 positive and 4 negative test records

A single model's empirical ROC AUC is defined by the **28×4 = 112 positive–negative rank comparisons**. If all score ranks are distinct, its AUC lies on increments of **1/112 ≈ 0.008929**. Moving **one** of the four negative observations from below all positives to above all positives can shift AUC by as much as **28/112 = 0.25**. Therefore a small test set may be extremely sensitive to just one negative observation.

We calculate a *tie-free random-ranking reference*, conditional on the fixed class composition, by enumerating **all C(32,4) = 35,960 placements** of the four negative-class labels in the 32 possible score ranks. For negative ranks (0le r_1<r_2<r_3<r_4<32), the positive–negative win statistic is (U=4(31)-sum_i r_i-6), and AUC is (U/112). This is an exact distribution under **hypothetical exchangeable, tie-free random score ranking**; it is **not** an exact inferential p-value for the actual eight-forest mean AUC or its potentially tied RF probability scores. The eight forest runs reused **identical test data**, not eight biological replications.

| Exact hypothetical random-ranking reference | AUC interval |
|---|---:|
| Central 90% (discrete nearest-rank quantiles) | **0.2411–0.7589** |
| Central 95% (discrete nearest-rank quantiles) | **0.1964–0.8036** |

The observed 2022 model means from the locked #298 receipt, considered only as **descriptive thresholds within that random-rank reference**, are:

| 2022 outcome | Old-data training | Published-source mean AUC (8 RF seeds) | Tie-free random-rank lower-tail fraction at threshold* |
|---|---|---:|---:|
| Home range | All older bird years | 0.415736 | 0.300779 |
| Home range | Older bird years **purged of test birds** | **0.373884** | **0.211819** |
| Nesting | All older bird years | 0.320312 | 0.126863 |
| Nesting | Older bird years **purged of test birds** | **0.313616** | **0.126863** |

*These fractions are **not calibrated significance tests for averaged model outputs**. The model predictions may have ties, all eight forests are correlated through reuse of the same test records, and the 2022 discrepancy was noticed before choosing this audit. They are presented solely as a transparent diagnostic conditional reference.*

## Accuracy versus a majority-class benchmark

With **28/32 = 87.5% positives**, an oracle that knows the **test-period class prevalence** and always guesses positive gets **87.5% accuracy** without using any movement feature. In the bird-purged 2022 source models, home-range mean accuracy is **87.5%** (no better than this trivial class-majority rule), while nesting mean accuracy is **75.0%** (worse by **12.5 percentage points**). The 2022 source-home-range log-score gain relative to the *valid training-only prevalence baseline* is **−0.609657**, while nesting retains **+0.184597**. Distinguish these two baselines: the majority rule based on **observed test labels is an in-sample diagnostic, not a deployable forecast baseline**; the training-only prevalence log-score reference was correctly computed without test-label leakage by the original #298 analysis.

The audit emits this test-majority diagnostic for **all twelve predeclared year×response×training-mode panels**, not just the anomalous 2022 cases. Thus the high 2020/2021 accuracy can be judged against their separate observed class proportions rather than being naively compared to 2022.

## Bounded conclusion

The 2022 AUC reversal is a **real numerical finding of the fixed original source models**, but **its mechanism remains unidentifiable from 32 birds and four negatives**. It may reflect tiny negative-class support, covariate differences, ecological variation or model transfer instability. We do **not** infer a regime shift, individual identity mechanism or selection on score direction. The exact tie-free rank reference is not a confidence interval for the ecological effect, and cannot establish whether the true AUC is below 0.5; it does explain why the observed aggregate should not be overinterpreted.

Original BOP `empirical_state_prediction_mixed`, red-kite new external group `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`, and original Dryad `NOT_ADMITTED` remain unchanged.

## Reproduction

```bash
python -m pytest tests/test_bop_swiss_2022_rank_resolution_v1.py
python scripts/bop_swiss_2022_rank_resolution_v1.py --out /tmp/bop-swiss-2022-rank-reference.json
```

Run uses **only** the merged original Swiss 96-model aggregate receipt from PR #298. No new external download or provider authentication is required.
