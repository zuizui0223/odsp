# Chapter 2 synthetic benchmark design

Status: development design; no empirical claim.

This document defines the first known-truth families for ODSP Chapter 2 before any empirical habitat-complexity result is used to tune them.

## Common state space

Use a normalized support tensor with axes:

```text
Y × X × Z × T
```

Horizontal dimensions are held fixed when the target contrast is niche thickness. The generating tensor is treated as truth and is not available to any future estimator until final scoring.

## Family 0 — planar sufficiency

Within each occupied x-y state there is exactly one z state and one t state.

Expected:

- `exp(H(Z|XY)) = 1`;
- `exp(H(T|XY)) = 1`;
- no pairwise overlap inflation from marginalizing z/t.

Purpose: negative control showing that extra axes are not automatically rewarded.

## Family 1 — pure vertical thickness

Each x-y cell contains `k_z > 1` equally supported vertical states, with one time state.

Expected:

- `exp(H(Z|XY)) = k_z`;
- temporal thickness = 1;
- full added thickness = `k_z`.

Purpose: canopy/depth analogue.

## Family 2 — pure temporal thickness

Each x-y cell contains `k_t > 1` equally supported time states, with one z state.

Expected:

- temporal thickness = `k_t`;
- vertical thickness = 1.

Purpose: season/diel analogue.

## Family 3 — independent z × t thickness

Each x-y cell contains all combinations of `k_z × k_t` with factorized support.

Expected:

- vertical thickness = `k_z`;
- temporal thickness = `k_t`;
- joint thickness = `k_z * k_t`;
- conditional z–t interaction information = 0.

## Family 4 — coupled z × t states

Marginal z and t use are broad, but only a subset of z×t combinations is permitted.

Expected:

- vertical and temporal thickness remain >1;
- joint thickness is lower than their product;
- conditional z–t interaction information is positive.

Purpose: detect structure that neither axis alone fully describes.

## Family 5 — projection-hidden pairwise partition

Construct two taxa with identical x-y marginals but disjoint z, t, or joint z×t support.

Expected:

- horizontal Schoener overlap may equal 1;
- full overlap may approach 0;
- planar overlap inflation is positive;
- vertical-only, temporal-only and joint-only families are distinguishable.

## Family 6 — habitat structural capacity

Hold the horizontal footprint and total mass fixed while varying the number and evenness of available z states.

Motivating contrast:

- structurally simple habitat: low effective vertical state count;
- layered habitat: high effective vertical state count.

This family validates the quantity only. It does not assume that real forests must exceed real grasslands; that is an empirical hypothesis requiring matched observation coverage.

## Scoring gates

A future known-truth benchmark should require:

1. exact or tolerance-bounded recovery of analytically known effective state counts in Families 0–4;
2. correct ordering of planar overlap inflation in Family 5;
3. correct capacity ordering in Family 6;
4. invariance to positive rescaling of support mass;
5. explicit abstention/failure under zero mass, negative support, invalid axes, or wholly unavailable state space.

No empirical dataset may be used to change these expected directions after outcome inspection.
