# BOP_RODENT pooled-baseline gain decomposition

Date: 2026-09-13  
Role: **post-outcome descriptive secondary amendment** to the frozen BOP_RODENT state-prediction endpoint.

## Why this amendment exists

The prospectively frozen BOP_RODENT primary random forest includes fixed species one-hot indicators as predictors, but its frozen primary comparator is the hierarchically weighted **pooled** training altitude-state marginal `P(A)`. The frozen primary held-out gain therefore combines two sources of predictive advantage:

1. replacing the pooled marginal with the training-fold marginal for the held-out species; and
2. predicting additional within-species variation from temperature, location and cyclic time covariates.

This was a valid frozen primary estimand, but the two contributions are scientifically different and should be visible to reviewers.

## Exact decomposition

For each already-scored held-out individual,

```text
G_total   = mean log P_model(A | X, species) - mean log P_pool(A)
G_species = mean log P_species(A)            - mean log P_pool(A)
G_context = mean log P_model(A | X, species) - mean log P_species(A)
```

so that

```text
G_total = G_species + G_context.
```

`P_species(A)` is reconstructed separately within each frozen training fold using the original hierarchical weights: every admitted species has equal total weight, and every training individual within a species has equal total weight. No model was refit, no raw GPS data were re-accessed, and the original pooled comparator remains the primary comparator.

The reconstructed pooled marginal reproduced every frozen individual `mean_marginal_log_score` with maximum absolute error `3.63e-13` nats. The maximum additivity error was also `3.63e-13`.

## Result

Across the 30 frozen held-out individuals:

```text
mean G_total   = +0.570910 nats/event
mean G_species = +0.072794
mean G_context = +0.498116
```

Thus the descriptive mean pooled-comparator gain is dominated by within-species contextual prediction rather than by the pooled-to-species baseline shift. `G_context` was positive for 23/30 individuals.

| Species | n | low <50 | 50-200 | 200-500 | >=500 | mean total | species component | within-species context |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| *Buteo buteo* | 5 | 23,504 | 4,876 | 495 | 94 | +0.230311 | +0.273619 | **-0.043307** |
| *Circus aeruginosus* | 8 | 25,605 | 6,610 | 10,309 | 2,917 | +0.349524 | -0.148767 | **+0.498291** |
| *Circus cyaneus* | 8 | 12,285 | 10,212 | 4,307 | 3,028 | +0.245549 | -0.102246 | **+0.347795** |
| *Circus pygargus* | 9 | 9,974 | 6,678 | 27,989 | 5,772 | +1.246130 | +0.313759 | **+0.932371** |

The large *C. pygargus* gain therefore is **not** primarily explained by species identity relative to the pooled marginal: about `0.932/1.246` nats/event of its descriptive mean gain is the within-species context component. Conversely, *B. buteo* shows the opposite pattern: its species baseline accounts for the positive pooled-comparator gain while the mean within-species context component is slightly negative. The component structure is therefore heterogeneous among species.

## What does not change

This amendment does **not** replace the prospective endpoint or its comparator. The original result remains:

- 27/30 individuals with positive frozen primary RF gain;
- 30/30 with positive Brier improvement;
- terminal category `empirical_state_prediction_mixed` because three individual primary log-score gains were non-positive.

The decomposition is descriptive and post-outcome. It cannot reclassify the endpoint, establish a causal species effect, or claim universal positive within-species context gain.

## Provenance

Frozen primary source:

- workflow run `33897335554`
- artifact `9946375169`
- artifact digest `sha256:49291cf0f2c90955fc23bdc702ccef1ef8b710ce100c8e338c5fc6b91388b8f7`
- frozen result JSON SHA-256 `9e681852d1982e03d9a0696ce5b78c8f367bbffcc401bc54e9b62368a211499d`

Amendment first-green result:

- workflow run `34733014869`
- artifact `10310047790`
- artifact digest `sha256:0bec74c68ffbd00cd4c1d3b08418d21f9f137726a525c579199398784772b6f5`
- amendment result JSON SHA-256 `44a02f584b819a4af83c0d53684ed285cad322b1a3e5ef30aba605e5f3aff352`

Canonical machine-readable summary: `BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json`.
