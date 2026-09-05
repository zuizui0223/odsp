# ODSP continuous and circular conformal uncertainty v1

The continuous and circular state predictors can return model-based intervals or arcs, but those summaries depend on the reference density being well specified. This layer adds split-conformal prediction sets around arbitrary upstream point/scale predictions.

The guarantee is deliberately narrow: **finite-sample marginal coverage under exchangeability between the calibration and target rows**. It is not conditional-coverage or distribution-shift robustness.

## Continuous state

```python
from odsp.continuous_circular_conformal import fit_continuous_conformal_calibrator

cal = fit_continuous_conformal_calibrator(
    predicted_center=mu_cal,
    observed=y_cal,
    predicted_scale=sigma_cal,
    miscoverage=0.10,
)

intervals = cal.intervals(mu_test, predicted_scale=sigma_test)
report = cal.evaluate(mu_test, y_test, predicted_scale=sigma_test)
```

With a supplied positive scale, nonconformity is

```text
abs(y - center) / scale
```

so the interval adapts to upstream heteroscedastic uncertainty. Without a scale, raw absolute residuals are used.

A positive affine response-unit change leaves the standardized conformal quantile unchanged when center, observed value and scale are transformed consistently.

## Circular state

```python
from odsp.continuous_circular_conformal import fit_circular_conformal_calibrator

cal = fit_circular_conformal_calibrator(
    predicted_center=time_cal,
    observed=time_observed_cal,
    period=24.0,
    miscoverage=0.10,
)

arcs = cal.arcs(time_test)
```

Nonconformity is the shortest circular distance from observed to predicted state. A returned arc may cross the period origin, so a 23:30 prediction can have a valid arc extending into the following clock day.

The arc is invariant to a common phase-origin shift. Equivalent hours/minutes representations scale the half-width with the period unit while preserving the represented subset of the circle.

## Joint height-time prediction region

For a joint continuous-circular prediction, the first implementation uses a transparent Bonferroni construction:

```python
from odsp.continuous_circular_conformal import (
    fit_joint_bonferroni_conformal_calibrator,
)

cal = fit_joint_bonferroni_conformal_calibrator(
    height_center=h_cal_pred,
    height_observed=h_cal,
    time_center=t_cal_pred,
    time_observed=t_cal,
    height_scale=h_cal_scale,
    period=24.0,
    total_miscoverage=0.10,
)

regions = cal.regions(
    h_test_pred,
    t_test_pred,
    height_scale=h_test_scale,
)
```

The total `alpha=0.10` is split equally, giving 95% component prediction sets. Their Cartesian product has a Bonferroni simultaneous marginal-coverage lower bound of 90% under the exchangeability assumptions.

This is **not** a highest-density joint region and does not use the fitted joint density shape. It is intended as a simple distribution-free trust envelope around the richer joint ODSP forecast.

## Distribution shift

Conformal calibration does not make a predictor shift-proof. If the state process changes after calibration, empirical coverage may collapse. The known-truth benchmark deliberately introduces post-calibration continuous and circular shifts and requires this degradation to remain visible rather than being described as guaranteed coverage.

## Known-truth benchmark

The prospective benchmark freezes seed `20260905`, 128 replicates, 1,000 calibration rows and 2,000 target rows per replicate. It requires:

- exchangeable continuous 90% coverage near nominal;
- exchangeable circular 90% coverage near nominal;
- exchangeable Bonferroni joint coverage near its 90% lower-bound target;
- strong coverage degradation after deliberately shifted continuous outcomes;
- strong coverage degradation after deliberately shifted circular outcomes;
- positive-affine response-unit invariance for standardized continuous scores;
- circular phase-origin invariance;
- equivalent hours/minutes arc scaling.

The first prospective execution passed every frozen obligation:

```text
continuous 90% coverage        0.90115234375
circular 90% coverage          0.90017578125
joint Bonferroni coverage      0.90428125
shifted continuous coverage    0.13568359375
shifted circular coverage      0.0001953125
continuous affine error        2.22e-16
circular phase error           0
circular hour/minute error     0
```

The deliberately shifted cases are not failures of the implementation; they demonstrate the declared limit of the exchangeability guarantee.

Run:

```bash
python scripts/run_continuous_circular_conformal_benchmark.py
```

The canonical values are pinned in `CONTINUOUS_CIRCULAR_CONFORMAL_VALIDATION_RECEIPT.json` and are rerun exactly by its receipt test.

## Scientific boundary

Coverage is a statistical property of the declared calibration architecture. It does not establish that the response is biologically the right niche state, does not repair observation/detection bias, does not establish causal environmental effects, and does not make a poor base predictor biologically useful.
