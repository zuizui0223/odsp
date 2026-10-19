# Equal daylight, different thermal–water contexts: database-first geographic pilot

**2026-10-19 | ODSP PR #267 | New environmental database; no animal-response estimate.**

## What was advanced

This step stops adding endpoints to the same nine GPS birds. It tests the environmental premise of the ecological question using a newly specified geographic frame, rather than selecting papers or sites by their reported animal effects: **at matched modeled photoperiod, does the sign of seasonal thermal change determine the sign of climatic water change?**

The design was committed before retrieving the new climate values: `research/SOLAR_SEASON_MACROCLIMATE_PILOT_20261019.json`, commit `8c56d5b4ec633926e56427a5b8e4e0e2236a3e32`. This is a 20-point pilot, not an area-unbiased global estimate or a biome census. Seasonal thermal lag is not claimed as a new discovery. The contribution is a reusable source-backed database that separates thermal and water contexts relevant to later animal-response tests.

## Sampling and source

Seven latitude bands (-45,-30,-15,+15,+30,+45,+60 degrees) and 48 longitudes per band give **336 candidates**. A checksum-verified Natural Earth 110m land union, with a 0.25-coordinate-degree boundary buffer, leaves **102 land-eligible candidates**. One point per latitude and longitude sector is selected by the minimum SHA256 of a fixed seed plus coordinates. Empty strata remain empty; **20 points** are selected without weather values or wildlife records. This reproducible hash selection is not a land-area probability sample.

The candidate list and selected-point registry were archived **before the first weather request**, in artifact `macroclimate-land-only-roster-20261019` (12160393551). Registry SHA256: `d1190ecce82c6117eaabca12edb5c057e8aba8b554e70fa3e7ef4229aedfe5e7`.

Climate comes from **C3S/ECMWF ERA5 via Open-Meteo**, fixed `models=era5`, `cell_selection=nearest`, `elevation=nan`. The data are reanalysis estimates, not direct field observations. Daily source range is 2017-12-01–2023-06-30. Fixed UTC offsets rounded from longitude/15 approximate local mean-solar dates and avoid DST changes.

For each local summer-solstice cycle **2018–2022**, compare dates 21–160 days before and after **June 21 in the north / December 21 in the south**. Pairing maximizes one-to-one matches and then minimizes total absolute modeled daylength mismatch, with a **two-minute caliper**, no date reuse and no climate-dependent date selection. Daylength uses the registered NOAA fractional-year approximation, not terrain-corrected sunlight. Require >=60 valid pairs and >=80% of the astronomical roster per point/cycle.

The primary response is mean air-temperature difference. Secondary responses are maximum air temperature, preceding-30-day precipitation, and preceding-30-day `sum(P − reference ET0)`. The latter is a **climatic supply-minus-reference-demand proxy**, not actual evapotranspiration, soil moisture, measured drought, vegetation or forage. A larger value can still be negative in absolute terms. Temperature and this derived index are not independent variables because ET0 uses meteorological inputs including temperature.

## Completed source database

[Workflow 39192649276](https://github.com/zuizui0223/odsp/actions/runs/39192649276) completed successfully. All **20 selected sites** were retrieved: **40,760 point–day records**, **100 qualified point–summer-cycle comparisons**, and **13,386 valid one-to-one photoperiod date pairs**. No site failed or was replaced.

SQLite and corresponding CSV tables retain selected sites, source provenance, daily data, every paired date, point/cycle results and point summaries. Raw response snapshots and exact URLs/hashes are retained; response SHA256s are local snapshot fingerprints, not provider attestations. The full database artifact is `solar-season-macroclimate-database-20261019` (12161086477), ZIP SHA256 `dc8a1f165cde1fbc7eff30728092f13ac1b37b51817e2a1f55262b20e3571313`.

## Actual environmental results

All differences are **decreasing-daylength minus increasing-daylength**.

| Joint context | Points classified by five-cycle means | Point–cycle instances |
|---|---:|---:|
| Warmer, climatic water balance lower | **9** | **47** |
| Warmer, climatic water balance higher | **8** | **41** |
| Cooler, climatic water balance higher | **3** | **12** |
| Cooler, climatic water balance lower | 0 | 0 |

The 100 entries are repeated years at 20 points, not 100 independent ecosystems. These are descriptive signs, not significant effects or estimated global frequencies. Absence of the fourth combination does not imply impossibility.

The five-cycle mean temperature differences span **-2.297 to +12.287 °C**; climatic water-balance differences span **-79.75 to +234.32 mm** for the 30-day index. Sixteen points are warmer in every cycle, one is cooler in every cycle, and three change thermal sign. Water-balance sign persists in all five cycles at 15 points, while five change sign. Joint signs are invariant across five cycles at 12 points and variable at eight.

### Same latitude, opposite water context

The three registered **30°S** points use the same daylength matching but yield:

| Longitude | Delta mean T | Delta preceding-30d precipitation | Delta preceding-30d P−ET0 | Water-index sign in five cycles |
|---|---:|---:|---:|---|
| 63.75°W | **+2.993 °C** | +61.24 mm | **+60.69 mm** | higher 5/5 |
| 18.75°E | **+4.568 °C** | +4.65 mm | **-37.04 mm** | lower 5/5 |
| 116.25°E | **+6.180 °C** | -5.68 mm | **-79.75 mm** | lower 5/5 |

These are illustrative post-inspection rows from the complete unchanged sample, not three newly selected confirmatory tests. At the middle point, precipitation rises slightly but reference demand increases more. Across the full pilot, **four points have positive five-cycle precipitation differences but negative P−ET0 differences**. This arithmetic does not establish observed soil drying.

At **15°N, 78.75°E**, the decreasing branch is cooler in all five cycles: mean **-2.297 °C**, with a higher water index **+166.11 mm**. Thus an everywhere-warmer declining branch is not even a descriptive property of this fixed pilot.

## Full point means

| Latitude | Longitude | Delta mean T, °C | Delta P30, mm | Delta P−ET0 (30d), mm | Warmer cycles | Higher-water-index cycles |
|---:|---:|---:|---:|---:|---:|---:|
| -45 | -71.25 | +4.547 | -6.44 | -43.82 | 5/5 | 0/5 |
| -45 | +168.75 | +5.371 | -23.69 | -55.91 | 5/5 | 0/5 |
| -30 | -63.75 | +2.993 | +61.24 | +60.69 | 5/5 | 5/5 |
| -30 | +18.75 | +4.568 | +4.65 | -37.04 | 5/5 | 0/5 |
| -30 | +116.25 | +6.180 | -5.68 | -79.75 | 5/5 | 0/5 |
| -15 | -71.25 | -0.616 | +154.99 | +171.99 | 2/5 | 5/5 |
| -15 | +48.75 | +2.370 | +225.41 | +234.32 | 5/5 | 5/5 |
| -15 | +131.25 | -0.427 | +100.87 | +134.19 | 2/5 | 5/5 |
| +15 | -86.25 | +0.303 | +92.48 | +93.18 | 4/5 | 5/5 |
| +15 | +26.25 | +2.387 | +22.93 | +47.22 | 5/5 | 5/5 |
| +15 | +78.75 | -2.297 | +115.68 | +166.11 | 0/5 | 5/5 |
| +30 | -108.75 | +4.457 | +89.52 | +89.79 | 5/5 | 4/5 |
| +30 | +11.25 | +7.464 | -0.73 | -59.86 | 5/5 | 0/5 |
| +30 | +93.75 | +10.750 | +95.75 | +76.44 | 5/5 | 5/5 |
| +45 | -93.75 | +12.287 | +36.15 | -13.91 | 5/5 | 2/5 |
| +45 | +26.25 | +8.272 | -4.03 | -43.85 | 5/5 | 0/5 |
| +45 | +101.25 | +8.776 | +11.38 | -36.94 | 5/5 | 0/5 |
| +60 | -123.75 | +11.479 | +17.54 | -17.96 | 5/5 | 2/5 |
| +60 | +33.75 | +8.792 | +26.69 | +3.41 | 5/5 | 2/5 |
| +60 | +78.75 | +10.885 | +31.41 | +2.58 | 5/5 | 3/5 |

Small multi-year water differences at the last two points are not stable ecological states: their annual signs vary. Coarse reanalysis and mountain/continental geography also limit interpretation of large thermal contrasts as individual microclimates.

## What this contributes to the animal hypothesis

**Matched daylength does not guarantee matched thermal–water context, even at the same latitude.** Therefore, a proposed general animal rule should be conditional on environmental differences, rather than predict one common nighttime shift from the label “declining photoperiod.”

A falsifiable next biological hypothesis is that these thermal and resource-related contexts help predict whether an animal reduces daytime use, increases nighttime use, changes location, or remains similar. **That animal response is not measured here.** No NDVI, actual forage, animal tracking or camera observation was added. Integrating animal data will require compatible dates, observation units, spatial scales and sampling opportunities; new weather points alone are not animal replication.

## Independent verification

Seven fixtures passed before execution: deterministic land-only roster selection, hemispheric summer dates, maximum matching checked against brute force on all 512 possible 3×3 candidate graphs, constant-climate zero contrasts, missingness, fixed-offset signs and typed SQLite storage.

After downloading the result archive, a separate local verifier recomputed all daily rolling indices and pair differences directly from the **20 raw API responses**, reconciled every point/cycle and point mean, checked all registry selections, no reused dates, CSV/SQLite values and row counts, and SQLite integrity. Maximum modeled mismatch: **1.999869308147 minutes**. This verifies calculations and snapshots, not independent physical weather truth.

Implementation: `scripts/solar_season_macroclimate_20261019.py`; tests: `tests/test_solar_season_macroclimate_20261019.py`; workflow: `.github/workflows/solar-season-macroclimate-20261019.yml`, code commit `38521de20aee2d3b2f19d698d923527f228a0efd`.

## Sources and attribution

- C3S/ECMWF ERA5: https://www.ecmwf.int/en/forecasts/datasets/era5-hourly-data-single-levels-1940-present ; DOI https://doi.org/10.24381/cds.adbb2d47 .
- Open-Meteo source and reference-ET0 definitions: https://open-meteo.com/en/docs/historical-weather-api .
- Natural Earth land: https://www.naturalearthdata.com/downloads/110m-physical-vectors/110m-land/ ; source ZIP https://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip .
- Maintainer checksum catalogue: https://github.com/geopandas/geodatasets/blob/main/geodatasets/json/database.json . Original land SHA256 `1926c621afd6ac67c3f36639bb1236134a48d82226dc675d3e3df53d02d2a3de`.

**PR #267 remains Draft.** Historical Serengeti, Rhode Island, Uljin, satellite and GPS numerical results are untouched. This environmental pilot is not a claim that seasonal climatic lag itself is novel or that animal generality has been established.
