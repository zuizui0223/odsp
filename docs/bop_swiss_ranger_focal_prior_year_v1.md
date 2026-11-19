# Focal-bird chronological other-year exposure: earlier-year train, later-year test

## What is already established

ODSP main includes the source-first outcome-blind Swiss 697-seasons/258-bird-ID cohort and the verified 2024 NestTool `year_id` versus `bird_id` split distinction (PRs #293–#295). The [same-test R ranger comparison in PR #296](https://github.com/zuizui0223/odsp/pull/296) matched 50 test bird-ID rows and 488 training rows between models. It found **no improvement in classification accuracy from training with a second season of the test bird**; HR mean log loss increased by +0.021876 while nest mean log loss changed by −0.000909. Crucially, in #296 the test year was chosen randomly among two available years, so the training source could be *later* than the test source.

## New directional question, frozen before source reread

Does exposure to **a strictly earlier year** from each of the same 50 focal two-season birds improve prediction of their **later year**, on identical later-year test rows, relative to training only on other birds? The chronology direction was predeclared in `research/BOP_SWISS_RANGER_FOCAL_PRIOR_YEAR_V1_CONTRACT.json` at commit **`4b3d8d486207f6488701bdc71f662f089b3f0b8f`**. It uses the same dated publicly prepared NestTool RDS (2024 GitHub commit `8fdf3884…`, exact file length 53,709,803 bytes, Git blob `fab942c0df8d6f77dc1db2bd2e2717681b9a3632`) and original 34 movement predictors.

**IMPORTANT:** the labels in this Swiss RDS have **already been opened during PRs #295 and #296**. This is a prospective *choice of method*, but it is **not a fresh independent or untouched holdout**. Do not report confirmatory p-values, external predictive gain or a new multi-study biological result.

## Strict chronology and source gate

Before reading HR/nest values in this route, require that the source year-ID strings match **`^[12][0-9]{3}_.+$`**, each initial four-digit calendar year is 1990–2024, and any available separate `year` column agrees exactly with the year-ID prefix. Require all **51** bird-ID strings with exactly **two** eligible seasons to have **two different calendar years**; otherwise stop at `HOLD_CHRONOLOGICAL_ID_YEAR_GATE`. Enforce the existing source-schema gate: 697 unique year IDs, 258 bird strings, original one–seven-season histogram **66/51/62/56/20/2/1**, 34 original predictor names and HR/nest response *column names only*. No outcome values are read until these checks pass.

## Matched-size, matched-test 16-seed R ranger comparison

For each **frozen** seed 20261201–20261216, sample 50 of the 51 two-season bird-ID strings, then fix the **later** calendar year of each selected bird as the test set (one year per bird; **50 rows**). The strictly **earlier** year is the candidate exposed training record. From the **597 season rows of other birds**, sample 438 common training rows; sample 50 more outsider rows for the unrelated-bird control. Each model trains on **488 rows** and predicts the exact same **50 later-year test rows**, with **438 training rows in common**. The focal-bird-prior-year arm has exactly **50** shared bird IDs across its train/test sets and zero identical year-ID rows; the unrelated-bird arm has **zero** shared bird IDs.

To isolate one substantive change from #296, we reuse its verified 2024-original-family R `ranger` implementation and frozen **500 trees, mtry=5, min.node.size=10, 34 original features and train-only imputation**, changing only the calendar-year rule and the 16 prespecified seeds. Two outcomes, HR and nest, generate 64 model fits. Report identical source-wide score metrics and paired exposed-minus-disjoint deltas on identical test rows, all as **descriptive** sensitivity.

**Not a global future-year prediction:** the 438 common and 50 control training rows from *other* birds are not restricted to being earlier than *every* test year. Thus this tests the *focal animal's own* earlier season versus no prior season for that bird; it is not a forward-chaining population study or an untouched future-year external forecast. The 50 replacement rows necessarily change predictors and labels, so it is **not** a pure causal effect of individual familiarity.

## Fail-closed execution

Run source-free Python known-truth tests on 3.10, 3.12 and 3.13. Then run the source-free R chronological splitter and two synthetic ranger forest tests. Only after all checks pass may the official workflow download the exact pinned 2024 public RDS into ephemeral runner storage. Verify full size/Git blob, run the outcome-blind historical source schema plus new chronology source gate, then fit the 64 predeclared ranger models on only HR/nest. Export **only aggregate model JSON / schema JSON / original source HOLD**, never raw RDS, GPS, individual IDs, exact test years, per-year predictions or reproductive success outcomes. After the original source run, freeze the artifact SHA256 and switch future CI to offline-only.

## Claims unchanged

Original BOP endpoint remains `empirical_state_prediction_mixed`, red-kite new external animal/group outcome remains `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`, original Dryad remains `NOT_ADMITTED`. A strong temporal same-source score in this subset cannot establish globally transferable ecological behaviour or original 2024 publication accuracy.
