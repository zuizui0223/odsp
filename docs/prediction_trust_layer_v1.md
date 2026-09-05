# ODSP prediction trust layer v1

The state-prediction core answers **which ecological state, with what probability?**
The trust layer adds three separate questions:

1. **uncertainty** — which states must remain in a calibrated prediction set?
2. **novelty** — is the query environment inside the training domain, multivariately novel, or in strict extrapolation?
3. **generalization profile** — at which independent levels does the held-out state prediction transfer?

These diagnostics do not replace the primary ODSP state probability or held-out log-score gain. They describe when and where that prediction should be trusted.

## 1. Split-conformal state prediction sets

Use a calibration sample that was not used to fit the upstream state learner.

```python
from odsp import fit_state_conformal_calibrator

# p_cal and p_test are normalized rows from any probabilistic state learner.
cal = fit_state_conformal_calibrator(
    p_cal,
    y_cal,
    classes=("low", "mid", "high", "very_high"),
    miscoverage=0.10,
)

sets = cal.prediction_sets(p_test)
report = cal.evaluate(p_test, y_test)
```

For nominal 90% coverage, `sets[i]` is the set of altitude/time/behaviour states retained for row `i`. The implementation uses split conformal nonconformity `1 - p(true_state)` and the finite-sample conformal quantile.

**Claim boundary:** marginal finite-sample coverage requires exchangeability between calibration and target rows. It is not a guarantee of conditional coverage, and distribution shift can reduce empirical coverage. ODSP deliberately reports that failure rather than hiding it.

## 2. Environmental novelty and extrapolation

```python
from odsp import fit_environmental_novelty_model

novelty = fit_environmental_novelty_model(X_train, reference_quantile=0.95)
rows = novelty.summarize(X_new)
```

Each row receives:

- `nearest_scaled_distance` — nearest training point after training-standardization;
- `novelty_ratio` — distance divided by the frozen training leave-one-out reference distance;
- `outside_feature_indices` — predictors outside their univariate training ranges;
- `category` — `in_domain`, `novel`, or `strict_extrapolation`.

`strict_extrapolation` takes priority whenever any feature lies outside the training range. A point can still be `novel` while every individual predictor remains inside its training range if the multivariate combination is unusual.

The score is invariant to positive affine rescaling of predictors because centring and scaling are learned from the same training data.

**Claim boundary:** novelty is a warning/diagnostic. It neither repairs an extrapolated prediction nor proves that the prediction is wrong.

## 3. Multi-level generalization profile

A single `mixed` label may hide useful structure. Generalization profiles retain the same out-of-sample row-level log-score gains but aggregate them separately at caller-declared independent levels.

```python
from odsp import generalization_profile_from_probability_field

profile = generalization_profile_from_probability_field(
    p_oof,
    y,
    classes=classes,
    marginal_probability=train_marginal,
    groupings={
        "individual": individual_id,
        "site": site_id,
        "year": year,
        "species": species,
    },
)
```

Possible output:

```text
individual  mixed          27/30 positive
site        generalizing   12/12 positive
year        mixed           4/5 positive
species     generalizing    4/4 positive
```

Every level is a separate estimand. A positive species-level aggregation cannot erase a negative individual-level result. The descriptive level mean is never allowed to rescue a conflicting group.

**Critical requirement:** `p_oof` must be genuinely out of sample (cross-fitted or prospectively held out). In-sample probabilities cannot support a transfer claim.

## 4. Recommended combined output

For one query row, an eventual ODSP application can report:

```text
state distribution
  low       0.08
  mid       0.20
  high      0.63
  very high 0.09

90% conformal state set
  {mid, high}

environmental domain
  novelty ratio 0.74
  in_domain

transfer profile
  new individual  mixed
  new site        generalizing
  new year        mixed
```

The three layers answer different questions and should not be collapsed into one confidence number.

## 5. Frozen known-truth benchmark

`run_prediction_trust_benchmark(seed=20260905)` checks that:

- exchangeable conformal coverage is near nominal 0.90;
- a deliberately shifted outcome distribution produces degraded coverage rather than a false guarantee;
- strongly shifted covariates are marked as strict extrapolation;
- novelty scores/categories are invariant to positive affine feature rescaling;
- a fine-level mixed transfer result remains visible even when a coarser grouping is fully positive.

Run with:

```bash
python scripts/run_prediction_trust_benchmark.py
```

The dedicated `prediction-trust-layer` workflow tests the API and uploads the machine-readable benchmark artifact.

## 6. What is still not implemented

This trust layer still assumes a finite discrete ecological state response. Continuous densities such as `p(height | X)` or circular `p(time | X)` are a separate next development step. Causal attribution and automatic correction of detection/observation bias are also outside this layer.
