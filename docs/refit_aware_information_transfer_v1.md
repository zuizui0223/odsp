# Refit-aware information-transfer certification

## Why a second uncertainty layer is needed

A familywise transfer ceiling computed from one set of held-out predictive scores
is conditional on that fitted set of predictors. It answers whether validation
sampling uncertainty is compatible with transfer of each added information step.
It does **not** answer whether the same conclusion survives plausible upstream
refits.

The refit-aware layer takes an explicit ensemble of already fitted predictors and
propagates both sources of variation without allowing a favorable reference fit
to override refit sensitivity.

## Input

For every declared information level, supply an aligned score matrix

```text
[refit, held-out row]
```

on exactly the same validation observations. The same ordered information
filtration is used for every refit.

For example:

```text
pooled          {}                     R x N scores
species         {species}              R x N scores
species_context {species, context}     R x N scores
```

The function is

```python
certify_refit_information_transfer(...)
```

in `odsp.refit_information_transfer`.

ODSP does not fit the models, choose the refit scheme, or infer independence among
refits.

## Nested Monte Carlo design

Each Monte Carlo draw performs two operations.

1. Select **one refit ID** from the supplied empirical refit ensemble. The same
   selected refit is used for every independent group and every information step.
2. Within each independent group, resample the declared validation blocks. The
   same sampled block indices are used for every information step within that
   group.

This preserves two dependence structures that would be broken by independent
resampling:

- correlation among information levels caused by using the same fitted model;
- correlation among adjacent transfer increments evaluated on the same validation
  blocks.

A single studentized max-t critical value is then computed over the full estimable
`group x information-step` family.

## Why the refit is shared globally

Choosing a different refit independently for each group would create artificial
hybrid models that never existed. Choosing a different refit independently for
each information step would similarly combine incompatible fitted ladders.

The refit-aware procedure therefore treats one supplied refit as a coherent
upstream analysis state. A draw either uses that refit everywhere or not at all.

## Three ceilings

The audit keeps three distinct quantities.

### Reference-fit ceiling

The point and validation-block-certified ceilings for one explicitly named
reference refit. This is useful for tracing the original analysis but cannot
rescue a refit-aware failure.

### Refit point ceilings

The ordinary all-group point ceiling for every supplied refit. Variation among
these values is reported as `refit_sensitive` rather than being hidden by an
average.

### Refit-aware certified ceiling

The finest consecutive information level whose group-by-step intervals remain
familywise robust-positive after both refit selection and validation-block
resampling.

A reference fit may therefore reach

```text
pooled -> species -> species+context
```

while the refit-aware ceiling stops at `species`. In that case the correct claim
is that the fine context step is not stable to the supplied refit ensemble.

## What the refit ensemble means

The intervals describe sensitivity to the **empirical mixture of supplied
refits**. They are not a standard error of the mean fitted model, and ODSP does
not divide refit variability by `sqrt(R)`.

The method does not claim that the supplied refits are statistically independent.
The refit scheme must be scientifically justified upstream and declared by the
analysis. Examples could include repeated training resamples, posterior predictive
fits, alternative initialization/refit realizations, or prospectively defined
training perturbations, depending on the modelling framework.

## Fail-closed rules

- At least `minimum_refits` supplied refits are required for refit-aware cells.
- Every independent group requires at least `minimum_blocks_per_group` positive-
  mass validation blocks.
- All comparator levels must have finite score on every positive-weight row for
  every refit.
- If any supplied refit assigns non-finite score at a richest-level step for a
  group, that group-step cell is unavailable and the transfer ceiling cannot cross
  it.
- Total gain cannot jump over a failed information step.
- A favorable reference fit cannot override a refit-aware failure.

## Relation to the earlier refit audit

`odsp.model_refit_transfer_uncertainty` remains the one-comparison audit for a
single gain matrix. The new module lifts the same scientific principle to a
strict information filtration and preserves the whole `group x step` family in
one joint certification.

## Claim boundary

This is still a conditional sensitivity procedure. It propagates validation-block
sampling and the explicitly supplied refit ensemble. It does not establish that
the ensemble spans every source of model uncertainty, does not infer a refit
scheme, and does not turn model uncertainty into a causal claim.
