# BOP: a separate exact test of positive animal-gain population content

**Status: method implementation; no new biological validation.**

The module odsp/group_gain_content.py answers a question that a marginal
rank prediction bound does not answer: does the evidence support that at
least a prespecified fraction of a target population has gain above a fixed
threshold? This uses an established one-sided exact binomial test. No new
conformal theorem or biological finding is claimed.

## 1. The correction and the two questions

The previous technical note incorrectly concluded population positivity
from an observed positive random rank lower limit. Its rank lemma is correct;
the omitted randomness was the calibration sample.

| Question | Statistic and guarantee | Assumption and first relevant count |
|---|---|---|
| Does a lower limit cover one future animal's gain? | Calibration order statistic; coverage marginal over calibration and the future score | Exchangeable scores for one fixed predictor/reference; nine calibration animals allow a finite nominal-90% lower limit |
| Is the target population's positive-gain fraction at least 90%? | Fixed-threshold one-sided binomial test with 5% false-support control | IID animal-level gain indicators in the selected population; 29 all-positive calibration animals are the first supporting case |

For a prespecified t, the valid rank consequence is

\[
\Pr(L_\alpha>t,\ G_{\mathrm{new}}\le t\mid\mathcal F)
\le k/(n+1)\le\alpha.
\]

This is a joint event. It does not say that the conditional error probability
after observing a positive limit is at most alpha. With IID +/-1 gains and
true positive probability 0.8, the nine-calibration-animal limit is positive
with probability 0.134217728. The future positive probability is still 0.8;
the joint failure probability is 0.0268435456. The original rank method is
working correctly in this counterexample.

## 2. Exact population-content decision

Let c be the target positive fraction, t a fixed gain threshold, and
1-delta the confidence level. For n independent animal-level gains in one
prespecified target population, let x count gains **at or below** t.

Under the null that the positive fraction p is at most c,

\[
p_{\mathrm{bin}}=\sum_{j=0}^{x}{n\choose j}(1-c)^j c^{n-j}
\]

is a valid lower-tail p-value, maximized at the null boundary. The rule
issues support when this value is at most delta. For every fixed p<=c,
the probability of issuing support across repeated samples is at most delta.
Thus support for the stronger alternative p>c also supports the requested
weaker claim p>=c. This is frequentist error control, not a posterior
probability that a particular supported claim is true.

With c=0.9, delta=0.05 and t=0, exact calculations give:

| Calibration animals | Nonpositive gains | Exact-tail value, approximately | Decision |
|---:|---:|---:|---|
| 9 | 0 | 0.3874204890 | Count cannot support the claim |
| 28 | 0 | 0.0523347633 | Count cannot support the claim |
| 29 | 0 | 0.0471012870 | Support under the declared IID model |
| 45 | 1 | 0.0523677814 | Not supported |
| 46 | 1 | 0.0480037996 | Support under the declared IID model |

These displayed p-values are approximations; decisions use exact rational
arithmetic. At count n the best possible p-value is c^n. The API checks this
before accepting outcomes. An unsuccessful test does not prove that the
population fraction is below c. The reserved validation group is part of
ODSP's surrounding validation design, not an extra requirement of the
binomial test itself.

## 3. Assumptions that freezing cannot establish

The predictor/reference, target stratum, threshold, content target, confidence
and sample size must precede outcome inspection. Do not keep adding animals
until the test passes or choose a favorable stratum/threshold after scoring.
One result concerns one preselected stratum; repeated tests and simultaneous
claims require a separate multiplicity design.

The gain indicators must be IID for the target sampling process conditional
on upstream training/model information. They need not contain independent
GPS fixes. Conversely, distinct animal IDs and exchangeability by themselves
are insufficient: perfectly correlated animals can all have positive gain
with probability 0.8 even at n=29, invalidating binomial false-support control.
The conditioning claim is not automatically conditional on the entire
realized feature/forecast roster; animal-specific fixed covariates can yield
heterogeneous success probabilities. A serialized roster is an integrity
record, not a sampling theorem.

Historical cross-fitted BOP scores use different fitted models and are not
admitted here. The Swiss model-record error counts also are not independent
animal gains. Original BOP mixed, red-kite external HOLD and Dryad NOT_ADMITTED
remain unchanged.

## 4. Executable protocol

1. Freeze an existing fixed-forecast plan. Where managed source-to-model replay
   or canonical identity checks are required, perform those upstream checks.
2. Call freeze_group_gain_content_plan with one selected stratum and the
   explicit sampling declaration. It verifies the forecast/artifact digests,
   reserves validation support and records count feasibility without labels.
3. Call assess_group_gain_content with **complete calibration-role outcomes
   only**. It verifies the policy, repeats the immutable-plan checks, stops
   before label access if the count cannot support the claim, and compares
   all row IDs with the frozen calibration role before retrieving any label
   values. It then snapshots only those calibration labels and calls the
   existing calibrate_fixed_group_gain scorer. Before counting successes it
   checks that weighted-aggregation roundoff has not changed any selected
   group's fixed-threshold classification.
4. Use the returned calibration unchanged in validate_fixed_group_gain for
   the separately reserved validation outcomes.

The assessment exports aggregate counts, digests, a conservative float upper
bound for the p-value and explicit scientific limits. Individual identities,
forecasts and labels are excluded from public summaries. Internal exact
fractions determine decisions; display rounding cannot turn a failure into
support.

### Weighted-aggregation roundoff gate

The inherited scorer uses floating products and division for weighted means.
Even a finite result can cross a strict threshold because of rounding. For
example, a single-row animal with gain log(0.75)-log(0.5) and weight 0.01
can round just above that same frozen threshold. With weight 5e-324 and gain
log(0.75)-log(0.375), the inherited mean can become 1.0 instead of about 0.693.

The content API therefore also computes the sign of sum(w_i * (d_i - t))
exactly, treating each frozen binary weight, per-row binary log delta d_i and
binary threshold as a rational number. Positive weights make this sign
equivalent to the weighted-mean threshold event. If it disagrees with the
legacy classification for any selected animal, assessment stops with an
error and issues no support decision. Both passes use the same snapshot of
calibration labels. The existing calibration object and historical scoring
code remain unchanged.

This guard addresses aggregation rounding, not exact transcendental
logarithms or every possible numerical error in the inherited score. A
finite legacy mean may still differ numerically while giving the same
threshold classification. Do not retune weights or thresholds after outcomes
to evade a stopped assessment.

### Small synthetic fixed-forecast example

The following fabricated probabilities illustrate the API, not biological
source admission or artifact-to-model execution.

~~~python
from odsp.fixed_group_gain_protocol import (
    freeze_fixed_group_forecasts, validate_fixed_group_gain,
)
from odsp.group_gain_content import (
    freeze_group_gain_content_plan, assess_group_gain_content,
)

model, reference = b"synthetic model", b"synthetic reference"
calibration = [
    dict(row_id=f"cal-{i}", group_id=f"animal-{i}", stratum="target",
         conditional=[0.75, 0.25], reference=[0.5, 0.5])
    for i in range(29)
]
validation = [
    dict(row_id="test", group_id="new-animal", stratum="target",
         conditional=[0.75, 0.25], reference=[0.5, 0.5])
]
forecast_plan = freeze_fixed_group_forecasts(
    training_group_ids=["training-animal"], classes=["a", "b"],
    calibration_forecasts=calibration, validation_forecasts=validation,
    model_artifact=model, reference_artifact=reference,
    training_source_sha256="a" * 64,
)
policy = freeze_group_gain_content_plan(
    forecast_plan, stratum="target",
    sampling_assumption="iid_group_gains_within_prespecified_stratum",
    minimum_positive_fraction="0.9", confidence_level="0.95",
    gain_threshold=0, model_artifact=model, reference_artifact=reference,
)
assert policy.count_allows_support  # outcome-blind, not a positive result
result = assess_group_gain_content(
    policy, forecast_plan, {f"cal-{i}": "a" for i in range(29)},
    model_artifact=model, reference_artifact=reference,
)
assert result.supported
print(result.as_public_dict())
validation_result = validate_fixed_group_gain(
    forecast_plan, result.calibration, {"test": "b"},
    model_artifact=model, reference_artifact=reference,
)
assert validation_result.strata[0].positive_validation_group_count == 0
~~~

Support for a population fraction does not promise that this next animal
improves. Its negative result does not update the frozen policy or calibration.

## 5. Verification and provenance

The design and implementation plan were committed before implementation at
64225fbde5bec0be543ccb9301f8616e4e77bd6b. The counterexample and numerical
count cutoffs were already known analytically; this was not a prospective
biological experiment or a tuned simulation benchmark.

The focused suite contains 63 new cases and 60 existing rank/fixed/managed
protocol cases. It covers the counterexample, exact count and probability
boundaries, every failure count in a known six-trial distribution, strict ties,
stratum isolation, event replication, frozen-policy/forecast/artifact changes,
wrong outcome roles, count-HOLD before any label read, nonfinite arithmetic
rejection, finite weighted-aggregation roundoff, a single calibration-label
snapshot, public-summary privacy and legacy validation reuse.

An independent check compared 816 exact tails with direct combinatorial
expansion and SciPy's one-sided binomtest. An isolated negative control
replaced only the exact decision with binary-float arithmetic; the rational
boundary test then failed as intended. Independent review additionally exposed
ordinary-weight and subnormal-weight threshold errors. Four new regressions
failed before the aggregation guard. Three additional poisoned lazy-mapping
cases verified that role mismatches are rejected before any label value is
read. A fresh normal run passed all 123 cases.

~~~bash
python -m pytest -q tests/test_group_gain_content.py \
  tests/test_new_group_gain_envelope.py \
  tests/test_fixed_group_gain_protocol.py \
  tests/test_managed_group_forecast_v1.py
~~~

The dedicated workflow runs these tests on Python 3.10, 3.12 and 3.13.
The standard scientific-core workflow also collects the new tests.

## Statistical references

- Angelopoulos, A. N. & Bates, S. (2023), Conformal Prediction: A Gentle Introduction.
  [Author preprint, especially sections 1 and 3.2](https://arxiv.org/pdf/2107.07511).
- Clopper, C. J. & Pearson, E. S. (1934), The use of confidence or fiducial
  limits illustrated in the case of the binomial. Biometrika 26, 404–413.
  [Official exact-binomial implementation reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html)
  and [Clopper–Pearson interval reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).
