# Binary-context mixture-robust individual gain (synthetic method route)

## Motivation and estimand

The remaining Dryad candidate has published daylight/site/breeding restrictions
and unknown actual Data_1a time support. Existing BOP common-input synthetic
learner uses **mean-solar-clock 06--18 versus its complement**, not daylight.
Raw group-average gain can change when the proportions of records in those
two contexts change, even with identical within-context empirical gains.

This is distinct from arbitrary bounded row reweighting already implemented
in bounded_reweighting_robustness.py: hold relative weights within each
observed context fixed and allow **every** mixture weight between the two
contexts, then test the population fraction of groups robust under the whole
mixture simplex. No row-level independence is assumed for this arithmetic.

For group g, compute the two frozen forecast log-gain means m0,m1 using
positive within-context base weights. Natural mean is its observed
weight mixture. Equal-context mean is (m0+m1)/2. The exact lower envelope
over all context mixtures is min(m0,m1), and the upper envelope max(m0,m1).
Both contexts must have the predeclared minimum observed row count; missing
support is a structural HOLD, not zero or an imputed gain. Every group in
both frozen calibration and reserved validation roles is retained, or the
whole route stops before reading target labels. The minimum is a row-count
screen only, not a certification of adequate independent visits.

## Primary decision and scope

Use the already-established synthetic-only FrozenIdentityCheckedTransport
to bind source, model/reference, feature context and canonical identities.
Exactly one target stratum and a predeclared row-count rule. Fix threshold
zero, null positive-robust fraction <=0.9, one-sided alpha .05, and fixed
calibration size. At least 29 calibration groups and a separate reserved
validation group are required by the existing protocol. Explicitly declare
IID **robust group-score indicators** for the selected group observation
protocol, conditional on fixed upstream model/training. This assumption is
not verified by software. Primary event is both m0>0 AND m1>0 in the SAME
group. Apply the existing exact binomial tail to the number of groups
with a nonpositive minimum. Raw, equal-context and context-specific
positive counts are descriptive only, not additional content tests.
No independent validation labels are read by this route and no new rank
bound is implied. No outcome-driven changes of policy.

Use exact rational accumulation of existing binary per-row log deltas and
binary weights; this does not make transcendental logarithms exact.
No identities, per-row labels or private crosswalk hash in public reports.

## Verification before integration

1. Same within-context scores under different observed mixtures; raw gain
   flips while equal-context and lower-envelope results stay identical.
2. A positive raw result for all 29 groups can fail robust content; robust
   29/29 supports the fixed binomial decision conditional on IID.
3. At n=46, two disjoint single-context failures can allow 45/46 in EACH
   context but only 44/46 robust; do not substitute marginal positives
   for joint positivity.
4. Strict zero ties, weighted rows, exact sign arithmetic, missing context,
   insufficient counts, wrong-role lazy mappings, modified policy/context,
   canonical identity and artifact replay. Preserve whole roster and read
   admitted calibration labels once.
5. Explicit no real source admission, no new BOP RF or Dryad outcomes, no
   claim of correcting detection bias, within-context shifts, hidden true
   activity or independent biological coverage.

The mathematical endpoint and synthetic counterexample are known before
implementation. This is a new method proof, not a prospectively unobserved
ecological experiment or a new statistical theorem.
