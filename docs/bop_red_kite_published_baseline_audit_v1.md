# Red kite: class prevalence is not future-bird prediction gain

**Audit status:** postpublication arithmetic on already published group totals. No new source CSV rows, GPS coordinates, individual ID strings, breeding outcomes or model predictions were downloaded, opened or scored in this analysis.

**Source:** Oppel et al., *Journal of Avian Biology*, first published 17 October 2024, https://doi.org/10.1111/jav.03246, and official Zenodo https://doi.org/10.5281/zenodo.13736049. Source metadata (merged PR #283) and first-line column headers (merged PR #284, commit 5212c4cf2eae348559e94e9ca0cf3ae30fc633e1) were separately frozen and are left unchanged.

## Recomputed published class-prevalence reference

| German reproductive target | Public positive count | Population context | NestTool accuracy reported by paper | Post-hoc majority accuracy | Illustrative gap (pp) |
|---|---:|---|---:|---:|---:|
| Home range | 98 | 99 eligible individual-seasons | 96.0% | 98/99 = 98.99% | -2.99 |
| Nest attempt | 89 | 99 eligible individual-seasons | 84.8% | 89/99 = 89.90% | -5.10 |
| Fledging success | 55 | 89 reported attempts | 84.7% | 55/89 = 61.80% | +22.90* |

*The exact outcome-scored denominator for the paper's 84.7% success accuracy has not been independently reconciled with the original source rows. Its arithmetic difference is illustrative, not a paired model-comparison estimate.

The all-German majority rule is calculated **after** seeing the original paper's labels. It is an **oracle reference**, not a training-only predictor or valid independent test baseline. In particular, the two negative illustrative gaps do **not** prove inferior probabilistic forecasting: threshold accuracy differs from log score and Brier score, and the baseline was not genuinely out-of-sample.

Nevertheless this exposes a real question for ODSP: high classification accuracy can coincide with negligible or misleading evidence of added ecological information when almost every selected individual season is in the same class. Source-independent evaluation must use actual class probabilities and a defensible training-only or disjoint target-adaptation reference.

The same paper reports 99 eligible seasons from **63 biological birds** and two German populations; repeated seasons for one bird are **not independent groups**. NestTool originally trained its models on 258 Swiss birds (697 seasons) and already evaluated German nesting outcomes. Red-kite outcomes are therefore not a novel unstudied external ecological discovery for ODSP.

## Next admissible biological analysis

1. Define the biological target in advance: nest attempt (yes/no) and fledging success conditional on an attempt are different binary tasks; do not label non-attempting seasons as nest failures.
2. Obtain a source-only canonical bird-by-year and German study-population identity roster with no label values. All seasons for one bird must remain in a single partition, and repeated tags must be resolved.
3. Before any individual outcome access, freeze a source-native, reproducible Swiss training model and its reference, a disjoint German target-adaptation/calibration/validation split, and an exact score-roster denominator. The original BOP altitude random forest is not transferable to nesting-state labels.
4. Require at least 9 individual calibration birds and at least one different test bird in a biologically defensible target stratum to compute a non-vacuous nominal 90% rank lower bound. Two German source populations alone do not establish across-population exchangeability.
5. Report bird-mean log-score and Brier improvement, holdout probabilities and group identity provenance separately from threshold accuracy. A completed source-only analysis is still not a real future-bird gain result.

**Unchanged terminal:** BOP altitude state = empirical_state_prediction_mixed; red-kite biological future-animal gain = HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER.

## Offline reproduction

Run: python -m pytest tests/test_bop_red_kite_published_baseline_audit_v1.py
Run: python scripts/bop_red_kite_published_baseline_audit_v1.py --out /tmp/bop-redkite-published-baseline.json

No network permission is used by this script. The sole input is research/BOP_RED_KITE_PUBLISHED_BASELINE_AUDIT_V1.json.
