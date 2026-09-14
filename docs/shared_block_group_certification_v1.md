# Cross-group shared-block certification

## Problem

ODSP's ordinary simultaneous group certification resamples validation blocks independently within each held-out group. That route is appropriate only when the group-level validation samples can reasonably be treated as independent.

Many ecological designs violate that condition. Multiple species, sites or treatments may be observed in the same years, surveys, camera days or field visits. A shared year can make prediction errors move together across species. Resampling each species independently destroys that empirical covariance structure.

This module adds a separate **paired shared-block** route for such designs.

## Eligibility rule

The paired route is intentionally strict. Every independent group must contain **exactly the same set of positive-mass shared block IDs**.

Examples that can qualify:

```text
species A: year 1, year 2, ..., year 10
species B: year 1, year 2, ..., year 10
```

or

```text
treatment A: site 01, ..., site 20
treatment B: site 01, ..., site 20
```

A design such as

```text
species A: years 1-10
species B: years 1-8
```

fails closed. ODSP does not impute missing shared blocks, condition on a post-outcome common subset, or silently fall back to an independent-group bootstrap.

Zero-weight rows do not create positive block support. If a group's entire contribution for one shared block has zero total weight, that block is treated as absent from that group and the paired design fails.

## Resampling rule

Let `b = 1,...,B` index the common shared validation blocks. One bootstrap draw samples a sequence of block indices

```text
b*1, ..., b*B
```

once. The exact same sampled sequence is reused for:

- every held-out group;
- every adjacent information-filtration step, or every lattice edge;
- every cell entering the simultaneous family.

Within each group, the weighted mean is recomputed using that group's own block weights and numerators. Thus groups can have different numbers of rows and different row weights inside the same shared block while preserving the paired block identity.

A single studentized max-t critical value is then formed over the full estimable

```text
group × contrast
```

family.

## What assumption changes

The ordinary ODSP block bootstrap records that validation-group independence is assumed.

The shared-block route instead records:

```text
validation_group_independence_assumed = false
same_block_draw_shared_across_all_groups_and_contrasts = true
shared_block_exchangeability_assumed = true
```

The scientific assumption is therefore shifted, not eliminated. The declared shared blocks must be defensible exchangeable sampling units for the validation target.

## Information-filtration wrapper

`certify_shared_block_information_transfer()` applies the paired resampling design to a strict information filtration.

The point decomposition remains the same. The uncertainty layer changes only in how the held-out blocks are resampled. The certified transfer ceiling advances only through consecutive steps that are `robust_generalizing` across every group under the joint paired-block max-t family.

## Information-lattice wrapper

`certify_shared_block_information_lattice()` applies the same paired design to every edge of a complete information lattice.

The full family is

```text
group × lattice edge.
```

A positive full-vs-base gain, a favorable information order, or a Shapley average cannot override a failed paired-block edge. The certified path count uses only edges classified `robust_generalizing` under the joint family.

## Scope boundary

This route is **not** a general solution for arbitrary cross-group dependence.

It is appropriate when there is a real paired/repeated validation structure and every group shares the same positive-mass block support. Unbalanced cluster designs, spatial random fields, phylogenetic dependence, or arbitrary network dependence require a different resampling/modeling strategy.

The method deliberately rejects those cases rather than pretending a paired bootstrap is valid.
