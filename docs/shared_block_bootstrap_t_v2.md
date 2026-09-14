# Shared-block certification v2: paired replicate-studentized bootstrap-t

## Why this method exists

The independent-group bootstrap-t route assumes validation groups can be resampled independently. That is inappropriate when multiple groups are observed on the same exchangeable years, sites, surveys, camera-days or other validation clusters.

The paired shared-block route instead requires every group to contain exactly the same set of positive-mass block IDs. One sampled block sequence is drawn per bootstrap replicate and reused across every group and every information contrast.

Version 2 combines that covariance-preserving paired resampling with genuine replicate-specific studentization.

Historical paired v1 receipts remain unchanged.

## Point estimator

For group `g`, contrast `j`, and shared block `b`, let

```text
N_gjb = weighted gain numerator
W_gb  = score-weight mass.
```

Then

```text
theta_hat_gj = sum_b N_gjb / sum_b W_gb.
```

The original-sample cluster standard error is computed from ratio influence residuals

```text
R_gjb = N_gjb - theta_hat_gj W_gb.
```

## Paired bootstrap draw

For each bootstrap replicate, ODSP samples exactly `B` indices from the common block set with replacement. The same sampled block index vector is reused for all groups and all contrasts.

This preserves the empirical covariance caused by sharing validation blocks across groups and contrasts.

For every estimable cell, the bootstrap replicate recomputes both

```text
theta_hat_gj_star
SE_gj_star.
```

The cell statistic is

```text
T_gj_star = |theta_hat_gj_star - theta_hat_gj| / SE_gj_star.
```

The family statistic is the maximum across all estimable `group x contrast` cells. Its requested empirical quantile is the simultaneous bootstrap-t critical value.

Final intervals are

```text
theta_hat_gj +/- c * SE_gj.
```

where `SE_gj` is the original-sample cluster ratio standard error.

## Eligibility is fail-closed

The v2 paired route is available only when every group has exactly the same set of positive-mass shared blocks. In particular:

- missing blocks are not imputed;
- zero-weight group-block combinations count as absent support;
- a common subset is not selected post hoc;
- unbalanced panels are rejected rather than approximated as paired.

If this condition fails, a different dependence model is required.

## What this does not solve

The paired block design is not a generic dependence correction. It does not automatically handle:

- spatial random fields not reducible to exchangeable paired blocks;
- phylogenetic covariance;
- network dependence;
- irregularly missing shared clusters;
- upstream learner-refit uncertainty.

The method also does not infer that declared blocks are exchangeable. That is a scientific design assumption supplied by the analyst.

## Calibration

`run_shared_block_bootstrap_t_calibration()` evaluates a known global null with six groups, two contrasts, strong cross-group correlation (`rho=0.7`) and cross-contrast correlation (`rho=0.5`). Four scenarios are predeclared:

```text
paired-normal-b8
paired-normal-b20
paired-normal-b50
paired-t3-b20
```

The benchmark compares historical paired v1 fixed-scale standardization with paired v2 replicate-specific bootstrap-t on exactly the same simulated worlds.

The benchmark is methodological qualification, not biological evidence.

## Version boundary

- historical paired v1: `certify_shared_block_gains`
- prospective paired v2: `certify_shared_block_gains_v2`

New confirmatory paired-block analyses should identify the v2 method explicitly as

```text
paired_shared_block_replicate_studentized_bootstrap_t_v2
```
