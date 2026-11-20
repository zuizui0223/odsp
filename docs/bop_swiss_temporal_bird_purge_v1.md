# Swiss NestTool: retrospective calendar-forward, biological-bird-purged validation

## State and question

Merged PR #297 established that adding each test bird's earlier season did not substantially improve HR or nest predictions on **identical later-year test rows** in a Swiss same-source R ranger refit. However, **records from other training birds were allowed to occur in years later than some test years**. The next independent design constraint is to make *all* training seasons chronologically earlier than *all* test seasons, while also removing test bird identities from the training data.

**Question:** Can these previously studied 2024 Swiss source movement features predict home-range and nesting states across a real calendar-time break **and** across unseen `bird_id` strings? This is retrospective evaluation of an already accessed source, not a prospective deployment or untouched biological validation.

## Prospective method freeze, not a fresh-data holdout

Before this route downloaded the exact 2024 public prepared RDS, source and analysis definitions were frozen at commit **`8579e6d0260b1fc89f3047e6c6836a1542846cbe`** in `research/BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_CONTRACT.json`. The source is exactly `Vogelwarte/NestTool@8fdf3884b5f6079afdffdc5c563c9050766670a4:input_data_prepared.rds` (53,709,803 bytes, original Git blob SHA1 `fab942c0df8d6f77dc1db2bd2e2717681b9a3632`). This is the same source previously used in PRs #295–#297; **HR/nest labels from these birds were already examined**. The fixed source year range is 2016–2022, 697 unique season IDs, 258 bird-ID strings and 1–7-season multiplicity histogram **66/51/62/56/20/2/1**.

## Three fixed global calendar cutoffs

The **primary cutoff was fixed at 2021**, with 2020 and 2022 required sensitivity panels; no threshold will be selected posthoc by its predictive accuracy. For each cutoff year `c`,

- **Test:** *all* source bird-season rows with calendar year **`>= c`**.
- **Chronological-only training:** *all* source bird-season rows with calendar year **`< c`**. This obeys global time order but allows **different years of test birds** to occur in training.
- **Chronological + bird-disjoint training:** source rows with year **`< c`** **excluding every bird ID appearing in the test**. All remaining training years strictly precede every test year, and no biological `bird_id` string is shared between train and test.

The two training groups can have **different sample sizes**; this is required to transparently measure the cost of a strict bird purge, and it means the raw difference between their scores **cannot be attributed solely to individual identity reuse**. They evaluate **identical test rows** per cutoff. Counts, number of distinct birds, amount of ID overlap, year-range gate and group feasibility are computed **without reading HR/nest labels**.

## Outcome and model rules

Only after the fixed source, year, identity and training/test composition gate succeeds are HR/nest values read. Predeclared support constraints: at least 60 training and 20 test season rows; at least 20 training bird-ID strings and 10 test bird-ID strings; at least 5 of **each** class in training and 3 of **each** in test. An infeasible cutoff/target/mode is output as **HOLD**, not dropped and replaced with another cutoff.

Reuse the previously source-audited 2024 NestTool-family **R ranger probability RF**, 34 original movement features, **500 trees, mtry=5, min.node.size=10**, bootstrap/Gini, and training-only feature imputation. There is **no tuning on the test outcomes**. For each of 3 cutoffs × 2 outcomes × 2 training modes, fit 8 fixed forest seeds (`20261221`–`20261228`): up to **96 models**. Unlike PR #297, the calendar-based **test rows do not change across the eight forest seeds**, so these are algorithmic stability replicates, *not independent ecological validation samples*. Report all cutoffs, including failed source/label-support arms.

Score test accuracy, balanced accuracy, ROC AUC (when both classes present), log loss, Brier score, log-score gain against a training-only class-prevalence baseline. Export only whole-cohort cutoff counts, aggregate outcome metrics per forest seed, group identity-disjoint check and explicit HOLD flags. No individual animal IDs, year IDs, raw source data, probabilities, GPS or breeding success values are uploaded.

## Inference limits

Global year-order and biological-source-ID disjointness together improve over the focal-bird-only temporal comparison in PR #297, but **this remains the same Swiss population that was previously inspected**, the first 2024 author-tuned ranger split is not re-created, and the source strings are not independently authenticated across tracking providers. Test sets for 2020/21/22 overlap. No confirmatory p-value, independent-population transfer, one-sided future-individual coverage guarantee or correction to the original journal study follows.

Historical ODSP `empirical_state_prediction_mixed`, original Dryad `NOT_ADMITTED`, and external red-kite `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER` remain unchanged. The result is a *descriptive new-method calendar-forward retrospective sensitivity*.

## Execution

1. Python synthetic source and group tests on Python 3.10, 3.12 and 3.13.
2. Original-family source-free R ranger synthetic validation to check split logic and predictors before provider access.
3. Download only the pinned 53.7-MB 2024 prepared RDS in a private GitHub runner; verify byte length and Git blob SHA1.
4. Run the prior original source schema gate and new **outcome-blind** 2020/2021/2022 chronology/bird purge gate.
5. Fit only the 3×2×2×8 frozen forests subject to fixed class-support rules, then archive aggregate-only JSON; delete the ephemeral RDS.

After one real source run, freeze its first artifact digests and switch the workflow to **offline-only** verification, preserving the source gate and all panel outcomes without repeated RDS access.
