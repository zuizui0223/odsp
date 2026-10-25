# Same astronomical daylight, different ecological calendars in two original ungulate telemetry studies

**ODSP ecology-first public-source synthesis — 25 October 2026.** This report is an *observational, after-outcomes cross-study description* of two independently obtained wildlife GPS archives, not a model-prediction benchmark, causal test or newly preregistered comparative mechanism.

## Why this changes the ecological research question

The same original GPS day/night source estimand was used with different publicly archived North American ungulate study cohorts. The source metric is **q = log(1+median NIGHT observed GPS step km/h) − log(1+median DAY observed GPS step km/h)** on qualified within-individual tracking days; it does **not** measure activity duration, travel effort, movement-active probability or biological light entrainment.

Both independent-source mule deer samples had remarkably similar *unconditional* within-animal-year q vs astronomical daylength slopes: **Utah +0.0056194** versus **Wyoming +0.0055382** per extra daylight hour. These both had positive **individual-cluster** descriptive intervals on source GPS records.

**But conditioning on the same source-observed date's modelled ERA5 daily Tmax and preceding-30-day (precipitation − reference ET0) produced different conditional associations:**
- **Utah mule deer**: −0.0013405 (95% animal-bootstrap interval **−0.0024893 to −0.0001074**; 1,653 eligible animals)
- **Wyoming mule deer**: +0.0042378 (**+0.0028538 to +0.0056600**; 117 eligible animals)

The comparison is particularly informative because each study contains its own mule deer population and applies the **same original date-level environmental adjustment**; the positive raw photoperiod tendency alone does **not** establish an environmentally invariant ecological mechanism. The contrast in conditional slopes may reflect different thermal/water calendars, vegetation phenology, movement behavior, age/sex recruitment, habitat, study years and devices. **It does not identify which explanation is correct.** The raw and jointly adjusted slopes were estimated on partly different eligibility subsets; their numerical difference is NOT by itself an exact climatic mediation fraction.

Bighorn sheep did not have a clearly resolved positive daylength coefficient in either source; Utah pronghorn and wapiti had positive marginal daylength slopes whose source climate-adjusted intervals included zero. These are legitimate biological heterogeneity and absence-of-identified-direction findings, not an invitation to select only one positive species.

| Source | Original taxon | Unconditional individual-year q/daylight slope | Conditional daylight given Tmax + 30d P−ET0 | Animals admitted to joint model |
| --- | --- | ---: | ---: | ---: |
| Utah | Pronghorn | +0.004900 | −0.001101 | 213 |
| Utah | Wapiti | +0.009599 | +0.002408 | 331 |
| Utah | Mule deer | **+0.005619** | **−0.001340** | 1,653 |
| Utah | Bighorn sheep | −0.003412 | +0.001466 | 337 |
| Wyoming | Mule deer | **+0.005538** | **+0.004238** | 117 |
| Wyoming | Bighorn sheep | +0.000217 | −0.000516 | 41 |

All original source individual counts, uncertainty intervals, null values, negative values and original DOI are preserved in [source-level derived CSV](source_level_daily_climate_daylight.csv). Inferences are conditional on the original sampled animals, not the world's species populations. **Only two independently archived recruitment study cohorts** are involved, and two source populations do not establish a global ecological law.

## Source-replay receipt and important uncertainty discovered October 25

The original October 23 source GPS/ERA5 analyses were successfully run with provider-original GPS MD5 and original raw q/daylength result replays:

- [Utah 4-taxon original GPS and 28-grid date-level ERA5, run 39878716871](https://github.com/zuizui0223/odsp/actions/runs/39878716871): 4 taxa, zero ERA5 source grid holds.
- [Wyoming 2-taxon original GPS and 6-grid date-level ERA5, run 39878174016](https://github.com/zuizui0223/odsp/actions/runs/39878174016): 2 taxa, zero ERA5 source grid holds.

**New audit on October 25:** A post-outcome experimental route that re-fetched public ERA5 and attempted to algebraically decompose individual daylight coefficients verified Wyoming's original GPS source and all 6 weather grid requests, but **FAILED exact replay of the prior environment-adjusted mean**. Original +0.004237831 became **+0.004304305** for the same 117 mule deer under the **original unchanged adjustment algorithm and newly retrieved weather**. The original API JSON source hashes also differ between retrievals. Hash variation alone may reflect non-data fields (e.g. response generation timing); the model-coefficient shift demonstrates that the current replay inputs are not numerically identical. The exact data-processing change behind that difference has **not been isolated**, so do not assert that ERA5 science data were revised. The October 25 experimental decomposition route remains **SOURCE HOLD**, and its potentially novel biological coefficients must NOT be promoted as verified original results.

This integrity conflict is a **reproducibility limitation**. It does not automatically invalidate the source-bounded October 23 ecological observations, but it restricts attempts to infer exact subsequent mediation components using newly fetched data without frozen weather bodies. Earlier original outcomes are **preserved unchanged**. Ecological mechanisms require original source climate values to be snapshotted or source releases version-matched before follow-up statistical claims.

## Biological hypothesis for the next independent test

**Ecological-calendar coupling hypothesis:** across a species' populations, the association between solar-daylength and day/night movement speed is not fixed; it changes with the temperature, water and vegetation phenological state those same animals encounter. A genuine test would compare multiple independent original cohorts with **identically archived versioned weather and independent satellite vegetation** at source dates/locations and then investigate reproductive stage, habitat and source observation schedule. Causation cannot be inferred from this initial comparison.

**Potential falsification:** if direct vegetation and hydrologic phenophase and sampling context are properly aligned but conditional daylight associations remain equally context-dependent without relation to those states, the proposed eco-calendar explanation would need revision.

The goal is **discovering ecological organization and its heterogeneity**, not proving prediction transfer or improving camera detection.

## Credits and non-redistribution

- Utah original telemetry: Movebank DOI [10.5441/001/1.711](https://doi.org/10.5441/001/1.711), provider metadata CC0.
- Wyoming original telemetry: Movebank DOI [10.5441/001/1.703](https://doi.org/10.5441/001/1.703), original metadata CC BY-NC 4.0; preserve attribution and noncommercial rights for any raw-source downstream use.
- Source data are from others' openly archived tracking collections; **the new research object is the systematically defined original-source integration, cross-study biological contrast and testable ecological-calendar question**, not an original field-data-collection claim.
- No original tagged-animal IDs, exact source dates, GPS coordinates, or source animal trajectories are exported.
