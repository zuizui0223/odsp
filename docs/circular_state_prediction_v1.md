# ODSP circular state prediction v1

Circular ecological states should not be cut at an arbitrary origin. For local clock time, for example, `23:50` and `00:10` are close even though their ordinary numeric difference is almost 24 hours.

ODSP therefore supports a periodic density target:

```text
p(t | X)
```

with an explicit caller-declared period such as 24 hours.

## Native reference learner

```python
from odsp.circular_state import fit_von_mises_circular_state_model

model = fit_von_mises_circular_state_model(
    X_train,
    local_time_hours,
    period=24.0,
    sample_weight=weights_train,
)

pred = model.summarize(X_new, interval_level=0.90)
score = model.score(X_test, local_time_test)
```

The native model is intentionally transparent:

1. transform the circular state to angle `theta = 2*pi*t/period`;
2. fit weighted linear regressions to `cos(theta)` and `sin(theta)`;
3. recover a conditional mean direction;
4. calibrate a circular residual offset;
5. estimate a von Mises residual concentration from the weighted residual resultant length;
6. compare that conditional density with a von Mises training marginal density.

It is a reference learner, not a universal biological activity distribution.

## Primary transfer metric

The primary score is

```text
Delta log density = E_heldout[log p_train(t | X) - log p_train(t)]
```

Positive gain means that contextual circular organization predicts the independently held-out circular state better than the lower-information training marginal density.

The Jacobian from angle to the caller's state unit is included in both densities. It therefore cancels from the gain, which is why the same time represented as hours with period 24 or minutes with period 1440 should have the same gain.

## Circular error and prediction arcs

`model.score(...)` also returns circular mean absolute error and improvement over the marginal circular mean.

`model.summarize(...)` reports:

- mean circular state;
- von Mises concentration and residual resultant length;
- circular standard deviation on the caller's original scale;
- a symmetric prediction arc derived from the weighted training residual distribution;
- whether that arc crosses the declared period origin.

An interval such as `23.2–00.8` is therefore represented as a wrapping circular arc rather than an impossible negative or >24-hour interval.

## Midnight-safe distance

```python
from odsp.circular_state import circular_distance

circular_distance([23.9], [0.1], period=24.0)
# approximately 0.2 hours
```

## Independent groups

```python
from odsp.circular_state import score_circular_state_groups

grouped = score_circular_state_groups(
    model,
    X_test,
    local_time_test,
    individual_id,
)
```

Independent groups remain separate. All-positive gains are required for `generalizing`; all non-positive gains give `non_generalizing`; conflicting signs remain `mixed`.

## External circular density learners

A richer upstream model does not need to use the native von Mises reference learner. If it can provide conditional and training-marginal log density at each realized held-out state, use:

```python
from odsp.circular_state import score_circular_log_density_gain

score = score_circular_log_density_gain(
    conditional_log_density=log_p_t_given_x,
    marginal_log_density=log_p_t,
)
```

This makes Bayesian circular models, mixtures and other circular density estimators compatible with the same ODSP transfer score.

## Known-truth benchmark

The frozen benchmark checks three regimes using a 24-hour state:

1. stable conditional circular organization;
2. a null/unorganized process where context does not shift the circular state;
3. a shifted process where the held-out mean state is displaced by half a period.

Before result interpretation, the following obligations were fixed:

- all stable replicates must have positive held-out density gain;
- all half-period-shifted replicates must have negative gain;
- null mean gain must lie within ±0.02 of zero;
- a common phase-origin shift must preserve gain to `<=1e-10`;
- equivalent hour/minute representation must preserve gain to `<=1e-10`;
- a nominal 90% residual prediction arc must achieve empirical coverage between 0.87 and 0.93 under the stable same-process model.

The first benchmark execution used seed `20260905`, 128 replicates, 800 training rows and 1,600 held-out rows. It passed every frozen obligation:

```text
stable-generalizing
  positive gain             128 / 128
  mean Delta log density    +0.3595903006
  circular-MAE improvement  +0.4973134797 h

unorganized / null
  mean Delta log density    -0.0013889160

half-period shifted
  negative gain             128 / 128
  mean Delta log density    -7.2456082807

phase-origin invariance
  absolute gain error        0.0

hours -> minutes invariance
  absolute gain error        8.88e-16

nominal 90% circular arc
  empirical coverage         0.8942
```

Canonical values and original CI provenance are frozen in `CIRCULAR_STATE_PREDICTION_VALIDATION_RECEIPT.json`. The receipt test reruns the benchmark without touching any public empirical endpoint.

Run:

```bash
python scripts/run_circular_state_benchmark.py
```

## Semantic boundary

Circular prediction does not make observation time equal to latent biological activity time. In particular:

- local clock time is not automatically solar time;
- camera-detection time is not automatically unbiased activity time;
- positive circular density gain is not evidence of competition or temporal displacement;
- the von Mises reference is not a universal activity distribution;
- circular modeling does not remove observation or detection bias.

Joint height-time density, multivariate circular responses and causal temporal attribution are separate extensions.
