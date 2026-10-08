# Future-refit success probability v1

This route asks a different question from both existing ODSP refit routes.

The fixed-set route asks whether every supplied refit passes. The qualified v5
training-process route asks whether the **mean** held-out gain over the frozen
training process is positive.

This candidate asks:

> If the frozen training process is run one more time, what lower confidence
> bound can we place on the probability that the resulting refit is positive in
> every required validation-population cell?

Let (S_r=1) when refit (r) has true validation-population gain above the
declared tolerance in every validation-group x ordered-contrast cell. The new
estimand is (p=P(S_r=1)) for an iid draw from the frozen training process,
conditional on the frozen empirical training source.

## Two-stage lower bound

The overall one-sided error budget is frozen at 0.05 and split equally.

### 1. Validation uncertainty: alpha = 0.025

All observed refit x group x contrast cells are placed in one simultaneous
validation family. Validation blocks are resampled; refits are not resampled in
this stage. Within a validation group, the same block bootstrap draw is shared
across every refit and contrast.

A refit is **certified successful** only if every required simultaneous lower
bound exceeds the gain tolerance. Let K be the number of certified successful
refits.

If the simultaneous validation family covers, K cannot exceed the number of
truly successful observed refits.

### 2. Training-process sampling: alpha = 0.025

The frozen process generates independent refits. Therefore the number of truly
successful observed refits among R draws is binomial with parameter p.

ODSP applies the exact one-sided Clopper-Pearson lower bound to K successes out
of R. Because that lower bound is monotone in K, substituting the conservative
certified count K remains conservative whenever the validation family covers.

By a union bound, the probability that the reported lower bound exceeds the true
future-refit success probability is at most the validation-stage error plus the
binomial-stage error.

## Small-R ceiling

Even perfect observed success cannot create arbitrary certainty.

With the frozen process-stage alpha of 0.025, if all R observed refits are
certified, the maximum possible lower bound is alpha^(1/R). For example:

- R=8: about 0.631;
- R=20: about 0.832;
- R=50: about 0.929.

This ceiling is reported explicitly. The route must not turn eight successful
refits into a claim that a future refit succeeds with probability >0.8.

## Scope

The initial candidate is deliberately narrow: independent validation groups,
exactly two ordered contrasts, and a prospectively frozen independent training
process. It is internal-only until its own prospective operating-characteristic
qualification passes. The existing v5 process-mean route and fixed-set route are
unchanged.
