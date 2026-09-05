# ODSP trusted joint forecast v1

This interface combines the main post-v4 ODSP prediction components without collapsing them into one confidence score.

A fitted object keeps four roles separate:

```text
training rows
  -> joint density model p(z,t|X)
  -> environmental novelty reference

independent calibration rows
  -> split-conformal height x time prediction region only

new forecast rows
  -> joint state summary + conformal region + novelty warning

independent validation rows
  -> joint/coupling log-density gain and grouped transferability
```

## Fit

```python
from odsp.trusted_joint_forecast import fit_trusted_joint_state_forecaster

forecast_model = fit_trusted_joint_state_forecaster(
    X_train,
    height_train,
    time_train,
    X_calibration,
    height_calibration,
    time_calibration,
    period=24.0,
    total_miscoverage=0.10,
)
```

The calibration split does **not** refit the joint density model or the novelty cloud. It is used only to calibrate the Bonferroni split-conformal height x time region.

The joint density summary and conformal envelope deliberately use different height summaries. The joint ecological forecast can report height conditional on the predicted time mode, while the Bonferroni coverage envelope uses the marginal component prediction `z|X` together with `t|X`. This keeps the coverage construction separate from the autoregressive joint-density interpretation.

## Forecast

```python
rows = forecast_model.forecast(X_new)
```

Each row contains separate fields for:

```text
model state prediction
  time mode
  model-based time arc
  height mean at predicted time mode
  model-based height interval

conformal uncertainty
  joint target coverage
  conformal height interval
  conformal circular time arc

prediction domain
  novelty ratio
  in_domain / novel / strict_extrapolation
  outside-feature indices
```

There is intentionally no single `confidence` field. Probability/density, coverage calibration, environmental novelty and transferability answer different questions.

## Joint draws

```python
height_draws, time_draws = forecast_model.sample_joint(
    X_new,
    draws_per_row=500,
)
```

These paired draws preserve the autoregressive joint prediction `p(z,t|X)` and can be used to render a state-resolved map cell as a height-time distribution rather than a scalar suitability value.

## Validation

```python
score = forecast_model.score(X_test, height_test, time_test)
coverage = forecast_model.evaluate_conformal(X_test, height_test, time_test)
profile = forecast_model.score_groups(
    X_test,
    height_test,
    time_test,
    individual_id,
)
```

The density score retains separate contextual joint gain and directional height-time coupling gain. Group scoring remains conservative: a failed individual cannot be rescued by a pooled positive average.

## Novelty and transfer are not interchangeable

A forecast can have positive transfer on an independent validation set while a particular new row is a strict extrapolation. Conversely, an in-domain row does not guarantee state-prediction transfer. ODSP therefore reports these diagnostics side by side instead of using novelty as a probability correction.

## Known-truth integration benchmark

The end-to-end synthetic process uses separate training, calibration and test splits. It requires:

- the joint model to contain training rows only;
- same-process joint and coupling density gains to be positive;
- Bonferroni joint coverage to remain above the frozen finite-sample lower tolerance of 0.88;
- at least 90% of bounded same-domain queries not to be strict extrapolation;
- all strongly shifted environmental queries to be strict extrapolation;
- forecast rows to expose no aggregate confidence score.

The first successful run returned:

```text
joint log-density gain             +2.2874331924
coupling log-density gain          +0.4322539619
Bonferroni joint coverage           0.9400
same-domain non-strict fraction     1.0000
shifted strict-extrapolation        1.0000
training/calibration split          preserved
aggregate confidence field          absent
```

### Pre-green Bonferroni contract correction

The original integration contract mistakenly imposed an upper coverage limit of 0.93. A failed diagnostic run produced valid conservative coverage of 0.94 while every other obligation passed. Because Bonferroni supplies a simultaneous **coverage lower bound**, not an upper-bound guarantee, forcing the synthetic generator or model to reduce valid coverage would have been result-driven tuning.

Before any green validation receipt was created, the contract was therefore amended to remove only that mathematically invalid upper bound. The generator, seed, split sizes, gain thresholds and novelty thresholds were unchanged. The amendment is recorded in `TRUSTED_JOINT_FORECAST_CONTRACT_AMENDMENT_2026-09-05.json`.

Run:

```bash
python scripts/run_trusted_joint_forecast_benchmark.py
```

The canonical successful values are pinned in `TRUSTED_JOINT_FORECAST_VALIDATION_RECEIPT.json` and replayed exactly by the receipt test.

## Scientific boundary

The integrated object is a presentation and workflow layer, not a new causal model. Conformal coverage does not imply transferability, novelty is not an error probability, positive coupling gain does not establish a mechanism, and state semantics must still be biologically justified. Absolute altitude is not automatically height above ground, and clock time is not automatically latent activity time.
