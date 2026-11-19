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
