# ODSP — Chapter 2: multidimensional niche geometry

ODSP is **Chapter 2** of the fixed four-chapter programme `niche-to-survey-four-chapter-v1`:

1. **SDMR** — which environmental dimensions define an interpretable realized niche?
2. **ODSP** — how thick and multidimensional is that niche beyond a flat x-y map?
3. **EOG** — which distributional/transition worlds remain possible and reachable?
4. **ACSP** — where should field effort be directed next?

See [`FOUR_CHAPTER_PROGRAM.md`](FOUR_CHAPTER_PROGRAM.md) and [`CHAPTER_CONTRACT.json`](CHAPTER_CONTRACT.json).

## Scientific center

A conventional species-distribution product ultimately collapses support to a horizontal field:

```text
S(x, y)
```

ODSP asks what that projection discards. An ecological state can instead be indexed by additional axes:

```text
S(x, y, z, t, ...)
```

where `z` may represent canopy stratum, height, water/soil depth or another explicit vertical state, and `t` may represent observation/activity time, date or season when the source precision permits it.

The Chapter-2 question is:

> **How much ecological state-space information is lost when a multidimensional niche/support distribution is flattened to x-y?**

This is especially relevant for structurally complex habitats. Equal horizontal area need not imply equal ecological state-space capacity: a vertically layered forest can contain many distinguishable states within one x-y cell, whereas a structurally simple grassland may contain fewer.

## Niche thickness

`odsp.niche_geometry` provides model-agnostic information-theoretic metrics on any non-negative support distribution.

For horizontal axes `X,Y`, vertical axis `Z` and time axis `T`:

```text
vertical information      = H(Z | X,Y)
temporal information      = H(T | X,Y)
joint added information   = H(Z,T | X,Y)
```

The corresponding effective state counts are:

```text
vertical thickness        = exp(H(Z | X,Y))
temporal thickness        = exp(H(T | X,Y))
joint added thickness     = exp(H(Z,T | X,Y))
```

These quantities answer a specific question: **after horizontal location is already known, how many effectively distinct states remain along the added axes?**

Examples:

- one usable vertical stratum in every x-y cell → effective vertical thickness ≈ 1;
- four equally used canopy strata in every x-y cell → effective vertical thickness = 4;
- two activity periods that are completely determined by location → global time diversity may be 2, but conditional temporal thickness = 1;
- independent two-level z and two-level t use within each location → effective joint thickness = 4.

The implementation also reports conditional z–t dependence as a descriptive information quantity. It is not a causal interaction statistic.

## Active input layer: source-preserving observation time

`odsp.temporal_information` standardizes observation-time metadata already present in public occurrence sources while retaining source fields and their actual precision.

For GBIF this includes fields such as `eventDate`, `eventTime`, year/month/day, day-of-year interval fields and verbatim date. For iNaturalist it includes `observed_on`, `observed_on_string`, `time_observed_at`, `time_observed_at_utc`, `time_zone` and `zic_time_zone` when present.

Canonical output records:

- source and source occurrence ID;
- observed date and/or datetime;
- source-provided UTC representation when available;
- time-zone name and UTC offset when supplied;
- explicit temporal precision: year, month, day, minute, second, interval or unknown;
- year/month/day/day-of-year and clock fields only when supported by the source;
- raw source time fields and fail-closed quality flags.

Rules:

- upload/creation/update timestamps are **never** substituted for biological observation time;
- date-only records do not become ecological midnight observations;
- timezone is not invented from coordinates at ingestion;
- conflicting duplicate fields are flagged rather than silently resolved;
- missing/partial time remains missing/partial.

## Example

```python
import numpy as np
from odsp import niche_thickness_profile, normalize_occurrence_time

observation_time = normalize_occurrence_time(
    "gbif",
    {
        "key": 123,
        "eventDate": "2026-05-17T21:34:12+09:00",
        "year": 2026,
        "month": 5,
        "day": 17,
    },
)

# y × x × canopy-stratum support.
forest_support = np.ones((2, 3, 4), dtype=float)
profile = niche_thickness_profile(
    forest_support,
    horizontal_axes=(0, 1),
    vertical_axis=2,
)

print(observation_time.temporal_precision)  # second
print(profile.effective_vertical_states)   # 4.0
```

## Scientific boundary

ODSP does **not** modify SDMR Product A. It is not a new environmental-variable selector, AUC replacement, or SDM tuning endpoint.

Raw opportunistic record counts are also not automatically treated as unbiased biological-use probabilities. Empirical niche-thickness inference must separately address effort, detectability, sensor geometry, time coverage and vertical coverage. Exact generating niche geometry is available only in known-truth/synthetic validation; empirical claims are about measured or model-supported realized state use under declared observation semantics.

## Relationship to the historical ODSP

The former ODSP spatial-patch/topology method remains retired. Its defensible support-topology component was migrated to [`zuizui0223/eog`](https://github.com/zuizui0223/eog). ODSP must not grow a duplicate reachability/topology implementation.

The active Chapter-2 scope is instead **multidimensional niche geometry and the information layers required to represent it**.

## Current goal

Build the Chapter-2 evidence chain in this order:

1. mathematical/synthetic validation of niche-thickness and projection-loss quantities;
2. source-preserving time and vertical metadata ingestion;
3. known-truth examples where x-y projection deliberately hides z/t structure;
4. independent empirical applications with defensible effort/detectability semantics;
5. habitat-complexity comparison, including the hypothesis that structurally layered systems such as forests contain greater ecological state-space thickness than simpler planar habitats.
