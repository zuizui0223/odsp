# Separate future-animal rank coverage from positive population content

## Intent and diagnosed error

The rank lemma in `docs/bop_individual_gain_inference_theory_v1.md` is valid,
but section 3 item 1 incorrectly turns an observed positive random lower
limit into a population positive-gain probability statement conditional only
on upstream training. Marginal coverage averages over calibration samples.
For a prespecified threshold t the valid consequence is
`Pr(L > t and G_new <= t | F) <= k/(n+1)`, not a guarantee conditional on
observing `L > t`. Independent +/-1 gains with positive probability 0.8 and
n=9 give `Pr(L>0)=0.134217728` and joint failure 0.0268435456, while future
positivity remains 0.8. These analytical values were known before this design.

## Approaches and selected scope

1. Correct the prose only: necessary, but leaves no operational way to ask
   whether a specified fraction of a population benefits.
2. **Selected by the implementer under the user's action-first instruction:**
   correct the interpretation and add a separate, opt-in exact binomial test
   with an outcome-blind policy and count preflight.
3. Reference-mixture downside control: useful for the Swiss log-loss problem,
   but does not repair this inference error and is deferred.

This is an established exact binomial method, not a new conformal theorem or
a new biological result. Existing rank calculations, immutable receipts,
Swiss cells, historical mixed BOP and external-source HOLD states stay intact.

## Statistical contract

For one prespecified target stratum, fix the predictor/reference, threshold t,
target positive fraction c and confidence error delta before calibration
outcomes. Sample size is fixed independently of outcome-driven stopping.
Require IID animal-level gain indicators in that population conditional on
upstream training/model information. Exchangeability alone is insufficient.
Do not automatically condition this assumption on a realized covariate or
forecast roster; freezing those files establishes integrity, not IID sampling.

With x calibration gains <=t among n animals, compute exactly
`p = sum(comb(n,j)*(1-c)**j*c**(n-j), j=0..x)`.
Reject the null `Pr(G>t) <= c` when `p <= delta`; this supports the weaker
claim `Pr(G>t) >= c`. For every fixed null population, the probability of
issuing support is at most delta. This is repeated-sample error control,
not a posterior probability after seeing support. Ties count as nonpositive.

The best possible p-value at count n is `c**n`; if it exceeds delta, stop
before accessing labels. At c=0.9 and delta=0.05: 28 all-positive animals
fail, 29 pass; with one nonpositive animal, 45 fail and 46 pass. These are
per-stratum counts, not GPS records, repeated model seeds or independent
studies. The integrated protocol reserves at least one validation animal
in that stratum; validation is not needed for the binomial calculation itself.
There is no multiple-stratum or repeated-analysis error control in this API.

## Interfaces and execution order

Create `odsp/group_gain_content.py`, using standard-library exact rational
arithmetic and the existing fixed-forecast protocol, with no new dependency.

- `freeze_group_gain_content_plan(forecast_plan, *, stratum,
  sampling_assumption, model_artifact, reference_artifact,
  minimum_positive_fraction='0.9', confidence_level='0.95',
  gain_threshold=0.0) -> FrozenGroupGainContentPlan`.
  Validate unchanged forecast/artifact bytes; require the explicit assumption
  `iid_group_gains_within_prespecified_stratum`, one selected nonempty stratum,
  calibration support and a reserved validation group. Hash policy, original
  plan digest, selected counts, threshold and exact rational parameters.
  Expose count feasibility without accepting any outcomes.
- `assess_group_gain_content(content_plan, forecast_plan,
  calibration_outcomes, *, model_artifact, reference_artifact)
  -> GroupGainContentAssessment`.
  Verify policy and base-plan integrity, stop on count insufficiency before
  reading outcomes, and call `calibrate_fixed_group_gain` to obtain the actual
  frozen-forecast scores. Do not accept caller-provided scalar gains or read
  validation outcomes. Compute the selected stratum's exact binomial tail.
  Retain the resulting `FrozenGainCalibration` for unchanged legacy validation.

Public summaries contain aggregate counts, policy/calibration digests and
explicit assumptions/claim limits; no animal identifiers or per-row outcomes.
Use exact rational comparison for decisions and an outward-rounded float
upper bound for p-value display. Do not infer that failure to support proves
poor population performance. Artifact-to-forecast execution and canonical
animal identity still require the existing managed/identity routes upstream.

## Validation and delivery

Known-count tests exercise 9 versus 29, 28/29, 45/46, exact p-value boundaries,
threshold ties, arbitrary sign/magnitude, stratum isolation, invalid parameters,
policy/plan/artifact mutations, wrong outcome roles, count-HOLD before label
access and reuse of the calibration in legacy validation. Independent finite
binomial calculations check the decision; no tuned Monte Carlo benchmark.

Correct the theory note, update manuscript section 2.2 and the method spine,
and document the API plus its assumptions. Dedicated Python 3.10/3.12/3.13 CI
and existing scientific-core CI are integration gates. Independent mathematical
and whole-change reviews precede merge. No new source data or refits are used.
