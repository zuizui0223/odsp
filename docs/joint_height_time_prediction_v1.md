# ODSP joint continuous-circular state prediction v1

ODSP can predict a continuous state and a circular state jointly rather than returning two unrelated marginal summaries. The reference factorization is

```text
p(z,t | X) = p(t | X) p(z | X,t)
```

where `z` may be a genuinely measured continuous height/depth state and `t` an explicitly periodic state such as local clock time.

## Why two gains are needed

A joint model answers two different questions.

### Contextual joint value

```text
G_joint = E_heldout[log p_train(z,t|X) - log p_train(z,t)]
```

The X-free comparator is modeled as `p_train(t) p_train(z|t)`, so it preserves overall height-time organization while discarding context `X`. Positive `G_joint` therefore asks whether context improves prediction of the joint state.

### Directional height-time coupling value

```text
G_coupling = E_heldout[log p_train(z|X,t) - log p_train(z|X)]
```

This asks whether knowing the realized circular state improves continuous-state prediction after context is already known. It is directional and predictive. It is not a symmetric dependence measure and does not establish a mechanism or causal effect.

## Native reference learner

```python
from odsp.joint_state import fit_joint_continuous_circular_state_model

model = fit_joint_continuous_circular_state_model(
    X_train,
    height_train,
    local_time_train,
    period=24.0,
    sample_weight=weights,
)

score = model.score(X_test, height_test, local_time_test)
summary = model.summarize(X_new)
height_draws, time_draws = model.sample_joint(X_new, draws_per_row=500)
```

The dependency-light reference model combines:

- the circular harmonic-regression/von-Mises model for `p(t|X)`;
- a Gaussian model for `p(z|X)`;
- a Gaussian model with `X + sin(t) + cos(t)` for `p(z|X,t)`;
- a time-only Gaussian model for the X-free comparator `p(z|t)`.

Richer external joint-density models can use the same ODSP scoring interface if they provide realized held-out conditional, marginal-joint and optionally factorized-contextual log densities.

## Prediction output

A query row can return:

```text
most likely time       21.8 h
90% circular time arc  19.4–00.7 h  (wraps origin)
height at time mode     88.2 m
90% height interval     44.1–132.3 m
```

`sample_joint(...)` is more general: it draws paired `(z,t)` values from the full autoregressive reference density. These draws can be used to visualize the predicted height-time niche within a map cell instead of collapsing it to one suitability value.

## Independent groups

```python
from odsp.joint_state import score_joint_state_groups

profile = score_joint_state_groups(
    model,
    X_test,
    height_test,
    local_time_test,
    individual_id,
)
```

Joint contextual gain and directional coupling gain receive separate conservative group classifications. A positive joint result cannot rescue failed coupling, and a positive coupling result cannot rescue failed contextual transfer.

## Frozen known-truth benchmark

Before numerical interpretation, the benchmark contract fixes five regimes:

1. stable context and stable height-time coupling;
2. no contextual organization, but real height-time coupling;
3. contextual organization, but no extra height-time coupling;
4. held-out context/time organization shifted relative to training;
5. held-out height-time coupling reversed relative to training.

The frozen obligations require the method to recover these separations and to preserve both gains under:

- a common circular phase-origin shift;
- equivalent hours-to-minutes time units;
- a positive affine change of continuous-state units.

The first execution used seed `20260905`, 128 replicates, 800 training rows and 1,600 held-out rows. Every frozen obligation passed:

```text
stable context + coupling
  joint gain                 +0.7162669716   (128/128 positive)
  coupling gain              +0.1099501637   (128/128 positive)

context-unorganized, coupled
  joint gain                 -0.0025560732   (~0)
  coupling gain              +0.0913059799   (128/128 positive)

contextual, uncoupled
  joint gain                 +0.7200183888   (128/128 positive)
  coupling gain              -0.0012475738   (~0)

context shifted
  joint gain                 -8.7529080748   (128/128 negative)
  coupling gain              +5.4661655716   (128/128 positive)

coupling shifted
  joint gain                 -2.5760347895
  coupling gain              -1.7579250461   (128/128 negative)
```

The context-shift result is deliberately informative: the height-time relationship remains useful when the realized time is known, yet the contextual joint forecast fails because the time organization no longer transfers. ODSP therefore does not collapse these into one notion of “multidimensional prediction success.”

All representation invariance obligations also passed:

```text
common time phase-origin shift
  joint gain error            0.0
  coupling gain error         0.0

hours -> minutes
  joint gain error            0.0
  coupling gain error         0.0

positive affine height units
  joint gain error            0.0
  coupling gain error         4.44e-16
```

The canonical values and original workflow artifact are frozen in `JOINT_HEIGHT_TIME_PREDICTION_VALIDATION_RECEIPT.json`. The receipt test reruns the benchmark without opening any public empirical endpoint.

Run:

```bash
python scripts/run_joint_state_benchmark.py
```

## Semantic boundary

The words `height` and `time` are placeholders for declared state semantics. In particular:

- absolute altitude is not automatically height above ground;
- observation clock time is not automatically latent activity time;
- `G_coupling > 0` does not imply temporal control of height, competition, displacement or any other causal mechanism;
- the autoregressive factorization is a predictive decomposition, not a claim that time causally precedes height;
- joint density prediction does not remove observation or detection bias.

The current implementation covers one continuous and one circular state. Higher-dimensional vector densities and causal attribution remain separate extensions.
