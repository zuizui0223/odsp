# Event-table workflow and baseline hierarchy

ODSP's scientific core already separates state representation from scoring. The
`odsp.workflow` module adds a small operational surface for third-party event
tables without changing any frozen empirical endpoint.

## Minimal long-table contract

Each row is one event. The caller names columns explicitly:

```python
from odsp.covariate_state_prediction import make_state_classifier
from odsp.workflow import EventTableSpec, cross_validate_state_events

spec = EventTableSpec(
    state="altitude_state",
    features=("temperature", "latitude", "longitude", "sin_hour", "cos_hour"),
    group="individual_id",
    stratum="species",
    fold="fold",
)

result = cross_validate_state_events(
    events,
    spec=spec,
    estimator=make_state_classifier("random_forest"),
    baseline="pooled",
)
```

`events` may be any iterable of row mappings. A pandas DataFrame also works
through its `to_dict(orient="records")` method, but pandas is not an ODSP
dependency.

The workflow does not infer scientific roles from names. The state, predictors,
independent group, optional stratum, optional fold and optional event-weight
column are all declared by the caller. A group is rejected if it spans multiple
folds or strata.

## Comparator is a first-class choice

For a held-out group, ODSP can report gain against either:

- `baseline="pooled"`: the training-only state marginal;
- `baseline="stratum"`: the training-only marginal within the held-out group's
  declared stratum.

When a stratum is declared, every group also receives the additive decomposition

`G_pooled = G_stratum_shift + G_context_within_stratum`

with

`G_stratum_shift = mean(log P_train(A|stratum) - log P_train(A))`

and

`G_context_within_stratum = mean(log P_model(A|X) - log P_train(A|stratum))`.

Choosing the reported baseline does not refit or otherwise alter the prediction
model.

## Training weights remain explicit

By default, a declared event-weight column is used for model fitting and held-out
scoring. A caller may instead provide an explicit training-weight policy.

ODSP includes
`equal_stratum_equal_group_training_weights`, which gives equal total training
mass to each stratum, then each independent group within stratum, then each row
within group. With `stratum="species"` and `group="individual_id"`, this is the
same weighting family used by the frozen BOP raptor endpoint.

The generic workflow does not replace that endpoint. Tests compare the generic
training marginals against the existing BOP-specific reconstruction on the same
synthetic fold, while the frozen BOP result and terminal category remain
untouched.

## Public workflow surface

For ordinary application code, start with these names from `odsp.workflow`:

- `EventTableSpec`
- `prepare_event_table`
- `equal_stratum_equal_group_training_weights`
- `training_state_baselines`
- `cross_validate_state_events`

Lower-level ODSP modules remain available for custom learners, state geometries,
scoring and diagnostics, but users do not need to assemble support tensors by
hand for a standard long-table workflow.
