# ODSP continuous scalar state prediction v1

Discrete state prediction answers questions such as “which altitude bin?” or “which time bin?”. For genuinely continuous scalar responses, ODSP can instead retain the measurement scale and predict a density:

```text
p(a | X)
```

where `a` may be altitude, depth or another explicitly defined real-valued ecological state.

## Native reference learner

```python
from odsp.continuous_state import fit_gaussian_continuous_state_model

model = fit_gaussian_continuous_state_model(
    X_train,
    altitude_train,
    sample_weight=weights_train,
)

pred = model.summarize(X_new, interval_level=0.90)
score = model.score(X_test, altitude_test)
```

The native learner is weighted linear regression for the conditional mean with a Gaussian residual density. It is intentionally transparent and should be treated as a reference learner rather than a universal ecological distribution.

A prediction row returns:

```text
mean altitude       126.4 m
standard deviation   42.1 m
90% interval         57.1–195.7 m
```

## Primary transfer metric

The primary score is the continuous analogue of the finite-state ODSP gain:

```text
Δ log density = E_heldout[log p_train(a | X) - log p_train(a)]
```

The comparator `p_train(a)` is estimated from the same training sample but discards contextual organization. Positive gain means the contextual continuous-state density predicts independently held-out states better than the training marginal density.

`model.score(...)` also reports:

- CRPS and CRPS improvement over the marginal density;
- RMSE and RMSE improvement over the marginal mean.

CRPS and RMSE are complementary diagnostics. They do not override a conflicting primary held-out log-density gain.

## Independent groups

```python
from odsp.continuous_state import score_continuous_state_groups

grouped = score_continuous_state_groups(
    model,
    X_test,
    altitude_test,
    individual_id,
)
```

Groups are scored separately. `generalizing` requires every held-out group to have positive density gain, `non_generalizing` requires every group to be non-positive, and mixed signs remain `mixed`.

## External density learners

ODSP does not require the Gaussian reference learner. Any method that can evaluate its conditional density and lower-information training marginal density at the realized held-out state can use the same primary score:

```python
from odsp.continuous_state import score_continuous_log_density_gain

score = score_continuous_log_density_gain(
    conditional_log_density=log_p_a_given_x,
    marginal_log_density=log_p_a,
)
```

Possible upstream methods include distributional regression, Bayesian conditional-density models, mixture-density neural networks, heteroscedastic Gaussian models and normalizing flows.

## Response-unit invariance

For a positive affine change of measurement units `a' = c a + d`, both conditional and marginal densities receive the same Jacobian term. Therefore their log-density **gain** should be unchanged. The known-truth benchmark verifies this numerically. CRPS and RMSE, in contrast, scale with the measurement unit and should be interpreted on that scale.

## Semantic boundary

A continuous numeric field is not automatically a valid ecological-state axis. In particular:

- altitude above mean sea level is not automatically height above ground;
- an observation timestamp is not automatically unbiased activity time;
- a positive held-out density gain does not establish a causal environmental effect;
- continuous density prediction does not remove observation or detection bias.

## Known-truth benchmark

The frozen benchmark uses three regimes:

1. stable conditional organization: training and test share the same continuous response relationship;
2. unorganized/null: covariates carry no state information;
3. shifted organization: held-out response structure is reversed relative to training.

It requires all stable replicates to have positive density gain, all shifted replicates to have negative gain, null mean gain to remain near zero, affine response-unit invariance, and approximately nominal Gaussian interval coverage under correct specification.

Run:

```bash
python scripts/run_continuous_state_benchmark.py
```

## Not yet covered

This first continuous implementation is univariate and non-circular. Circular local time and multivariate continuous state densities are separate extensions. The native reference learner is homoscedastic; richer heteroscedastic learners can already be evaluated through the external log-density interface, but are not fitted by the dependency-light core yet.
