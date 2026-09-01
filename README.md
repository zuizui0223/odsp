# ODSP — Chapter 2: multidimensional niche geometry

ODSP is **Chapter 2** of the fixed four-chapter research program:

1. **SDMR** — select interpretable environmental niche axes/drivers;
2. **ODSP** — measure niche dimensionality and thickness hidden by planar maps;
3. **EOG** — infer compatible/reachable distributional worlds;
4. **ACSP** — convert uncertainty into survey action.

See [`FOUR_CHAPTER_PROGRAM.md`](FOUR_CHAPTER_PROGRAM.md) and [`CHAPTER_CONTRACT.json`](CHAPTER_CONTRACT.json).

## Scientific center

A conventional species-distribution product ends as a horizontal support field

```text
S(x, y)
```

but an organism may occupy additional states within the same horizontal cell:

```text
S(x, y, z, t, ...)
```

where `z` can be height above ground, canopy stratum, water depth, soil depth, or another explicitly measured vertical state, and `t` can be time of day, season, phenological phase, tide, or another explicitly measured temporal state.

ODSP asks:

> **How much ecological niche structure is hidden when those added states are collapsed into a flat x-y map?**

The motivating contrast is structural complexity. Equal horizontal area need not contain equal ecological state space: a grassland cell may expose only a small number of distinguishable vertical states, while a forest cell can contain forest floor, herb, shrub, understory and canopy states. ODSP quantifies that difference rather than treating both as one categorical land-cover value.

## Implemented Chapter-2 core

`odsp.niche_geometry` is a model-agnostic information layer for non-negative support tensors. It provides:

- `H(Z | X,Y)` — vertical information remaining after horizontal location is known;
- `H(T | X,Y)` — temporal information remaining after horizontal location is known;
- `H(Z,T | X,Y)` — joint vertical-temporal information;
- `exp(H)` — effective number of added states, an interpretable niche-thickness scale;
- `I(Z;T | X,Y)` — conditional dependence/redundancy between vertical and temporal use;
- `axis_thickness_map(...)` — per-x-y-cell information and effective-state maps;
- `niche_thickness_profile(...)` — whole-support summaries.

Example:

```python
import numpy as np
from odsp import axis_thickness_map, niche_thickness_profile

# y × x × vertical stratum
support = np.zeros((1, 2, 4), dtype=float)
support[0, 0, 0] = 1.0       # thin: one used stratum
support[0, 1, :] = 1.0       # thick: four equally used strata

local = axis_thickness_map(
    support,
    horizontal_axes=(0, 1),
    added_axes=(2,),
)

print(local.effective_states)  # [[1., 4.]]

profile = niche_thickness_profile(
    support,
    horizontal_axes=(0, 1),
    vertical_axis=2,
)
```

If an equal-weight tensor describes structurally available states rather than species support, the same machinery yields a descriptive **ecological state-space capacity** map. That is different from species niche use and must be labelled accordingly.

## Time as an input axis

`odsp.temporal_information` preserves observation time from public biodiversity records without fabricating precision. It currently normalizes GBIF and iNaturalist observation-time fields and retains date/time precision, source-provided UTC/time-zone information, raw fields, and quality flags.

Important rules:

- upload/creation/update timestamps are never substituted for biological observation time;
- date-only records do not become midnight observations;
- time zones are not inferred from coordinates during ingestion;
- missing or partial time remains missing/partial;
- timestamp availability alone does not establish a temporal niche.

See [`TEMPORAL_INFORMATION_LAYER.md`](TEMPORAL_INFORMATION_LAYER.md).

## Elevation is not the z axis

A raster elevation value is normally one attribute of an x-y surface. It can act as a geophysical template or proxy for temperature, snow, vegetation and other processes in Chapter 1 / SDMR.

ODSP's `z` axis instead means **multiple ecological states available within the same horizontal location** — for example ground, herb layer, shrub layer, understory and canopy. Keeping these concepts separate is part of the chapter boundary.

## Scientific boundaries

The current niche-thickness metrics are descriptive geometry, not a validated biological niche model. In particular:

- raw opportunistic occurrence counts are not assumed to be unbiased use probabilities;
- empirical z/t analysis requires observation effort and detectability at matching resolution;
- niche thickness is not occupancy probability, abundance, competition or a causal coexistence mechanism;
- it does not identify the physiological/fundamental niche;
- SDMR Product A remains scientifically closed and is not retuned by Chapter 2;
- EOG remains the owner of support topology, reachability and alternative distributional worlds;
- ACSP remains the survey-action layer.

## Historical ODSP boundary

ODSP's former spatial-patch/topology method remains superseded. Its defensible support-topology component was migrated to EOG at merge `023261f4cac6d70973d097634807472976df749b` (EOG PR #61). Those spatial algorithms are not reintroduced here.

The active ODSP identity is now **multidimensional niche geometry plus source-preserving axis information**.
