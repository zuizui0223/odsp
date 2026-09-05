# Forecast model comparison v1

ODSP can compare alternative probabilistic ecological-state forecasters on the **same independent validation rows** without compressing transferability, calibration and sharpness into one confidence score.

## Candidate evidence

For each learner, provide realized held-out:

- conditional log density `log p(state | context)`;
- the corresponding training-marginal comparator `log p(state)`;
- independent group labels such as individual, site, year or region.

Optional trust evidence is:

- whether the realized state fell inside the declared prediction set/region;
- the target marginal coverage;
- prediction-set or prediction-region size;
- sample weights.

The learner itself can be RF, multinomial regression, a Bayesian density model, a neural density model, a joint ODSP reference model or another probabilistic forecaster. The comparison layer only consumes held-out evidence.

## Decision order

1. Compute row-level conditional-minus-marginal log-density gain.
2. Compute a mean gain independently inside every declared group.
3. Require all group gains to be positive for `generalizing`; a pooled positive mean cannot rescue one failing group.
4. If coverage evidence is supplied, require empirical coverage to be within the declared tolerance of the target before a candidate becomes `trusted_admissible`.
5. Compare trusted candidates on held-out log-density gain and prediction-region sharpness.

There is no aggregate confidence score.

## Example

```python
import numpy as np
from odsp.forecast_model_comparison import (
    evaluate_forecast_candidate,
    compare_forecast_candidates,
)

candidate = evaluate_forecast_candidate(
    "model-A",
    conditional_log_density=log_p_conditional,
    marginal_log_density=log_p_marginal,
    groups=individual_id,
    covered=inside_prediction_region,
    target_coverage=0.90,
    region_size=prediction_region_size,
)

result = compare_forecast_candidates([candidate, other_candidate])
print(result.recommended_by_log_score)
print(result.pareto_front_names)
```

## Interpretation

`transfer_admissible` means all independent groups have positive held-out conditional-versus-marginal gain. `trusted_admissible` additionally requires audited coverage within tolerance. `pareto_front_names` reports non-dominated trusted candidates when log-density gain is maximized while coverage error and prediction-region size are minimized.

The recommended candidate is the trusted-admissible candidate with the largest held-out log-density gain. This recommendation is conditional on the declared validation design; it is not evidence that the learner is the true biological mechanism.

## Claim boundary

- Good marginal coverage does not imply transferability.
- Positive transfer does not imply calibration.
- A sharp region cannot compensate for bad coverage.
- A pooled mean cannot override a failed independent group.
- A selected predictor is not automatically causal, mechanistic or biologically complete.
- Observation and detection biases are not automatically removed.
- The framework does not emit one aggregate confidence score.

The frozen v4 manuscript, its anonymous review bundle and all closed Tawaki, bat, Serengeti, MH_ANTWERPEN and BOP_RODENT endpoints remain unchanged.
