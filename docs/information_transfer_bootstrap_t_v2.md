# Information-transfer bootstrap-t v2

## Scope

Version 2 upgrades the validation-sample uncertainty layer for ODSP information-transfer analyses. The estimands do not change: a strict filtration still compares adjacent nested information sets, and a complete information lattice still compares every legal subset edge.

The change is inferential. Every relevant held-out contrast is placed into one simultaneous family and studentized inside each bootstrap replicate.

Historical v1 functions and frozen empirical receipts are not rerun or reclassified.

## Multi-contrast family

For each independent validation group `g`, ODSP constructs row-wise held-out gains for every requested contrast `k`. Within a group, caller-declared exchangeable validation blocks are sampled with replacement.

One sampled block sequence is reused for **all contrasts in that group**. This preserves the empirical covariance among adjacent filtration steps or among lattice edges evaluated on the same validation blocks.

For every bootstrap replicate and every estimable group-by-contrast cell, ODSP recomputes

```text
theta_gk_star
SE_gk_star
```

and forms

```text
T_gk_star = |theta_gk_star - theta_hat_gk| / SE_gk_star.
```

The family statistic is the maximum over all estimable `g x k` cells. The resulting critical value is therefore shared across the complete family rather than recomputed separately for each step or edge.

## Strict information filtration

`certify_information_transfer_v2()` first validates the strict nesting contract

```text
C0 subset C1 subset ... subset CK.
```

It then constructs all adjacent score increments and certifies them jointly. The certified transfer ceiling advances only through a consecutive run of `robust_generalizing` steps.

A later positive step cannot jump over an earlier mixed, uncertain, unavailable or robust-nonpositive step.

## Complete information lattice

`certify_information_lattice_v2()` retains the complete `2^m` subset requirement for `m` scientifically declared information blocks. Every directed edge is certified in one `group x edge` bootstrap-t family.

Full-transfer paths are counted only through `robust_generalizing` edges. Therefore:

- positive full-vs-base gain cannot rescue a failed intermediate edge;
- choosing the best information order after observing outcomes is not allowed;
- Shapley contributions remain descriptive order-averaged point summaries and cannot rescue an edge failure.

## Non-finite support

A non-finite held-out gain in one group-by-contrast cell makes that cell unavailable. It does not erase unrelated contrasts, but any filtration ceiling or lattice path requiring that cell stops there.

Comparator support rules remain unchanged from the underlying ODSP information methods.

## Dependence assumptions

This v2 route resamples validation blocks **independently between groups**. It therefore requires scientifically defensible validation-group independence.

When multiple groups are measured on the same exchangeable years, sites, surveys or other paired validation blocks, use the shared-block paired route rather than declaring those groups independent.

## Refit uncertainty

The v2 bootstrap-t confidence interpretation covers validation-sample uncertainty conditional on supplied predictions. It does not turn an empirical ensemble of upstream refits into an independent probability sample.

Refit-aware ODSP analyses therefore remain explicitly labelled sensitivity analyses unless a separate sampling model for the refits is scientifically justified.

## Prospective use

For new confirmatory information-transfer endpoints, the version-2 surfaces are preferred:

```text
odsp.information_transfer_v2.certify_information_transfer_v2
odsp.information_lattice_v2.certify_information_lattice_v2
```

The historical v1 surfaces remain available for frozen provenance.
