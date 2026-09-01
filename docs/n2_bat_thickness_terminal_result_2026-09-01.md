# N2 / ODSP — European free-tailed bat terminal empirical result

Date: 2026-09-01  
Program: `niche-to-survey-four-chapter-v1`  
Chapter spine: **N2 — HOW THICK is it? / 地図は、niche を薄くする。**

## Terminal decision

**`empirical_n2_thickness_not_generalizing`**

The result is terminal for the frozen European free-tailed bat empirical lane. It is not a technical STOP and it is not an absence-of-thickness result.

## Frozen provenance

- selected taxon: *Tadarida teniotis*;
- source: Movebank Data Repository DOI `10.5441/001/1.52nn82r9`;
- checksum-pinned original tracking stream MD5: `570872ab7aba674b9bdc2f2ee6044a71`;
- structural-preflight merge: `be5a86e850b99457d1e6055289c2990fb8ca358f`;
- thickness-contract merge: `8250331209cbabf85afdcf92672104e8543816c7`;
- outcome-engine merge: `e99022ffe7a904d3f9917d9315d85ba4cdc91d5c`;
- one-shot execution head: `fe7d66c49902f7bca7a3d0229b15cd1e884ace85`;
- workflow run: `33481773409`;
- execution merge: `7bc820b463294f083376bbd9eff69098ce956bfb`;
- terminal artifact ID: `9790203720`;
- terminal artifact digest: `sha256:4e28817908650ea3dbcf91341c0a27c00982102f0c8a690c1ce8ba5ed5f19d8b`.

No outcome-affecting code, grid, bin, weighting, split, dataset, or z definition was changed after numeric height was opened.

## Primary design

The empirical axis is the native same-event Movebank field `height_above_msl`. It is **not** transformed to height above ground and no DEM subtraction is used.

Primary representation:

- x-y: EPSG:3035, 5 km cells;
- model-pool-only structural eligibility: >=30 events and >=3 model individuals per cell;
- frozen eligible cells: 18;
- z bins: `[-inf, 0, 50, 100, 200, 400, 800, 1600, 3200, inf]` m above mean sea level;
- whole-individual split: 6 model bats, 2 sealed bats;
- model weighting: equal individual weight, not pooled event weight;
- per-individual categorical probabilities: Jeffreys pseudocount 0.5 before individual averaging.

For each eligible cell, `P_model(z|x,y)` is the arithmetic mean of the represented model bats' smoothed within-cell z distributions. `P_model(z)` is the arithmetic mean of the model bats' smoothed marginal z distributions.

## Numeric QC

All structurally joint events had a finite numeric height:

- finite height: 10,335;
- structurally joint x-y-height events: 10,335;
- fraction: 1.0;
- frozen minimum: 0.99.

## Descriptive thickness

The frozen model-pool support produced:

- `H(Z|X,Y) = 1.3918623004770097` nats;
- `exp(H(Z|X,Y)) = 4.022333876564191` effective vertical states.

Thus the fitted model-pool representation is not vertically thin. Conditional on the declared x-y cells, it retains roughly four effective fixed altitude states on average.

This is a **descriptive model-pool statement**. It is not by itself sufficient for the empirical support decision.

## Independent answer check

The sealed answer check asked whether the frozen location-conditioned vertical distribution predicts each new individual's vertical state better than the model-pool marginal vertical distribution:

`mean[log P_model(z|x,y) - log P_model(z)]`.

Frozen results:

| Sealed individual | Scored events | Mean log-score gain |
|---|---:|---:|
| Bat5 | 475 | -0.43541033813280833 |
| Bat7 | 1,049 | -0.021938657402345435 |

Equal-individual mean: **-0.22867449776757687**.

Both gains are <=0. Under the preregistered rule, the answer-check category is therefore:

**`estimable_but_non_generalizing`**.

The terminal category is consequently:

**`empirical_n2_thickness_not_generalizing`**.

## What this means

The empirical data support two different statements that must not be collapsed:

1. **Descriptive thickness exists in the model pool.** A flat x-y representation discards substantial vertical-state detail in those fitted individuals.
2. **The x-y-resolved vertical geometry is not transferable under this endpoint.** Conditioning on x-y made prediction of the sealed individuals' z states worse than using the model-pool marginal z distribution for both sealed bats.

Therefore the correct conclusion is not "there is no vertical niche". The result says that the detailed spatial organization of vertical use inferred from the six model bats is not a stable cross-individual niche map under the frozen design.

A useful conceptual distinction for Chapter N2 is now explicit:

- **thickness magnitude** — how much added-axis state information exists within a fitted support;
- **thickness organization** — whether the location-conditioned added-axis distribution is stable enough to generalize beyond the individuals used to construct it.

The first is descriptively present here; the second is not supported.

## Sensitivities

Sensitivities cannot override the primary decision.

- 2.5 km: `H=1.40948`, effective states `4.09383`; both sealed gains negative; non-generalizing.
- 10 km: `H=1.21287`, effective states `3.36313`; both sealed gains negative; non-generalizing.
- finer frozen z bins: `H=1.44788`, effective states `4.25410`; both sealed gains negative; non-generalizing.
- coarser frozen z bins: `H=1.33214`, effective states `3.78914`; both sealed gains negative; non-generalizing.
- source-marked-outlier exclusion: **not evaluable** because the frozen 18-cell support denominator could not be retained after exclusion.

The scale/bin sensitivities therefore agree with the primary non-generalization result, but they remain secondary evidence only.

## Claim boundary and hard stop

Do not claim from this lane:

- fundamental niche;
- height above ground or canopy-relative height;
- causal vertical habitat preference;
- absence of vertical niche structure;
- a transferable universal 3D niche map;
- support for the forest-versus-grassland Gate-E hypothesis.

Do not rerun, retune, swap the dataset, replace the primary grid/bin scheme, convert the primary z axis to AGL, or select a more favorable individual subset. The European free-tailed bat lane is scientifically closed.

The predecessor Tawaki result remains separately valid as `empirical_gate_d_unavailable`; it must not be replaced or reinterpreted by this bat result.
