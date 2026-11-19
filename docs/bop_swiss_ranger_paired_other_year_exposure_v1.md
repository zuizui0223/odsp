# Swiss NestTool ranger: paired same-test comparison of other-year bird exposure

## Main scientific question

Prior ODSP results: the exact 2024 NestTool trainer source split by `year_id` rather than biological `bird_id` (PR #293); the original Swiss source contains 697 eligible seasons and 258 bird-ID strings, including **51 IDs with exactly two eligible years** (PR #294); and a frozen new scikit-learn RF held 488 training and 209 test seasons in each design, finding **96.23% HR** and **94.02% nest** accuracy when test bird IDs were unseen by training (PR #295). However, the year/bird designs in that experiment **did not test the identical rows** and used a new RF implementation.

This follow-up asks: **On the exact same test birds and season rows, does adding another season from each test bird to training change R ranger forecasts versus using only other birds?** The design tests within-bird familiarity as a *data-substitution sensitivity*, not a proof of causal leakage, because replacement training rows have different predictor/label distributions.

## Freeze before source or response access

The original 2024 prepared source is the public [Vogelwarte/NestTool `input_data_prepared.rds` at commit `8fdf388…`](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/input_data_prepared.rds), 53,709,803 bytes, Git blob `fab942c0df8d6f77dc1db2bd2e2717681b9a3632`. Before this analysis, source, grouping, target, R model and all 16 random seeds were fixed in [`research/BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_CONTRACT.json`](../research/BOP_SWISS_RANGER_PAIRED_OTHER_YEAR_EXPOSURE_V1_CONTRACT.json) at commit **`0ff935d43624ad6f0efbcfd344a695f0e4f80279`**, ahead of any new RDS request or label access.

The source gate requires exactly 697 unique `year_id` rows, 258 unique source `bird_id` strings and the full source histogram of seasonal multiplicities **(1 through 7): 66,51,62,56,20,2,1**, including **51 birds present in exactly two seasons**. The original 34 movement predictors and the HR/nest outcome column names are checked before any outcome-value read. Only HR and nest can then be used; *nesting success is never inspected*. A source/metadata mismatch is HOLD, not a reason to find an alternative cohort.

## Fixed paired design (same held-out rows within each seed)

Each of **16 precommitted seeds** from `20261119` through `20261134`:

1. Uniformly select **50 of the 51 source bird-ID strings** present in *exactly two seasons*. Randomly choose one season per selected bird for the common test set (**50 season rows from 50 IDs**). The other season of each selected bird is the potential *same-bird exposure* record; its temporal ordering relative to the test season is not assumed.
2. The remaining 597 season rows all belong to birds **absent from the test set**. Randomly select **438 common training season rows** from that pool. From the remaining 159 outsider rows, randomly select **50 control filler rows**.
3. **Bird-disjoint control model:** train on the 438 common + 50 unrelated-bird filler rows (**488 total**); test on the 50 preselected test rows, with **0 shared bird IDs** between roles.
4. **Same-bird-other-year exposure model:** train on the same 438 common + the 50 *other-year* rows from the test birds (**488 total**); test on the **exact same 50 rows**, with **50 distinct test bird IDs** appearing in both roles but **no identical year-ID row** repeated.
5. Fit the **same model and seed** to each arm. All 16 splits and both HR/nest targets are reported; no fold selection based on model results.

The two training datasets share **438/488 source rows**, have equal sizes and the two test datasets are **literally identical within each seed**. Changing 50 training rows necessarily also changes their biological feature and label distributions. Consequently this is a **paired same-test exposure-vs-control sensitivity**, not a pure causal effect of bird identity or a universal new-bird accuracy effect. The 50 test birds are specifically from the two-year subset and do not represent all 258 source birds.

## R ranger, not exact historical tuned forest

This deliberately uses `ranger`, the original NestTool's R probability-forest **algorithm family**, with **fixed 500 trees**, **mtry=5**, `min.node.size=10`, bootstrap sampling, Gini split, one thread, and the same seed for the paired arms. The feature formula contains the same 34 original source predictor columns with train-only numeric median and sex mode imputation. Training-only outcome prevalence supplies a separate marginal baseline for optional log-score gain. Test labels never influence feature preparation, fold selection or hyperparameters. The original authors tuned RF hyperparameters using training OOB selection; those exact historical tuned models and original 2024 random assignments are **not replicated here**.

Record accuracy, balanced accuracy, AUC when the common test has both classes, log loss, Brier, and log-score gain relative to training-only class prevalence for both HR and nest. **Primary paired deltas** (same exact test rows) are exposed-minus-disjoint in test log loss, Brier and accuracy; they are descriptive across repeated source resamples. No false independent study replication, p-value, universal external generalization or correction of original journal accuracy.

## Reproducibility and safety

Python 3.10/3.12/3.13 tests first check that the original published source-group histogram makes a 50-bird paired test feasible, all test rows are held out, exactly 488 training seasons are used and only 50 training rows differ. Separately, a source-free **R self-test** with artificial 697 seasons checks the actual R pairing and fits source-free ranger models before downloading any live RDS.

One first GitHub Actions source job downloads the single pinned RDS into private runner storage, checks its **size and Git blob SHA1**, runs the earlier **outcome-blind** 697/258 schema gate, and only then runs the frozen R ranger models reading HR/nest values. Raw RDS, animal IDs, individual predictor/outcome rows and per-season probability outputs are not saved or uploaded. Only source-wide safe aggregate JSON and explicit source HOLD are eligible artifacts. After the first provider-result, subsequent CI should become **offline-only**, preserving the original artifact SHA256.

Original ODSP BOP terminal: `empirical_state_prediction_mixed`. New red-kite external/outcome-group state remains `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`. No Swiss→Germany transfer is performed here.
