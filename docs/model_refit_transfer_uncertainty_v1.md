# Model-refit transfer uncertainty

Use `odsp.model_refit_transfer_uncertainty.audit_model_refit_transfer_uncertainty`
to ask whether a result from one fitted model survives a declared collection of
training-only refits. It accepts a numeric matrix of shape `(refits, held_out_rows)`.
Each entry is the log density/probability of the observed state under the refit
minus the log density/probability under its appropriately paired training-only
comparator. Discrete, continuous, circular and joint state predictors can all
supply such gains, provided their density measures and targets agree.

```python
from odsp.model_refit_transfer_uncertainty import audit_model_refit_transfer_uncertainty

result = audit_model_refit_transfer_uncertainty(
    gains,                         # refits x the SAME held-out observations
    individual_ids,                # one independent-group label per observation
    blocks=day_ids,                 # one dependence-block label per observation
    refit_ids=training_refit_ids,   # unique stable IDs; not row IDs
    reference_refit_id=training_refit_ids[0],
    nested_draws=4000,
    minimum_refits=8,
    minimum_blocks_per_group=8,
)
print(result.reference_fit_category)
print(result.refit_sign_stability)
print(result.refit_aware_category)
```

The default reference is the lexicographically first refit ID, not the best
performing refit. Without supplied IDs, positional IDs are generated. Reordering
requires retaining IDs, including any explicitly declared reference. Models must
not be selected by their performance on these validation rows.

## What is computed

One refit is drawn uniformly for an entire Monte Carlo replicate. That SAME refit
is used for every validation group in the replicate. Within each group, entire
caller-declared blocks are independently sampled with replacement. Conditional
and comparator gains remain paired. This retains shared model variability across
groups; selecting a different refit independently for each group would erase it.

The centre is the equal-weight mean of the refits' original group mean gains.
The nested spread is NOT divided by the square root of the number of refits:
more supplied refits refine the empirical mixture, not the independent sample
size of the ecological validation experiment. The output separately retains:

- the existing simultaneous audit of the declared reference fit;
- per-refit group means, sign counts, and between-refit standard deviation;
- nested marginal percentile intervals and standardized max-t intervals;
- insufficient-refit/block outcomes, which prevent global admission.

The max-t statistic standardizes deviations by each group's estimated nested
standard deviation, held fixed across draws. This is not a double-bootstrap
method re-estimating a new standard error inside every draw. Identical refits
numerically reduce to the existing simultaneous audit by reusing the same
block-sampling random streams. Unique refit IDs do not prove independent fitting.
Zero row weights are allowed within positive-mass blocks; an entirely zero-mass
block or group is rejected explicitly.

## Scope of the result

**This is an empirical refit-ensemble sensitivity audit, not a universal confidence
guarantee for retraining.** Its centre describes the declared empirical mixture.
A finite list of refits is not automatically a bootstrap sampling distribution or
a posterior. The interval describes this mixture plus resampled validation blocks;
it is not a confidence interval for the mean of R independent models. Validation
of population coverage under any specific training-resampling design is additional
work, not established by the deterministic fixtures.

This layer does not fit models, infer a resampling scheme, verify observational
alignment from raw identities, correct detection bias, or check train/test leakage
from a gain matrix. Construct refits on training data only; keep tuning, ensemble
selection, conformal calibration, and final evaluation data roles separate.
Repeated seeds on the same training set capture algorithmic variability, not all
training-sample uncertainty. The reference/comparator must use compatible measures
and observations. Dependent validation groups need a different joint resampling
scheme; shared refit selection alone does not fix their dependence.

Simultaneous interval coverage and testing a single conjunction ('all group gains
are positive') are distinct inferential goals. The latter is an intersection-union
problem and does not automatically require a multiplicity correction. The max-t
layer here targets the former; it must not be described as repairing an inevitable
false-positive inflation in every all-groups-positive test.

No existing `assess_state_forecast` admission, v4 manuscript, or empirical endpoint
is silently changed. This module is an explicit opt-in audit. A reference pass
cannot overwrite an uncertain, mixed, nonpositive, or unavailable refit-aware
result. There is no aggregate confidence score.

## Reproducible examples and checks

`python examples/model_refit_transfer_demo.py --output demo.json` actually refits
Gaussian regressions on resampled synthetic training blocks and scores the same
independent synthetic validation observations. This is an implementation example,
not new evidence from a biological dataset.

`python scripts/run_model_refit_transfer_uncertainty_benchmark.py --output benchmark.json`
runs the 15 obligations fixed in `MODEL_REFIT_TRANSFER_UNCERTAINTY_CONTRACT.json`.
They include a positive reference fit whose gains reverse in other refits,
identical-refit reduction, insufficient refits/blocks, order invariance, and weight
scaling. Passing fixtures establishes those checks, not universal calibration.

Methodological background: Romano and Wolf (2005), *Stepwise Multiple Testing as
Formalized Data Snooping*, Econometrica 73:1237-1282,
DOI 10.1111/j.1468-0262.2005.00615.x, discusses studentization and dependence-aware
resampling. ODSP's empirical refit mixture is NOT claimed to inherit that paper's
asymptotic theorem without verifying its assumptions.
