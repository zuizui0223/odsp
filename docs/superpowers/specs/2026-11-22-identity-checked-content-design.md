# Identity-checked population-content transfer: design (2026-11-22)

## Current state and gap

PR #303 added an established exact binomial population-content test for one
fixed predictor/reference, but its lower-level API accepts a hash-consistent
forecast plan without requiring the existing canonical-animal identity audit
or source -> fitted artifact -> pre-outcome forecast replay.

The prior identity_checked_transport route performs these checks and scores a
new-animal rank bound, but does not expose the new population-content test
under the same pre-outcome admission and replay sequence.

## Scope

Implement an **additive, synthetic-known-truth-only** high-level adapter:
source/model replay -> canonical animal crosswalk -> selected-stratum content
count gate -> calibration-only exact test -> untouched validation.

The existing identity_checked_transport actively prohibits real BOP/Dryad
admission. This adapter must inherit that prohibition rather than provide a
new route around it. Nothing in this feature proves IID sampling or converts
the original biological BOP mixed conclusion into positive population content.

Use a **single target stratum in both calibration and validation** for this
adapter. The lower-level content scorer consumes the complete calibration
role. A multistratum plan would unnecessarily open other strata's outcomes
during a one-stratum test, and must stop before value access here.

## Proposed API

Module odsp/identity_checked_gain_content.py:

- freeze_identity_checked_gain_content(identity_checked, *, stratum,
  sampling_assumption, minimum_positive_fraction="0.9",
  confidence_level="0.95", gain_threshold=0):
  replay the existing source/model/crosswalk chain, enforce one target stratum,
  bind a frozen content policy to the same forecast plan and actual model/
  reference bytes, verify exact selected-stratum canonical group counts, and
  expose pre-outcome count feasibility. No calibration or validation labels.
- assess_identity_checked_gain_content(binding, native_calibration_outcomes):
  replay the chain and return HOLD on insufficient counts before reading
  any labels. Check exact native calibration row-ID set *before* value access;
  snapshot those values once, prefix with the frozen DRYAD namespace, and run
  the unchanged #303 exact content API. Return the original calibration and
  exact p-value in a bound result, with aggregate-only public summary.
- validate_identity_checked_gain_content(binding, assessment,
  native_validation_outcomes): replay source/model/identity and policy, verify
  the assessment belongs to this binding and its counts/p-value agree with
  its calibration gains, then invoke the existing untouched-validation route.
  Validation never retunes the already frozen content policy or result.

## Fail-closed and statistical boundaries

- No identity, source or model replay failures may read calibration/validation
  labels. Canonical identity record and forecast tampering must stop.
- Distinct IDs and software replay are necessary, not sufficient, for
  independently sampled IID group-gain indicators. A caller's exact IID
  sampling declaration remains an externally justified assumption.
- Fixed sample size and one prespecified stratum; no optional stopping,
  adaptive threshold, simultaneous stratum statement, real Dryad admission,
  historical RF replay, source RDS or GPS read.
- Do not modify the established exact binomial formula, ranking code,
  old receipts, or the biological N2 conclusions. No new empirical claim.
- Reject mismatched native calibration/validation role IDs without reading
  outcome values. No per-animal values or canonical identities in public JSON.
- Keep cross-source proof explicit: the synthetic reduced-feature learner is
  not the original BOP random forest.

## Verification

Use synthetic training rows with a fixed day/night conditional state pattern.
Check 9 versus 29 count feasibility, all-positive and one-failure cases,
an untouched validation animal whose gain can be negative, and source/identity/
policy tampering. Poisoned lazy mappings must detect any premature label read.
A second synthetic stratum must stop before one-stratum content assessment.
Verify downstream reuse of the exact original calibration hash.

Run existing identity/managed/conditional content tests, core CI and
independent read-only review before merging. Any PR/CI result is a methods
verification only, never a biological cross-source validation.
