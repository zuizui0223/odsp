# Sampling-weight sensitivity audit

ODSP does **not** infer a correct observation, effort, or detection model in this layer. Instead, the analyst supplies two or more scientifically plausible non-negative weighting scenarios on the **same held-out validation rows**. ODSP then asks whether the transfer conclusion is stable across those scenarios.

Each scenario is evaluated with the existing block-aware transfer uncertainty audit. Rows inside a caller-declared block remain together during bootstrap resampling.

```python
from collections import OrderedDict
import numpy as np

from odsp.sampling_weight_sensitivity import audit_sampling_weight_sensitivity

result = audit_sampling_weight_sensitivity(
    row_gain,
    groups,
    OrderedDict([
        ("uniform", np.ones(len(row_gain))),
        ("effort_adjusted", effort_weight),
        ("inverse_effort", 1.0 / effort_weight),
    ]),
    blocks=block_ids,
    confidence_level=0.95,
    bootstrap_draws=2000,
    seed=20260906,
    minimum_blocks_per_group=8,
)
```

The output retains every scenario separately, including:

- point transfer category;
- robust block-bootstrap category;
- minimum group lower confidence bound;
- maximum group upper confidence bound;
- overall and minimum-group Kish effective sample size;
- full block-aware audit.

The across-scenario summary is conservative:

- every scenario `robust_generalizing` -> `weight_robust_generalizing`;
- every scenario `robust_non_generalizing` -> `weight_robust_non_generalizing`;
- every scenario `unavailable` -> `stable_unavailable`;
- disagreement among robust categories -> `weight_sensitive`;
- any other single stable category is reported as `stable_<category>`.

No scenario is averaged with another, and one scenario cannot rescue another.

## Interpretation boundary

A stable result means only that the conclusion is stable over the **declared set of plausible weights**. It does not prove absence of observation bias. A sensitive result does not identify which weighting scheme is correct or which biological or sampling process caused the sensitivity.

This layer does not replace occupancy/detection models, inverse-probability weighting design, survey-effort models, or causal sampling-process models. It is a sensitivity audit over caller-supplied alternatives.
