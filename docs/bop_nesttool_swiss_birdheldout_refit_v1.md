# 2024 Swiss NestTool prepared features: season vs biological-bird held-out RF

## Current need

Merged [PR #293](https://github.com/zuizui0223/odsp/pull/293) verified that all three original NestTool training functions select `year_id` rather than `bird_id` when splitting training and test. Merged [PR #294](https://github.com/zuizui0223/odsp/pull/294) independently recovered **697 eligible Swiss seasons / 258 bird-ID strings**, with histogram **66/51/62/56/20/2/1** for 1–7 eligible seasons and conditional expected **121.992374** birds represented in both roles under a hypothetical uniform 488/209 year-ID split. That is *not* an actual performance comparison.

## Before prepared RDS or breeding responses are opened

The fixed source/model protocol in [`research/BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_CONTRACT.json`](../research/BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_CONTRACT.json) was committed **before** reading the historical binary prepared-feature input. The original source is the **28 August 2024 public GitHub commit** of [Vogelwarte/NestTool](https://github.com/Vogelwarte/NestTool), file [`input_data_prepared.rds`](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/input_data_prepared.rds), exactly **53,709,803 bytes**, Git blob SHA1 `fab942c0df8d6f77dc1db2bd2e2717681b9a3632` (first added 2 July 2024). The dated analysis script `NestTool_plotTrees.r` reads `readRDS('input_data_prepared.rds')$summary` at **line 103**.

**This is a distinct, previously prepared public GitHub RDS, not a file in the frozen Zenodo v1 source manifest.** It is not automatically certified as the exact input to every result in the original journal article. The source-schema gate must first verify the full Git blob hash, top-level list `$summary` data frame, **697 unique year IDs / 258 bird IDs**, the **entire seven-bin bird/season histogram** above, required 34 original movement predictors and the existence of HR/nest columns. It must NOT inspect HR/nest/success values. If anything mismatches, output **HOLD**; do not invent or adapt a new cohort.

Only after a successful outcome-blind gate is a separate source/model job allowed to read the **HR and nest labels**, without reading reproductive success. All raw features, IDs, labels and predictions remain ephemeral in the GitHub runner. The committed artifact contains **only aggregate test scores** and original source/code provenance.

## Refitting rather than replaying the historical exact model

This is a **new, frozen common-feature random-forest sensitivity comparison**, not byte-identical refitting of the authors' historically tuned `ranger` forest. It uses the same **34** movement features identified from the 2024 original HR/nest training R code, with train-only median imputation of missing numeric predictors, training-mode imputation for sex, and a frozen **scikit-learn RF with 500 trees, 5 candidate predictors at each split, bootstrap sampling, Gini criterion, leaf size 1, and no label reweighting**. Hyperparameters are fixed before opening source labels; test data never select predictors, splits or hyperparameters.

Across eight **precommitted seeds** 20261119–20261126, evaluate two targets separately:

1. **Season-held-out:** uniformly randomly assign 70% of the source year IDs to training and the remaining 30% to testing, without controlling biological bird identity.
2. **Bird-held-out:** randomly order distinct bird IDs and solve a deterministic subset-sum problem to form a training set with **exactly the same number of season rows** as the season-held-out arm, but with **no bird-ID overlap** between train and test. Fail if impossible; never use outcomes when choosing groups.

For each response, missing labels are excluded identically from the initial analysis panel **before partitioning**, and the exact N used is reported. No outcome-derived train/test stratification or seed substitution is permitted. Report each seed's **aggregate-only** test accuracy, balanced accuracy, ROC AUC (when defined), log loss, Brier, log-score gain over the training-only marginal prior, number of year rows, distinct birds in each role and overlapping bird-ID count. Aggregated mean/median/min/max and paired-seed differences are **descriptive only**: repeated random splits from one study are not independent ecological replications or a formal significance test.

The primary scientific comparison is the **sensitivity to the training/test biological unit under a matched test season sample size**. Even if an accuracy gap is observed, different held-out birds/classes/samples and the distinct RF implementation prevent directly attributing the full gap to literal leakage or directly adjusting the original journal's reported accuracies. Separate Swiss→Germany external validation is not re-evaluated and the original BOP `empirical_state_prediction_mixed` and red-kite new-group `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER` remain unchanged.

## Execution and stopping

First run synthetic tests under Python 3.10/3.12/3.13. Then download the exact dated public prepared RDS into an ephemeral runner directory, verify **size and Git blob**, and inspect only ID/feature **schema** using R `readRDS`. Only after the schema job passes does the model job download the same pinned RDS into its own ephemeral runner, export only allowed inputs and perform the frozen matched-size RF evaluation. If source is unavailable, labels are differently encoded, class support is insufficient, or the required predictors are missing, **HOLD**, not altered model conditions. Persist only schema and aggregate result JSON, never private CSV or raw RDS.

Original Swiss source-level eligible 697/258 numeric matching does not by itself authenticate every individual in the journal authors' saved 2024 random split. This study therefore addresses the group-splitting **design sensitivity**, not new transfer guarantees.

## First official result: the source gate passed and bird-disjoint accuracy remained high

The first [GitHub Actions run #44462371738](https://github.com/zuizui0223/odsp/actions/runs/44462371738) completed **successfully**. All synthetic RF safety tests passed on Python 3.10, 3.12 and 3.13. The **outcome-blind** schema job (`135352277285`) verified the original 53,709,803-byte prepared RDS and Git blob SHA1, **697 unique year IDs, 258 bird-ID strings, the entire source multiplicity histogram 66/51/62/56/20/2/1, and all 34 original predictors**. Only after that success did the frozen model job (`135352626472`) read the two predeclared label variables (`HR`,`nest`), with no success outcomes.

Original first source-schema artifact ID `14499344988`, ZIP SHA256 `3cdca6d81a94d5a21268e1419b12fb9e6568c99136e35ae0e4123ddaa7dbd9f0`, schema JSON 572 bytes SHA256 `f6d267261433655512cb131b7d935f78a51c4d0d1e29fa9d74b606bf67b310fc`. Original first model artifact ID `14500588048`, ZIP SHA256 `e89369281ff48136b8f367e1b65601fa03f3f42cc6cee6c3a489e972d6d10083`, aggregate-only result JSON 25,955 bytes SHA256 `94f33235c21bdfcb0fb65dcb12a9d8ddc1f3bccc38ae4f172a6a2e05f4fe8ff2`. The frozen contract SHA256 is `f14ed4ee792681ec5bcd7a4fe65c627680af6910fd8d10fa63da73f28ff98c28`. The first results and all 32 per-seed **aggregate-only** test records are pinned in `BOP_NESTTOOL_SWISS_BIRD_HELDOUT_REFIT_V1_FIRST_RECEIPT.json`.

### Outcome-blind, matched-size source design versus actual model scores

Each of the **8 frozen seeds** used **488 training season rows and 209 test rows** in each split mode for both HR and nest. Unlike the season-held-out design, the bird-ID-disjoint mode had **exactly zero** bird-ID strings in common between train and test; the season-held-out mode shared **mean 120.375 IDs** (range 115–128). These are the **realized overlaps in these eight new simulated splits**, **not** the authors' original 2024 random assignment. For comparison, the previously source-derived theoretical expectation across random season partitions was **121.992374**.

| Response and eight-seed mean | Randomly held-out seasons (`year_id`) | Completely held-out source bird IDs (`bird_id`) |
|---|---:|---:|
| **Home range:** test accuracy | **0.968301** | **0.962320** |
| Home range: test Brier (lower is better) | **0.029506** | 0.030738 |
| Home range: test ROC AUC | 0.986449 | **0.988877** |
| Home range: test mean log-score gain vs train prevalence | 0.546518 | **0.573996** |
| **Nesting:** test accuracy | **0.947368** | 0.940192 |
| Nesting: test Brier | **0.046422** | 0.048585 |
| Nesting: test ROC AUC | 0.978683 | **0.979726** |
| Nesting: test mean log-score gain vs train prevalence | **0.523484** | 0.516542 |
| Actual shared source bird-ID strings | Mean **120.375** | **0** |

**Positive empirical result for a defined narrow estimand:** In these newly refitted, same-study, fixed-family RF models, previously unseen source bird IDs were predicted with **high accuracy and positive log-score gain over the training-marginal reference**, even after enforcing complete bird-ID separation. The fold-wise test-set composition differs between protocols, so the small mean-score differences are descriptive and do not establish any causal accuracy inflation of the published original NestTool, nor equality of future deployed population predictive performance. *The score does not come from a formally independent country/study or a historically untouched holdout.*

### Why this changes the conclusion — and what it cannot change

The byte-audited 2024 original trainer functions did use season-level train/test splitting, so the group-independence concern is real. However, **the straightforward hypothesis that its high internal accuracy must collapse when bird IDs are separated is not supported by this new fixed-model source comparison**. Source identity and code provenance were controlled, both protocols used the same source features and equal test season counts, and the grouped test had zero source bird-ID overlap.

The model is an **explicitly new scikit-learn 500-tree forest**, not the authors' originally tuned R `ranger` forest, and the eight replicated random partitions share the same source birds; no independent-study p-value or 90%-coverage certificate is calculated. This cannot be used as a corrected estimate of the authors' exact accuracy, and **does not resolve the Swiss→Germany 99/63 vs archived-source 99/49 denominator issue**. The third nest-success predictor was not assessed. The ODSP original BOP terminal remains `empirical_state_prediction_mixed`, and real red-kite new-group transfer stays `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`.

### Post-result integrity and access closure

The first model result's SHA256 and the frozen source-schema checksum were recorded *before* modifying the workflow to **offline-only regression**. Future PR workflow runs execute synthetic known-truth splits and verify every metric from the immutable original JSON; they **do not redownload the prepared RDS or reopen source HR/nest labels**. The private runner-local source CSV and source RDS were deleted and never uploaded.