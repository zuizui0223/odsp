# All-refit directional robustness

## Scientific question

ODSP already separates validation-sample uncertainty from upstream model-refit
sensitivity.  A collection of supplied refits is not automatically a probability
sample from a well-defined population of all possible fits.  Therefore ODSP does
not assign a new confidence distribution to the refit axis.

For a prospectively directional transfer claim, the fixed-set robustness question
is instead:

> Does every supplied upstream refit independently support the same required
> positive-transfer steps on the held-out validation data?

The primary output is the deepest non-skippable information-transfer ceiling that
is certified in **every supplied refit**.

## Per-refit component tests

For each refit, ODSP uses an already-qualified one-sided validation-sample route:

- independent validation groups: `certify_positive_information_transfer_v2`;
- groups paired on exactly the same exchangeable validation blocks:
  `certify_shared_block_positive_information_transfer_v2`.

Each component refit test already applies one familywise lower bootstrap-t bound
over its full predeclared group-by-information-step family.  The scientific
alternative is directional: gain must exceed the declared non-negative tolerance.

## Refit-axis composition: an intersection-union rule

Let `A_r` mean that refit `r` satisfies the required positive-transfer claim.  The
fixed-set global alternative is

```text
A_1 AND A_2 AND ... AND A_R.
```

ODSP therefore reports global refit robustness only when every supplied refit
passes the corresponding component requirement.  This is the standard
intersection-union construction: the global null is the union of component
failures, so requiring every level-alpha component test to reject does not require
an additional Bonferroni-style correction across refits for this fixed-set AND
claim.

This is existing statistical theory, not a new ODSP theorem.  Classical
intersection-union references include Berger (1982) and Berger & Hsu (1996).
ODSP's contribution here is the operational ecological-transfer contract: apply
that logic to independently audited held-out information-transfer ceilings while
preserving the validation-family error control inside each supplied refit.

## What this does not mean

The supplied refits are **not** treated as independent observations.  ODSP does
not infer a sampling distribution for refits, estimate a probability that an
unseen refit will pass, or claim robustness to an unsampled population of model
algorithms, random seeds, training sets, preprocessing decisions or analyst
choices.

The claim is intentionally literal:

```text
all supplied refits passed
```

not

```text
all possible future refits would pass.
```

The old nested refit/block Monte Carlo machinery remains useful as a sensitivity
diagnostic, but it is not promoted to the primary confidence statement for a
refit population.

## Non-skippable ceiling

For every adjacent information step, ODSP records the directional certification
category from every refit.  The all-refit step is:

- `robust_across_refits` only when every supplied refit is
  `robust_generalizing`;
- `unavailable` when the robustness set is too small or any supplied refit is
  unavailable;
- otherwise `not_robust_across_refits`.

The all-refit ceiling advances only through consecutive
`robust_across_refits` steps.  A richer positive step cannot jump over an earlier
failure.  A reference refit, average refit, ensemble mean, or best refit cannot
rescue a failed supplied refit.

## Minimum refit count

The default minimum is two supplied refits.  This is a semantic robustness
minimum, not an asymptotic sample-size theorem.  With fewer than the declared
minimum, ODSP still returns the component refit audit but marks the global
all-refit robustness claim unavailable and leaves the global ceiling at the base
level.

## Independent-group and paired designs

The same refit-axis rule is available for two validation designs.

### Independent validation groups

Within each refit, groups are treated as independent validation units and declared
blocks are resampled within group.  The same bootstrap seed can be reused across
refits for deterministic comparison; this does not imply refit independence.

### Exact shared-block pairing

When every validation group is observed on exactly the same positive-mass block
set, ODSP uses the paired shared-block one-sided bootstrap-t route.  A single block
draw is shared across every group and contrast inside a replicate.  Missing blocks
are never imputed and support mismatch hard-stops.

## Information and score requirements

All refits must use the same strict information filtration and the same held-out
rows.  Every comparator score must be finite on every positive-weight row for
every refit.  The richest level may assign zero predictive support (`-inf` log
score); when that makes a required step unavailable in one refit, the all-refit
ceiling stops there.

## Reporting language

Preferred wording is:

> The directional transfer ceiling was robust across all supplied refits.

or, when it fails:

> The reference fit supported the richer ceiling, but the claim was not robust
> across the complete supplied refit set.

Avoid wording that implies a confidence interval over a population of possible
refits unless an explicit probabilistic refit-generating design has independently
been justified.
