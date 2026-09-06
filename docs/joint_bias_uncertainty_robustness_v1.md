# Joint bias–uncertainty robustness

This layer combines two ODSP sensitivity questions that are otherwise separate:

1. how uncertain is the held-out transfer gain when validation rows are correlated within caller-declared blocks?;
2. how much could the gain deteriorate under every row reweighting inside a declared multiplicative envelope?

For each bootstrap draw ODSP resamples whole blocks with replacement and then solves the **worst** and **best** possible weighted mean gain inside `[1/gamma, gamma]` relative to the declared base weights.

```python
from odsp.joint_bias_uncertainty_robustness import (
    audit_joint_bias_uncertainty_robustness,
)

result = audit_joint_bias_uncertainty_robustness(
    row_gain,
    groups,
    blocks,
    base_weight=base_weight,
    gamma=2.0,
    confidence_level=0.95,
    bootstrap_draws=1000,
    minimum_blocks_per_group=8,
)
```

For every independent group the result retains:

- the declared-weight point mean;
- deterministic worst/best gain under the full reweighting envelope;
- percentile bounds for the **bootstrap distribution of worst-case gain**;
- percentile bounds for the bootstrap distribution of best-case gain;
- `joint_robust_positive`, `joint_robust_nonpositive`, `envelope_sensitive`, `uncertain`, or `unavailable`.

A group is jointly robust-positive only when the lower confidence bound of the bootstrap **worst-case** gain remains above zero. Thus neither a positive point estimate nor a positive deterministic worst-case estimate alone is sufficient.

At `gamma=1`, the reweighting envelope collapses and the method reduces to the existing block-aware transfer uncertainty audit, up to floating-point precision.

## Interpretation boundary

This procedure is deliberately conservative but is not an exact finite-sample theorem. Its result depends on both the scientific block definition and the user-declared gamma envelope. It does not infer gamma, identify the sampling mechanism, correct observation bias automatically, repair a bad block definition, or guarantee performance under future distribution shift.
