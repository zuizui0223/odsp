# Equal daylight, divergent hydrothermal seasonal trajectories across a fixed land-grid pilot

**2026-10-19 — FIRST VERIFIED NUMERICAL GLOBAL-GRID PILOT; exploratory regional reanalysis, not a global population result or animal behavior.**

## Biological question

Does matching the length of the sunlit day on opposite seasonal branches imply similar ecological conditions? The earlier original Snapshot Serengeti field-source study documented stronger vegetation greenness on the decreasing-daylength branch while mammalian CAMERA PHOTO-time and CAMERA-location compositions varied. A broader ecological question is whether the season-associated environment itself can be represented by a single common “warmer/wetter” seasonal direction across places, or whether temperature and surface moisture have geographically different, sometimes opposing trajectories.

This is a PROSPECTIVE BIOLOGICAL HYPOTHESIS GENERATOR for animals' time-vs-location responses, **not** a new demonstration of animal climate adaptation, day-night activity or causal temperature/resource trade-offs.

## Source-blind sampling and provenance

The original `GLOBAL_GRID_EQUINOX_ENVIRONMENT_PILOT_20261019` exploratory choices were recorded **locally before the new climate outcomes** in the previous work package; the frozen choices were added to GitHub after API retrieval for transparency, **not** misrepresented as publicly preregistered.

- Initial **72 fixed points** at six latitude lines (−45,−30,−15,+15,+30,+45°) and 12 longitude lines (−180..+150°, 30° steps).
- Original offline, low-resolution Natural Earth land-mask screen yielded **21 fixed mainland/large-land points** (six south, 15 north), with no shifting to more promising sites after outcomes. These locations fall in **six geographic continent labels** (Africa, Asia, Europe, North America, South America and Oceania). They are NOT area-weighted random locations, representative of each continent or individual independent ecosystems.
- **2018, 2019, 2020** astronomical year cycles. North uses rising-daylength March and falling-daylength September of the same calendar year; South uses rising-daylength September and falling-daylength following March (the summer-solstice period). Dates were selected by astronomical declination/daylength alone, not ERA5 values: 63 site×cycle pairs, maximum modeled daylength mismatch **0.799784 minutes**.
- Open-Meteo **historical ERA5** explicitly `models=era5`, `timezone=auto`: same originally requested site local-date daily mean and maximum 2m temperature (°C), and mean surface 0–7cm volumetric soil moisture (m³/m³). These are **climate-reanalysis model outputs**, not direct weather, soil profile measurements, vegetation productivity or animal observations.
- Official API documentation: https://open-meteo.com/en/docs/historical-weather-api; original source retains each of **12** source URLs, returned site order, source date, time zone, original units and all values in two immutable-at-commit original response files. The original 21-site CSV and local source-blind protocol are also stored.
- Validation rejects source grid/date/timezone or unit mismatches, null/nonfinite, temperature max below mean, and soil volumetric fractions outside [0,1]. It keeps all planned pairs. **No model, date or location substitutions, weather imputation, post-result p-values or effect selection**.

### Original source and independent reproduction

- [Southern original 6 batches](../research/solar_global_equinoctial_pilot_20261019/era5_southern_6batches_original_source.json)
- [Northern original 6 batches](../research/solar_global_equinoctial_pilot_20261019/era5_northern_6batches_original_source.json)
- [Original 21 land sites](../research/solar_global_equinoctial_pilot_20261019/original_21_land_grid_sites.csv)
- [Original local protocol, archived only after source retrieval](../research/solar_global_equinoctial_pilot_20261019/original_local_protocol_20261019.json)
- [Replay script](../scripts/analyze_fixed_21site_global_equinoctial_era5_20261019.py), [six regression/known-truth tests](../tests/test_fixed_21site_global_equinoctial_era5_20261019.py), [original-source verified GitHub Actions CI 39201993065](https://github.com/zuizui0223/odsp/actions/runs/39201993065).
- All **six tests passed** and true source replay succeeded. GitHub artifact `odsp-original-global-equinox-era5-21sites-2018-2020` (ID **12164495464**) contains the complete **63-row CSV and exact numeric/source receipt JSON**. This is independently reproduced from the already saved original 12 API batch bodies; no live value was invented or copied from a synthetic fixture.

## First authentic modeled climate results

**62/63** original site×cycle pairs admitted. One original **2019** Iran point (+30°, +60°) returned **−0.001 m³/m³** in its declining-daylight soil-moisture response; a negative volumetric fraction is physically invalid. All three originally frozen variables for this pair are therefore **HOLD_PHYSICALLY_INVALID_SOIL_MOISTURE**, *not* zero; other 62 remain. Original raw source still contains the invalid value for provenance.

| Fixed-pair contrasts (falling − rising) | Positive | Negative | Exactly zero | Qualified pairs |
|---|---:|---:|---:|---:|
| Daily mean 2m temperature | **49** | 13 | 0 | 62 |
| Surface 0–7cm volumetric soil moisture | **38** | 20 | 4 | 62 |

Out of 62 valid pairs, **29** have *opposite signs* of their temperature and soil moisture shifts (18 warmer/drier; 11 cooler/wetter). Among the other pairs, 27 are warmer/wetter, two cooler/drier, and four warmer with no change in modeled surface moisture. The simple arithmetic mean across all *non-area-weighted* pair-years is **+6.853°C** temperature and **+0.02339 m³/m³** soil moisture; the means should **NOT** be called an average effect over Earth's land. The source also supplies 2018/2019/2020 repeated site observations, which are not independent new regions.

At the full-sample site level, **20 of 21** geographic points have all three original years qualified. **10/20** have opposite signs for their *three-year mean* temperature and moisture changes. **Five source points** have opposite signs of the *year-specific two-variable contrast on all three original pairs*, including a meaningful diversity of directions:

| Public fixed coordinate / region | Mean Δ air T (°C) | Mean Δ soil moisture (m³/m³) | Three original pair-year directions |
|---|---:|---:|---|
| Brazil (15°S, 60°W) | **−2.900** | **+0.1537** | Cool/wetter ×3 |
| Zambia (15°S, 30°E) | **−1.767** | **+0.1870** | Cool/wetter ×3 |
| Egypt (30°N, 30°E) | **+9.067** | **−0.0513** | Warm/drier ×3 |
| Oregon, USA (45°N, 120°W) | **+10.667** | **−0.2477** | Warm/drier ×3 |
| Argentina (30°S, 60°W) | **+1.867** | **+0.0273** | Each original year OPPOSED, but 3-year mean IS NOT |

### Non-obvious result: aggregating years can erase opposing paths

The fixed Argentina grid point in original pairs:
- 2018: **+1.4°C, −0.043 m³/m³** (warmer/drier).
- 2019: **+7.8°C, −0.026 m³/m³** (warmer/drier).
- 2020: **−3.6°C, +0.151 m³/m³** (cooler/wetter).

Every original **year-specific** daylength-matched contrast pairs *temperature and soil water in opposite directions*, but taking their arithmetic three-cycle means yields **+1.867°C and +0.0273 m³/m³**: a misleading *warmer/wetter* joint sign. This is a clear empirical aggregation/mixing caveat relevant to ODSP; it is **not** a formally identified Simpson's paradox, a measured plant-water physiological trade-off, or a causal climate relationship.

The accepted pilot spans six geographic continent labels but has only **21 preselected fixed land points**, one snapshot day-pair per year, and no Arctic/Antarctic or equatorial sampling. Hence strong global prevalence claims, biome-level hypothesis tests and p-values are not warranted. No inference is made about global proportions of warmer/wetter/drier seasons, or about wildlife shifts in any of these cells.

## What this says and does not say about ecology

**Supported**: the same near-equinox solar-daylight duration can coexist with opposite local thermal and shallow-soil water changes; in some fixed sites those opposed directions recur across three years, and their ecological signal can be masked by temporal averaging. The cross-region sign varies even when astronomical geometry is pre-matched.

**Working, UNTESTED mechanistic predictions**:
- A **thermal time-use pathway**: species whose midday exposure is costly might alter time-of-day use as core-hour heat conditions change, conditional on independently measured detector/sampling effort.
- A **moisture/resource location-use pathway**: changes in water and subsequent vegetation/forage might alter where organisms spend time, potentially affecting camera photo-site weights separately from within-site diel allocation.

The 21-site data only measure temperature and soil moisture, not vegetation productivity or animal time/place in those regions. The earlier Serengeti source provides vegetation NDVI and source CAMERA PHOTO data in **one other distinct observational system and earlier years**; combining the two observational strands does NOT create paired across-region animal effects or prove heat versus forage mechanisms.

**Important limits**: ERA5 is atmospheric/land reanalysis, not independent physical field measurements; original time zones are local-daily averages and may not capture animal microclimate; the Land-mask geography is low-res; the experiment samples arbitrary equinox snapshot days that can reflect short-term weather, not multiweek seasonal states; soil moisture at 0–7cm is not root-zone plant-available water or forage biomass; and some model values can be physically invalid. Annual cycles at the same site are dependent, as are sites within broad climate systems. There are **no animal detections, observed movement or station camera-hour calibration in the 21-site grid.**

### Manuscript use and stopping rule

Use this pilot as a *supplementary cross-region physical environment result* and to define the future explanatory contrast **Δenvironment = (ΔT, Δsoil-water)**, not as 21 corroborating animal sites or a primary independent demonstration of behavioral universalism. An ecology paper that claims independent animal response transfer still needs multiple truly sampled regions with independently verified sensor or camera operation, same-individual/site rising-and-falling dates, and an untouched external region. Keep all original NDVI/camera/GPS results and source-HOLDs immutable and PR #267 DRAFT.
