# ODSP — Chapter 2: multidimensional niche geometry

ODSP is **Chapter 2** of the fixed four-chapter programme `niche-to-survey-four-chapter-v1`:

1. **SDMR** — which environmental dimensions define an interpretable realized niche?
2. **ODSP** — how thick and multidimensional is that niche beyond a flat x-y map?
3. **EOG** — which distributional/transition worlds remain possible and reachable?
4. **ACSP** — where should field effort be directed next?

See [`FOUR_CHAPTER_PROGRAM.md`](FOUR_CHAPTER_PROGRAM.md), [`CHAPTER_CONTRACT.json`](CHAPTER_CONTRACT.json), and [`CHAPTER2_ROADMAP.md`](CHAPTER2_ROADMAP.md).

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

> **HOW THICK is it? — How much ecological state-space information is lost when a multidimensional niche/support distribution is flattened to x-y?**

The working principle is: **地図は、niche を薄くする。**

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

These quantities answer: **after horizontal location is already known, how many effectively distinct states remain along the added axes?**

`axis_thickness_map(...)` returns the same information separately for each supported x-y cell. A species-support tensor yields descriptive niche thickness; an explicitly defined availability/capacity tensor can instead represent structural state-space capacity. Those interpretations must not be mixed.

## Thickness magnitude versus thickness organization

The current empirical development shows why two distinct questions are needed:

1. **Thickness magnitude:** is added-axis state information present in a fitted support?
2. **Thickness organization / transferability:** does the detailed location-conditioned added-axis distribution remain useful for independent individuals or observations?

A fitted support can be descriptively thick without its fine x-y-resolved organization generalizing.

`odsp.transferability` now makes that distinction explicit and model-agnostic. For base state `B` (for example x-y) and added state `A` (for example z or t):

```text
in-sample organization    = I(A;B)
held-out transferability  = E_heldout[log P_model(A|B) - log P_model(A)]
```

`base_added_mutual_information(...)` measures only fitted organization. `score_conditional_transferability(...)` tests whether that organization predicts independent support better than the lower-information marginal representation. `classify_independent_gains(...)` provides the conservative all-positive / all-nonpositive / mixed rule for prospectively independent held-out groups.

The transferability core deliberately performs no hidden smoothing. Any smoothing or pseudocount rule must be declared upstream before held-out outcomes are opened. Known-truth tests include three deliberately distinct cases: thick but unorganized support, stable organization with positive held-out gain, and shifted organization with negative held-out gain.

## Current empirical status

### Tawaki lane

Terminal category: **`empirical_gate_d_unavailable`**.

The first GPS+dive-lane failed its frozen full site×year structural coverage rule before any thickness outcome was opened. It remains a valid empirical-unavailability result and is not rescued by later work.

### European free-tailed bat lane

Terminal category: **`empirical_n2_thickness_not_generalizing`**.

The second empirical lane used a public native same-event x-y-z Movebank stream for *Tadarida teniotis*. Source architecture, source identity/checksum, 5 km grid, z bins, individual weighting, 6-model/2-sealed split, and answer-check rule were all frozen before numeric height was opened.

Primary result:

```text
H(Z|X,Y)                  = 1.3918623004770097 nats
effective vertical states = 4.022333876564191
sealed Bat5 gain           = -0.43541033813280833
sealed Bat7 gain           = -0.021938657402345435
```

Thus the model-pool support is **descriptively vertically thick**, but the frozen `P_model(z|x,y)` did not predict either sealed bat's vertical state better than the model-pool marginal `P_model(z)`. The detailed x-y-conditioned vertical organization therefore did **not** generalize under this endpoint.

This does **not** mean the vertical axis is absent or that there is no vertical niche thickness. It means the transferable spatial organization required by the frozen empirical support rule is not supported.

See [`N2_BAT_THICKNESS_TERMINAL_DECISION.json`](N2_BAT_THICKNESS_TERMINAL_DECISION.json) and [`docs/n2_bat_thickness_terminal_result_2026-09-01.md`](docs/n2_bat_thickness_terminal_result_2026-09-01.md).

## Input layers

### Source-preserving observation time

`odsp.temporal_information` standardizes observation-time metadata already present in public occurrence sources while retaining source fields and actual precision.

For GBIF this includes fields such as `eventDate`, `eventTime`, year/month/day, day-of-year interval fields and verbatim date. For iNaturalist it includes `observed_on`, `observed_on_string`, `time_observed_at`, `time_observed_at_utc`, `time_zone` and `zic_time_zone` when present.

Rules include:

- upload/creation/update timestamps are **never** substituted for biological observation time;
- date-only records do not become ecological midnight observations;
- timezone is not invented from coordinates at ingestion;
- conflicting duplicate fields are flagged rather than silently resolved;
- missing/partial time remains missing/partial.

### Explicit vertical semantics

`odsp.vertical_information` requires callers to declare the semantic meaning of a vertical field. It distinguishes organism height/depth or structural state from locality elevation, bathymetry, sensor placement and other contextual fields.

The bat primary axis is deliberately the native GPS `height_above_msl`. It is not relabeled as height above ground and no DEM subtraction is introduced post hoc.

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

Raw opportunistic record counts are not automatically treated as unbiased biological-use probabilities. Empirical niche-thickness inference must separately address effort, detectability, sensor geometry, time coverage and vertical coverage. Exact generating niche geometry is available only in known-truth/synthetic validation; empirical claims are about measured or model-supported realized state use under declared observation semantics.

The former ODSP spatial-patch/topology method remains retired. Its defensible support-topology component was migrated to EOG. ODSP must not grow a duplicate reachability/topology implementation.

## Current development boundary

The current empirical N2 chain is scientifically closed at:

```text
known-truth thickness/projection recovery      supported
model-agnostic organization/transferability    implemented
Tawaki empirical lane                          unavailable
Bat structural feasibility                     supported
Bat descriptive vertical thickness             present
Bat cross-individual x-y-z organization         not generalizing
Gate-E forest/grassland promotion               blocked
```

The forest-versus-grassland structural-capacity hypothesis remains interesting but is **not authorized as a continuation or rescue of the completed bat endpoint**. Any future test would require a separately frozen programme with its own measurement architecture and validation logic.

Do not rerun or retune the completed Tawaki or bat endpoints, swap datasets after outcome access, replace primary grid/bin definitions, or use descriptive thickness alone to claim transferable 3D niche organization.
