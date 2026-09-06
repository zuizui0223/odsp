# Group-safe probabilistic forecast stacking

This post-v4 ODSP layer combines already fitted probabilistic ecological-state forecasters without using the final validation rows to learn ensemble weights.

## Data roles

Use four distinct roles when all are needed:

1. **member training**: fit the upstream candidate density models;
2. **stacking tuning**: evaluate all member densities on the same realized tuning states and learn convex stacking weights;
3. **conformal calibration**: after stacking, calibrate prediction sets/regions for the stacked forecaster on a separate split;
4. **validation**: freeze all weights and calibration rules, then score independent groups.

Validation rows must never update the stacking weights.

## Fit convex weights

```python
from odsp.forecast_stacking import fit_log_score_stacking

fit = fit_log_score_stacking(
    tuning_candidate_log_density,  # rows x candidate models
    candidate_names=["rf_density", "gam_density", "bayes_density"],
)
```

The fixed member densities are combined as

`p_stack(a|x) = sum_k w_k p_k(a|x)`

with non-negative weights summing to one.  ODSP uses EM to maximize weighted mean tuning log density.

## Untouched validation

```python
from odsp.forecast_stacking import evaluate_stacked_forecast

result = evaluate_stacked_forecast(
    fit,
    validation_candidate_log_density,
    validation_training_marginal_log_density,
    validation_group_ids,
    candidate_names=["rf_density", "gam_density", "bayes_density"],
)
```

Every declared independent group receives its own conditional-minus-training-marginal log-density gain.  `generalizing` still requires all group gains to be positive; a positive pooled average cannot rescue a failed group.

## Calibration does not transfer through stacking

Even if every member model has calibrated prediction intervals or conformal regions, those coverage claims are **not inherited** by the mixture.  The stack must be recalibrated on an independent calibration split before ODSP makes a coverage claim for the ensemble.

This is why `ForecastStackingFit` records:

- `validation_used_for_fit = False`;
- `coverage_inherited_from_members = False`;
- `requires_independent_recalibration = True`.

## Known-truth benchmark

The prospective benchmark uses complementary left/right Gaussian specialists and a broad training-marginal candidate.  It tests that:

- tuning learns complementary non-zero specialist weights;
- the broad marginal receives little weight;
- the frozen stack transfers across all stable validation groups;
- the stack beats every single candidate on the stable validation distribution;
- a strong validation shift is detected as non-generalizing;
- a positive pooled gain with one failed group remains `mixed`;
- candidate-column permutation changes neither named weight nor result;
- member coverage is never inherited and no aggregate confidence score is created.

## Claim boundary

Stacking is predictive model combination, not biological mechanism identification.  It does not guarantee robustness to distribution shift, remove observation bias, establish causality or make member-model calibration valid for the ensemble.  The frozen state-prediction v4 manuscript and all closed empirical endpoints remain separate from this development layer.
