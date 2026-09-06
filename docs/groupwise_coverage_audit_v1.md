# Group-wise coverage and trust audit

ODSP conformal and interval modules provide marginal coverage targets under their stated assumptions. This audit layer asks a different question: **where does empirical coverage fail across caller-declared ecological or independence groups?**

It does not claim conditional-coverage guarantees.

## Group-wise coverage

```python
from odsp.groupwise_coverage_audit import audit_groupwise_coverage

audit = audit_groupwise_coverage(
    covered,
    site_ids,
    target_coverage=0.90,
    tolerance=0.03,
)
```

The result reports pooled coverage and every group separately. A pooled value near 0.90 cannot rescue a site, year, species or individual whose empirical coverage is outside tolerance.

Possible descriptive categories are:

- `calibrated`: every declared group is within tolerance;
- `mixed`: some groups pass and some fail;
- `non_calibrated`: no group passes.

These are audit labels, not finite-sample conditional-coverage guarantees.

## Crossed transfer + coverage trust

```python
from odsp.groupwise_coverage_audit import audit_groupwise_forecast_trust

trust = audit_groupwise_forecast_trust(
    conditional_log_density,
    training_marginal_log_density,
    covered,
    independent_group_ids,
)
```

A group is trusted only when both are true:

1. its held-out conditional-minus-marginal log-density gain is positive;
2. its empirical coverage lies within the declared tolerance.

Dataset-level `trusted_admissible` requires every group to pass both conditions. Positive pooled gain cannot override a failed group, and good pooled coverage cannot override a local coverage failure.

## Novelty strata

The same coverage audit can be applied to categories produced by `odsp.prediction_novelty`, for example `in_domain`, `novel`, and `strict`. A coverage decline across these strata is useful evidence about where the prediction system becomes unreliable, but it is not proof that novelty caused the error and novelty is not itself an error probability.

## Known-truth benchmark

The frozen benchmark includes a deliberately deceptive case with pooled coverage ~0.90 while one independent group has coverage 0.60. ODSP must keep the group-wise result `mixed`. It also checks an all-calibrated regime, monotone coverage degradation across novelty strata, positive-transfer/bad-coverage and good-coverage/failed-transfer cases, group-order invariance, and the absence of any aggregate confidence score.

## Claim boundary

Group-wise empirical coverage audits do not establish conditional coverage, causality, biological validity or observation-bias correction. Group labels and tolerances are declared by the analyst and must be scientifically justified. The frozen state-prediction v4 manuscript and closed empirical endpoints remain separate from this development layer.
