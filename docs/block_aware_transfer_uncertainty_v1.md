# Block-aware transfer uncertainty

ODSP ordinarily classifies each independent validation group's held-out conditional-minus-marginal log-score gain by sign. This module adds a separate uncertainty audit so a tiny positive point estimate or many correlated rows cannot automatically authorize transferability.

## API

```python
from odsp.block_aware_transfer_uncertainty import (
    audit_block_aware_transfer_uncertainty,
)

result = audit_block_aware_transfer_uncertainty(
    row_gain,
    groups=individual_id,
    blocks=day_id,
    confidence_level=0.95,
    bootstrap_draws=2000,
    minimum_blocks_per_group=8,
)
```

Caller-declared blocks are resampled with replacement within each independent validation group and all rows from a sampled block remain together. If `blocks=None`, each row is treated as independent and `row_independence_assumed=True` is recorded explicitly.

## Decision rule

For each group:

- lower CI bound > 0 -> `robust_positive`;
- upper CI bound <= 0 -> `robust_nonpositive`;
- interval crosses zero -> `uncertain`;
- fewer than the declared minimum blocks -> `unavailable`.

`robust_generalizing` requires every group to be `robust_positive`. A positive pooled mean or positive point estimate cannot override an uncertain, unavailable or failed group.

## Why blocks matter

Repeated GPS fixes, images or sensor rows can make a row-wise bootstrap look much more certain than the number of independent ecological units warrants. The frozen known-truth benchmark therefore contains 800 repeated rows generated from only eight distinct blocks. Row-wise resampling gives a positive lower bound, whereas the scientifically relevant block bootstrap crosses zero and remains `uncertain`.

## Claim boundary

This is a percentile block-bootstrap uncertainty audit, not an exact finite-sample theorem. Validity depends on choosing scientifically defensible blocks. It does not repair a bad block definition, remove observation bias, identify mechanism or guarantee future performance after distribution shift.
