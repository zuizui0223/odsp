# Trust-aware model selection v2

This layer strengthens `odsp.forecast_model_comparison` by replacing pooled coverage admission with a **fail-closed group-wise coverage audit**.

A probabilistic ecological-state forecaster is eligible for trusted comparison only when every declared independent group satisfies both:

1. positive held-out conditional-minus-training-marginal log-density gain;
2. empirical prediction-set/region coverage within the declared tolerance.

Pooled gain and pooled coverage are still reported, but neither can rescue a local failure.

## Evaluate one candidate

```python
from odsp.trust_aware_model_selection import evaluate_trust_aware_candidate

candidate = evaluate_trust_aware_candidate(
    "model-a",
    conditional_log_density,
    training_marginal_log_density,
    covered,
    site_ids,
    region_size=region_size,
    target_coverage=0.90,
    coverage_tolerance=0.03,
)
```

The returned object retains the ordinary pooled forecast score and a separate `groupwise_trust` audit. `trusted_admissible` is fail-closed: every group must pass both transfer and coverage.

## Compare admitted candidates

```python
from odsp.trust_aware_model_selection import compare_trust_aware_candidates

selection = compare_trust_aware_candidates([candidate_a, candidate_b])
```

Among trusted candidates, the Pareto front uses three independent dimensions:

- higher mean held-out log-density gain is better;
- lower **worst-group** coverage error is better;
- smaller mean prediction-region size is sharper.

The recommended candidate is the trusted candidate with the highest held-out mean log-density gain. No scalar confidence score is constructed.

## Why v2 is stricter than pooled comparison

The known-truth benchmark contains a candidate with high gain and pooled coverage `0.9002`, but one of 20 groups has coverage only `0.60`. The pooled coverage check passes, yet group-wise coverage is `mixed`, so v2 rejects the candidate.

A second candidate has perfect group-wise coverage but one negative transfer group; it is also rejected. This makes calibration and transferability necessary but distinct conditions.

## Relationship to stacking

Use model selection and stacking for different questions:

- `forecast_model_comparison` / this v2: compare frozen candidate forecasts;
- `forecast_stacking`: learn a convex mixture on a dedicated tuning split;
- after stacking: recalibrate the ensemble on an independent calibration split, then apply group-wise transfer and coverage audits on untouched validation groups.

Member-model coverage is never inherited by a stack.

## Claim boundary

Group-wise empirical coverage is an audit, not a conditional-coverage guarantee. The recommended forecast is not asserted to be the true biological mechanism. Trusted admission does not guarantee performance under future distribution shift, remove observation bias or establish causality. Group definitions and tolerances remain analyst-declared scientific design choices. Frozen v4 submission artifacts and closed empirical endpoints are not modified by this post-v4 layer.
