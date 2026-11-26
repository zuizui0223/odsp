# BOP context-mixture robust group content v1

**Synthetic method verification only; real external BOP/Dryad remains HOLD.**
The Data_1a study's selection and time coverage have not been verified.
The existing reduced common-input learner represents the 06–18
mean-solar-clock interval and its complement, not actual daylight.

## What changes relative to the original group mean?

For an animal, let m0 and m1 denote empirical mean log-score gains in
the two observed contexts, holding relative within-context weights fixed.
The mean at a context-1 weight q is (1-q)m0+qm1. The observed mixture
uses that animal's original total context weights; equal-context
standardization uses q=1/2. The sharp lower and upper envelope across all
q in [0,1] is min(m0,m1) and max(m0,m1), respectively.

A robustly positive animal has both means strictly positive. This is
not the same as either a positive original average or a positive
equal-context average. It is also not an arbitrary row-reweighting
sensitivity: the within-context distribution is held fixed.

A fixed stratum and minimum number of rows in each context per animal
must be declared before target outcomes. Every calibration AND reserved
validation animal must meet that support rule. Missing support produces
HOLD, without discarding the animal, inventing a mean, pooling species,
or reading any calibration outcomes. The row-count rule is only
structural; correlated repeated fixes are not independent visits.
Calibration size must also permit the separate 90%-content test at
one-sided 5% error (at least 29 independent groups in this best case).
The existing synthetic identity/model/forecast replay precedes all
outcome reads.

## The primary statistical claim

For the fixed upstream model, reference and group observation protocol,
define a robust group-score indicator I=min(m0,m1)>0. If the indicators
are IID for the prespecified population, test P(I=1)<=0.9 by a
one-sided exact binomial tail. This is frequentist error control under
the stated IID assumption; the software does not prove that assumption.
There is one primary test, for the *same animals* improving in both
contexts. The natural, balanced and separate-context counts remain
descriptive. For example, 45/46 positive animals in each context
can each pass a separate content test, but if the two failures occur
in different animals there are only 44/46 robust positives and the
joint content test does not pass.

This is an empirical score functional under context reweighting,
not a claim about true latent activity, intervention effects, changes
within a context, missing context counterfactual outcomes, detector
bias removal, a population's unknown sampling weights, or future
group rank coverage. Context-specific score uncertainty remains
part of the group observation protocol. Retain a reserved validation
role; this route never reads its labels or issues a new rank envelope.

## API

~~~python
from odsp.context_mix_group_content import (
    ROBUST_IID, freeze_context_mix_content, assess_context_mix_content,
)
policy = freeze_context_mix_content(
    identity_checked, stratum="Circus pygargus",
    minimum_rows_per_context=1, sampling_assumption=ROBUST_IID,
)
print(policy.as_public_dict())  # outcome-blind
report = assess_context_mix_content(policy, calibration_states_by_native_row)
~~~

identity_checked is the existing synthetic-only FrozenIdentityCheckedTransport.
The minimum of one is illustrative, not a recommendation for real tracking
data; choose an observation-quality protocol before outcomes. The new
scorer uses exact rational sums of the binary log deltas and weights.
This does not make the logarithm calculations mathematically exact.
Only aggregate results are exported; private identity digests, animal
keys and row labels are not included. The existing model, reference,
rank, content, BOP mixed and Dryad NOT_ADMITTED results are unchanged.

## Known-truth examples and tests

Fabricated training observations assign low altitude inside the mean
solar clock window and high altitude outside. With low labels in both
target contexts, favorable inside-window observations can dominate a
9:1 mixture even though the outside-window gain is negative. Reverse
the relative context mass without changing any within-context outcomes
or model probabilities: the observed mean changes sign while the
equal-context mean and worst-mixture result stay fixed. With 29 such
calibration animals, all can be positive under the first observed
mixture and none is robustly positive. The primary robust test fails.

With matching labels in both contexts, 29/29 are robust positives;
the exact null tail is 0.9^29, approximately 0.04710. The
46-animal disjoint-failure counterexample tests the difference
between marginal and joint robust content. Tests also cover
outcome-blind whole-roster failure, exact boundary arithmetic including
subnormal weights, role-safe one-time label reads and managed context,
artifact and policy tampering. All examples are designed known-truth
fixtures, not new prospective ecological evidence.

Reproduce:
~~~bash
python -m pytest -q tests/test_context_mix_group_content.py
~~~

Design: docs/superpowers/specs/2026-11-26-bop-context-mix-robust-content.md.
