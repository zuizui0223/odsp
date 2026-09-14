# Information-lattice order-sensitivity audit

## The problem with a single filtration

A strict information filtration

```text
C0 subset C1 subset ... subset CK
```

makes every adjacent score comparison coherent, but it can still encode an
arbitrary scientific order. If `site` and `season` are both additional
information beyond `species`, neither order

```text
species -> species+site -> species+site+season
species -> species+season -> species+site+season
```

is automatically privileged.

The total score gain from the common base to the common full predictor is the
same along either path, but the adjacent held-out increments need not be. A
transfer ceiling reported from one path can therefore depend on a convenience
choice rather than the biology.

ODSP's information-lattice audit makes this dependence explicit.

## Complete subset score table

Let the fixed base information be `C0` and let `Z1,...,Zm` be declared,
variable-disjoint information blocks. The caller supplies a held-out score vector
for every subset of the added blocks:

```text
C0
C0 + Z1
C0 + Z2
...
C0 + Z1 + Z2
...
C0 + Z1 + ... + Zm
```

For `m` blocks this requires `2^m` score nodes. The method deliberately fails if
any subset is absent. Without the missing node, an apparently order-robust result
could simply reflect an unexamined path.

Each block may contain several variables when they constitute one scientific
information unit. Blocks must be mutually variable-disjoint and disjoint from the
fixed base information.

## Every edge is a held-out transfer comparison

For every subset `S` and every block `z` not already in `S`, ODSP scores

```text
S -> S union {z}
```

on the same held-out rows and independent groups.

The ordinary point category of an edge is `generalizing` only when its gain is
positive in every independent group. A large full-vs-base gain cannot override a
failed edge.

For logarithmic scores, an oracle edge has expected value

```text
I(A ; z | C0, S) >= 0.
```

Its magnitude may depend on `S`. A negative fitted held-out edge is therefore not
negative ecological information; it is evidence that the richer fitted
representation failed to add transferable predictive utility in that predecessor
context.

## Path status

Each permutation of the `m` information blocks is one admissible full path. ODSP
does not need to materialize all permutations: it counts successful paths by
dynamic programming on the subset lattice.

The point result distinguishes:

- `universal_full_transfer`: every admissible ordering reaches the full predictor
  through positive all-group edges;
- `order_sensitive_full_transfer`: at least one but not every ordering reaches
  the full predictor;
- `no_full_transfer`: no ordering reaches the full predictor without crossing a
  failed edge.

For two blocks, the known-truth score example

```text
base -> A   +0.4
A -> AB     -0.1
base -> B   +0.1
B -> AB     +0.2
```

has full-vs-base gain `+0.3`, but only one of the two admissible paths succeeds.
The correct result is therefore `order_sensitive_full_transfer`, not universal
transfer to the full information set.

## Block-level order robustness

For one block `z`, collect every lattice edge that adds `z` after every possible
predecessor subset. The block is `order_robust_generalizing` only if all of those
edges are all-group positive.

This is intentionally stronger than saying that one path contains a positive
increment for the block.

## Shapley summary

When every edge is finite, ODSP also reports the standard Shapley order-average
of the held-out marginal score contribution for each information block and each
independent group:

```text
phi_z = sum_S |S|! (m-|S|-1)! / m! * [v(S union {z}) - v(S)].
```

The group-specific Shapley contributions add exactly to the group's full-vs-base
score gain.

This is a descriptive order-average, not the confirmatory decision rule. A
positive Shapley contribution can coexist with a failed marginal edge in some
predecessor context. Therefore

```text
shapley_can_override_edge_failure = false.
```

The underlying Shapley averaging principle is established game theory and is not
claimed as a new ODSP theorem. Likewise, conditional proper-score decompositions
of information sources already exist in the forecasting literature. ODSP uses
these ideas only as supporting summaries around its held-out independent-group
transfer audit.

## Familywise certification over the lattice

`certify_information_lattice()` resamples caller-declared validation blocks
within each independent group. The same block sample is used for every lattice
edge in that group, preserving dependence among all subset comparisons.

A single studentized max-t critical value is then computed over the entire
estimable

```text
independent group x lattice edge
```

family.

The certified path count uses only edges whose category is
`robust_generalizing` across every independent group. It therefore reports the
same three path states at familywise confidence:

- universal full transfer;
- order-sensitive full transfer;
- no full transfer.

An unavailable edge caused by insufficient blocks or non-finite richest-level
support cannot be crossed.

## Why not choose the best ordering?

Selecting the ordering that yields the deepest ceiling after seeing held-out
outcomes is outcome-dependent model selection. It overstates transferability.
The lattice audit instead treats every predeclared admissible ordering as part of
the inferential object.

If scientific knowledge genuinely imposes a partial order among information
blocks, that restriction should be declared prospectively and a corresponding
restricted lattice can be developed. The complete Boolean lattice implemented
here is the appropriate audit when the declared blocks are scientifically
unordered.

## Computational boundary

The complete score table grows as `2^m` and the directed edge count as
`m * 2^(m-1)`. The method is therefore intended for a modest number of
scientifically meaningful information blocks, not thousands of raw covariates.
Raw predictors should first be grouped into predeclared information units when
that grouping is scientifically defensible.

## Claim boundary

The lattice audit diagnoses dependence on information-addition order and can
certify all lattice edges jointly with respect to validation-block uncertainty.
It does not choose information blocks from outcomes, does not fit the subset
models, does not remove upstream refit uncertainty, and does not turn predictive
transfer into a causal attribution.
