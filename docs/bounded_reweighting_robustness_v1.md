# Bounded reweighting robustness

This ODSP layer asks a stronger question than enumerating a few weighting scenarios:

> If every validation row's declared base weight were allowed to change anywhere inside a bounded multiplicative envelope, could the transfer conclusion flip?

For a caller-declared `gamma >= 1`, row multipliers may vary independently in

`[1/gamma, gamma]`.

The maximum-to-minimum multiplier ratio is therefore `gamma^2`. The scale of all base weights is irrelevant.

```python
from odsp.bounded_reweighting_robustness import (
    audit_bounded_reweighting_robustness,
)

result = audit_bounded_reweighting_robustness(
    row_gain,
    groups,
    base_weight=base_weight,
    gamma=2.0,
)
```

For every independent validation group, ODSP returns:

- the declared-weight point mean gain;
- the smallest possible mean gain over **all** permitted row multipliers;
- the largest possible mean gain over all permitted multipliers;
- `robust_positive`, `robust_nonpositive`, or `bound_sensitive`;
- `critical_gamma`, the smallest multiplicative bound within the configured search range that can destroy the point-sign conclusion.

The group-level conclusions are fail-closed. `gamma_robust_generalizing` requires every group to remain positive even under its worst allowed reweighting. A pooled mean cannot rescue a sensitive or failed group.

## What gamma means here

`gamma` is a user-declared sensitivity envelope, not a parameter inferred from the data and not automatically a detection-probability, odds-ratio, or causal-confounding parameter. For example, `gamma=2` permits each base weight to be multiplied independently by 0.5 to 2.0.

## Relationship to scenario-based sensitivity

`sampling_weight_sensitivity` evaluates a finite set of named scientific scenarios. `bounded_reweighting_robustness` instead asks for the worst case over a continuous envelope around one declared base-weight system. They answer related but different questions and neither estimates the true sampling process.

## Claim boundary

A conclusion that is stable through a declared gamma does not prove absence of observation bias. A small critical gamma does not identify the source of bias. This deterministic sensitivity envelope is not a sampling-uncertainty confidence interval and does not replace detection, effort, occupancy, survey-design, or causal sampling-process models.
