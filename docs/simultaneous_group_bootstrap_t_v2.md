# Simultaneous group certification v2: genuine block bootstrap-t

## Why a v2 exists

ODSP version 1 standardized outer bootstrap deviations by one standard deviation estimated from the complete set of outer bootstrap replicates. That procedure remains useful as a standardized max-deviation sensitivity analysis, and historical receipts remain frozen under that definition, but the denominator was not recomputed inside each bootstrap replicate.

Version 2 is prospective. It uses replicate-specific studentization and is the preferred simultaneous validation-sample certification for new endpoints.

No historical empirical endpoint is rerun or reclassified by this change.

## Estimator

For one independent validation group, aggregate each caller-declared exchangeable block `b` into

```text
N_b = weighted gain numerator in block b
W_b = positive score-weight mass in block b.
```

The held-out gain estimator is

```text
theta_hat = sum_b N_b / sum_b W_b.
```

The cluster ratio influence residual is

```text
Z_b = N_b - theta_hat W_b.
```

With `B` positive-mass validation blocks, ODSP uses

```text
SE_hat = sqrt{ B/(B-1) * sum_b Z_b^2 } / sum_b W_b.
```

This reduces to the usual standard error of an unweighted block mean when every block has unit weight.

## Bootstrap-t family

For each bootstrap draw ODSP samples exactly `B` validation blocks with replacement. It then recomputes both

```text
theta_hat_star
SE_hat_star
```

from that resampled block sample. For every estimable group the draw contributes

```text
T_g_star = |theta_hat_star_g - theta_hat_g| / SE_hat_star_g.
```

The family statistic is

```text
T_max_star = max_g T_g_star.
```

The requested familywise quantile of `T_max_star` is the simultaneous critical value `c`. The final interval is

```text
theta_hat_g +/- c SE_hat_g.
```

Thus the studentizer used inside `T_star` is genuinely replicate-specific.

## Degenerate zero-variance cells

A bootstrap draw with `SE_hat_star = 0` is handled fail-closed:

- if the bootstrap estimate also equals the point estimate within numerical tolerance, that cell contributes `T=0`;
- if the bootstrap estimate moves despite zero estimated spread, that cell contributes `T=infinity`.

The latter makes the resulting simultaneous interval uninformative rather than silently dividing by zero.

## What remains conditional

The familywise interpretation is conditional on the supplied held-out predictions and on two scientific design assumptions:

1. validation groups are independent for the independent-group route;
2. declared validation blocks are exchangeable sampling units within groups.

ODSP does not infer either assumption from labels.

For groups observed on the same years/sites/surveys, use the paired shared-block route rather than asserting group independence.

## Refit uncertainty is different

An ensemble of upstream model refits is not automatically an independent probability sample. ODSP therefore does **not** call refit-mixture sensitivity a bootstrap-t confidence guarantee. The refit-aware modules remain sensitivity analyses over the supplied empirical refit ensemble plus held-out block resampling.

This distinction is intentional: validation-sample uncertainty and model-refit sensitivity answer different questions.

## Version boundary

- Historical function: `audit_simultaneous_group_certification` (v1 provenance; frozen receipts).
- Prospective function: `audit_simultaneous_group_certification_v2`.
- Shared studentization primitives: `odsp.bootstrap_t`.

For new confirmatory analyses, v2 should be used unless a different predeclared inferential scheme is scientifically justified.
