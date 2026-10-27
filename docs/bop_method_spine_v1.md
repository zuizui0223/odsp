# ODSP BOP_RODENT methodology spine — one integrated scientific route (v1)

**Scope:** ODSP as a method paper. Biological solar/season/movement questions belong in RSDS, not here. This is a single ordered technical chain of **five stacked, currently unmerged Draft PRs**, not five independent ecological discoveries.

**One central inference:** more informative individual state predictions, portability to future animals, validity of a new-group gain bound, and input/identity compatibility across data sources are distinct claims. Never exchange one for another.

## The five completed methodological roles

| PR | Component | Frozen direct evidence | Claim ceiling |
|---|---|---|---|
| [#274](https://github.com/zuizui0223/odsp/pull/274) | Independent-*individual* log-score gain rank lower envelope; frozen predictor and group validation | 128 synthetic worlds, 40,960 group scores/scenario: same-process 0.899438, forced label-shift 0.068091 | 90% marginal new-group coverage only **if calibration/new group scores are exchangeable** for the fixed predictor. Original BOP archived cross-fit ranks are descriptive. |
| [#275](https://github.com/zuizui0223/odsp/pull/275) | Replay **source training rows → fitted model/reference bytes → outcome-blind forecast probabilities** | 64 synthetic worlds, 10,240 new groups/scenario: same-process 0.891504, forced label-shift 0.128711 | Executable binding **for the declared categorical reference learner**, NOT arbitrary BOP scikit-learn RF and not real-bird coverage. |
| [#276](https://github.com/zuizui0223/odsp/pull/276) | BOP 2023 v3 vs 2026 same-study source/individual identity gate | 35 original IDs matched; 45 current IDs (46 reference rows), 10 new IDs split over four taxa, maximum six in one species | **NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT**. Same-study metadata cannot supply nine fresh same-species calibration animals plus disjoint test; no GPS opened. |
| [#277](https://github.com/zuizui0223/odsp/pull/277) | Independent Dryad provider version/schema and source provenance | Official DOI/version metadata and CC0 license verified; original RF lacks external temperature, coordinates 0.1° rounded; external tagged-animal identity unverified | **NOT_ADMITTED** for original RF, no external prediction. First Actions JSON recovered after a later semantic-copy digest omission; scientific records and correction both preserved. |
| [#278](https://github.com/zuizui0223/odsp/pull/278) | New **reduced common-input** learner (species + binary *mean solar-clock* phase), frozen cross-source train → target calibration → untouched test | 24 synthetic worlds, 2,880 target individual scores/scenario: 0.902431 same-target-process, 0.262847 validation-only adversarial shift | Synthetic method proof only. This is a **different learner** from historic RF; Dryad remains NOT_ADMITTED and real cross-study independent group status untested. |

The historical **biological** BOP result itself remains an immutable upstream reference: 4 admitted species, 30 individually scored birds, 154,655 eligible GPS events, primary RF gain positive in **27/30** and multiclass Brier improvement positive in **30/30**, primary overall terminal **\`empirical_state_prediction_mixed\`**. The comparator for 27/30 was the original pooled fold-training altitude-state marginal, so it cannot by itself certify within-species context gain.

## Evidence ladder (do not promote prematurely)

1. **Observed old data:** the original 30-individual held-out BOP result is mixed; no retuning or rewriting.
2. **Statistical construction:** one mean score gain **per independently scored animal**. If \`n\` calibration groups and \`alpha\` one-sided miscoverage, the lower bound is the \`floor((n+1)*alpha)\`-th smallest score (or vacuous at rank 0). Coverage is marginal for **one future exchangeable group**, conditional on one fixed upstream model—not universal positive skill or a confidence interval for mean gain.
3. **Executable training chain:** model/reference artifacts are re-created from the exact training source, and every calibration and validation prediction must replay from those artifacts before outcomes open. Distinct role rosters and checksums are mandatory.
4. **Data-source gate:** only if independent animal IDs, source publication version, altitude semantics, timestamp units, feature availability and target-source group exchangeability are externally defensible can a **new preregistered real-data route** be proposed.
5. **Synthetic common-input proof:** replacing an incompatible predictor with a genuinely new common-input learner can yield well-calibrated **target-source** group prediction bounds in known truth, but **does not rescue an incompatible archived RF** or make an unverified biological sample confirmatory.

## Preventing false precision: the repeated-world unit

Original #278's 2,880 synthetic individual validation scores are distributed across 24 independent worlds. The **120 individuals inside each world share a fitted source predictor and target-source gain calibrator**, so a naive iid 2,880-group interval is not suitable for inference about the process of repeatedly refitting/recalibrating the whole pipeline.

A **post-result descriptive** world-level Monte Carlo audit (not part of the frozen qualification test) uses exact first-run world counts, pinned to the original GitHub Actions artifact; it reports equal-world means and approximate 95% Student-t intervals with **24 worlds as Monte Carlo units**:

| Quantity | Original pooled coverage/contrast | Approximate 95% MC interval over worlds |
|---|---:|---:|
| Exchangeable target calibration/test | 0.90243 | 0.88614–0.91872 |
| Validation-only deliberate shift | 0.26285 | 0.23678–0.28891 |
| Within-world paired coverage contrast | 0.63958 | 0.61518–0.66399 |

World-specific target coverage ranged from **0.7917 to 0.9833**: approximately 90% *average* group coverage does not promise 90% coverage for **every realized fitted model/calibrator**. The post-result precision audit changes no original success/failure categories. It does not estimate ecological model skill or positive mean gain.

Inspect:
\`research/BOP_COMMON_INPUT_V1_WORLD_COUNT_AUDIT_SOURCE.json\`,
\`scripts/audit_bop_common_input_world_uncertainty_v1.py\`,
\`tests/test_bop_common_input_world_uncertainty_v1.py\`.

## Existing source/interpretation evidence is immutable

Original scientific receipts:
- \`BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json\`
- \`BOP_FIXED_MODEL_GROUP_TRANSFER_V1_VALIDATION_RECEIPT.json\`
- \`BOP_MANAGED_SOURCE_TO_FORECAST_V1_VALIDATION_RECEIPT.json\`
- \`BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_TERMINAL_RECEIPT.json\`
- \`BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_TERMINAL_RECEIPT.json\`
- \`BOP_COMMON_INPUT_TRANSPORT_V1_VALIDATION_RECEIPT.json\`

These are checked in CI against pinned Git blob SHA1s, together with exact admission statuses and proof-level boundaries. The Dryad first-result original artifact, initial malformed later copy and documented correction **all remain available**; the earlier copy is not silently edited.

## Integration order and stop rule

The existing dependency sequence is **#274 → #275 → #276 → #277 → #278**. Keep the Draft PRs separate until they can be reviewed/merged in this order. Do not retroactively promote any stage to empirical BOP/Dryad external generalization; no new branch should be opened merely to tune the synthetic 90% coverage numbers.

**This method series is technically sufficient to form a methods-paper validation spine.** The missing scientific step for a stronger ecological cross-source result is *not* another synthetic benchmark: it is an **independent, actually accessible biological source** with validated identity, compatible predictors or an explicitly separate new model, frozen calibration/test rosters and untouched outcome access. Until such a source is admitted, this route stops at qualified methodology plus the historical mixed BOP finding.
