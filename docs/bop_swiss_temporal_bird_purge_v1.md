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

## First actual official source result: all 96 prespecified forests scored

The original [GitHub Actions run 44746545177](https://github.com/zuizui0223/odsp/actions/runs/44746545177) completed successfully. Python 3.10/3.12/3.13 synthetic source-group tests and R synthetic ranger tests passed before any new RDS read. The source job `136323453061` verified the exact 2024 RDS Git blob SHA1, prior **697 seasons / 258 bird ID strings / 34 predictors** source gate, and the new **outcome-blind calendar-forward bird-purging gate**. Only then were HR/nest values reread to fit all **96 model panels**. There were **zero** class-support or sample-size holds.

The first original aggregate artifact is ID `14633317139` (`bop-swiss-temporal-bird-purge-first`), ZIP **8,041 bytes**, SHA256 `04df9081e71d497c2e8c394e0fd79bfbb72524eb765dd019fdd4dc1f08be04ff`. Its three safe aggregate-only JSON files are:

| Artifact member | Bytes | SHA256 |
|---|---:|---|
| `bop-swiss-forward-original-schema-first.json` | 572 | `f6d267261433655512cb131b7d935f78a51c4d0d1e29fa9d74b606bf67b310fc` |
| `bop-swiss-forward-chronology-cohort-first.json` | 2,116 | `3153b930d19738585c0d6b1f7eb2869e7e5d6ba856e28f0253321ff662911aa4` |
| `bop-swiss-forward-bird-purge-ranger-first.json` | 84,103 | `7f566d36f1d01596289c89b1c29b04b4d07ff9e8f1762c081808e7a3271b10db` |

### Actual source temporal group eligibility

| Fixed cutoff | All older training seasons / birds | Older + bird-purged training seasons / birds | Later testing seasons / birds | Repeated test birds in older unpurged training | Repeated test birds after purge |
|---|---:|---:|---:|---:|---:|
| 2020 | 405 / 220 | **98 / 64** | **292 / 194** | 156 | **0** |
| **2021 primary** | 580 / 240 | **396 / 166** | **117 / 92** | 74 | **0** |
| 2022 | 665 / 258 | **555 / 226** | **32 / 32** | 32 | **0** |

All old-source training rows precede *every* test year under all cutoffs. Both training modes face identical future-year test rows, but the purged training set is smaller. Thus this is a valid source-key grouped/temporal **within-Swiss retrospective validation**, but the difference between the models is **not** solely the effect of shared biological bird IDs.

### First original outcome metrics, fixed eight forest RNG seeds

| Cutoff, outcome | Older all-bird AUC | Older bird-purged AUC | Bird-purged test accuracy | Bird-purged Brier ↓ | Bird-purged log-score gain vs training prevalence |
|---|---:|---:|---:|---:|---:|
| 2020 home range | 0.967915 | **0.966780** | 0.957620 | 0.036055 | **+0.662324** |
| 2020 nesting | 0.944024 | **0.949099** | 0.878853 | 0.085944 | **+0.553932** |
| **2021 home range** | 0.934495 | **0.933179** | 0.941239 | 0.053654 | **+0.267306** |
| **2021 nesting** | 0.891192 | **0.881147** | 0.833333 | 0.129345 | **+0.225660** |
| 2022 home range | 0.415736 | 0.373884 | 0.875000 | 0.127684 | **−0.609657** |
| 2022 nesting | 0.320312 | 0.313616 | 0.750000 | 0.197332 | +0.184597 |

**Positive but bounded conclusion:** The 2020 and predeclared primary 2021 calendar-forward, bird-ID-disjoint source models retain substantial discrimination and positive log-score gain above a training-only prevalence baseline. They are not evidence of *external country-level transfer* because the original source's outcomes were previously examined in PRs #295–#297.

**Important 2022 exception:** The two 2022 test responses each have **28 positives and only four negatives among 32 season rows**. Consequently **accuracy can remain apparently high while ROC AUC falls below 0.5** and the HR probability scores fall below the training-prevalence log-score baseline. This is a predeclared outcome/period sensitivity and cannot be removed by picking a more favorable cutoff after seeing results. The low AUC is consistently below 0.5 over eight different RF randomness seeds, but these seeds reuse the same *four negatives*, not independent data. It is **not yet evidence of an ecological regime shift**, a changing spatial mechanism, or a year-specific causal effect; test composition, sample-size uncertainty and covariate shift remain possible explanations.

Across all 2020/2021/2022 cuts, target prevalence in the future test was HR 0.650685 / 0.632479 / **0.875000** and nest 0.500000 / 0.521368 / **0.875000**. Thus class composition demonstrably changes; neither raw accuracy nor AUC should be interpreted without the outcome denominator.

### Source permanence and inference STOP

First official run IDs and complete ZIP/member SHA256, all twelve fixed outcome/model mean scores, both cohort group-count arms, and the 2022 negative-class caveat are preserved in `BOP_SWISS_TEMPORAL_BIRD_PURGE_V1_FIRST_RECEIPT.json`. `scripts/verify_bop_swiss_temporal_bird_purge_first_v1.py` verifies the original run provenance and every fixed summary **offline**, or the complete 96 panel original first result if the artifact ZIP is supplied. Post-first CI has been switched to offline-only tests and **never redownloads the RDS or reopens HR/nest labels**.

Scientific terminal limits: BOP `empirical_state_prediction_mixed`; real external red-kite `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`; historical Dryad `NOT_ADMITTED`. No one-sided rank coverage for unseen future animals has been certified.