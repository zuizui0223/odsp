# Satellite-measured greenness differs under the same astronomical daylength: original MODIS 2010–2013

**2026-10-15 · ODSP PR #267 · New independent remote-sensing RESULT, NOT yet a camera-specific animal response.**

## Why this matters ecologically

Sun geometry is an externally calculable annual forcing. Ecological resources are not locked to the same instantaneous annual photoperiod phase. If two dates have approximately equal astronomical daylength on opposite sides of the December solstice, their temperature, 30-day rainfall history and vegetation greenness may differ. This is a potentially important basis for seasonal asymmetries in a savanna ecosystem, but not evidence that an animal remembers photoperiod, responds to NDVI, migrates, or changes true circadian behavior.

## Authentic independent observation source, not invented NDVI

NASA MODIS/Terra **MOD13Q1 Collection 6.1**, 250-m 16-day NDVI, indexed via Microsoft Planetary Computer public STAC `modis-13Q1-061` with a documented anonymous **container-scoped** temporary SAS token. Product DOI: https://doi.org/10.5067/MODIS/MOD13Q1.061. Raster assets read remotely as cloud-optimized GeoTIFF (COG) windows with a paired `250m_16_days_pixel_reliability` quality band.

One **previously fixed regional representative location** 2.5°S, 34.75°E (chosen for the earlier ERA5 independent temperature/rainfall comparison) was used, averaging only a **3×3 adjacent pixel window**. This is an area under ~1 km across, **NOT** 186 source camera locations, the whole Serengeti, or directly sampled grazing resources. Quality is strict: original NDVI raw −2000..10000 scaled by 0.0001, QA code **exactly zero** (good), at least 6 of 9 reliable pixels per composite; cloud/marginal data not interpolated or gap-filled.

The [first actual original satellite SOURCE probe CI 38740896537](https://github.com/zuizui0223/odsp/actions/runs/38740896537) measured original dated composite **2012-01-17 through 2012-02-01 NDVI = 0.5484, 9/9 QA-good**, and that exact source pixel/QA result was REQUIRED to reproduce before expanding the full time series.

The first full-Terra-series attempt [CI 38741760524](https://github.com/zuizui0223/odsp/actions/runs/38741760524) found **83** real MOD13Q1 scenes but 78 of 83 repeated per-asset retrievals failed with HTTPError after the first five requests; only 4 sources qualified and the original v0 was archived as **insufficient and NOT an NDVI season result**. A separately frozen source-ACCESS v1 contract changed ONLY from repeated asset signing to the provider's officially documented anonymous **container-wide token**, without changing the 83 source items, photoperiod mirror calendar, NDVI scale, QA threshold, site or computation.

[**Verified revised original source CI 38742381644 SUCCESS**](https://github.com/zuizui0223/odsp/actions/runs/38742381644) replayed the initial exact 2012 0.5484/9-good pixel result, accessed **all 83 original Terra composite scenes**, and accepted **75** qualified scenes (8 source quality holds). It archived the complete ordered 83 items, dates, source QA and NDVI values as `serengeti-mod13q1-public-container-83scene-v1`, original full JSON SHA256 `e0e3c57de8d6a3ab9996412886e9733ea572cf9989f88a68b5c3ac5fb5557f11`. Tests ran before new scene outcome retrieval. Original v0 failure receipt preserved unchanged.

## Frozen equal-photoperiod environmental design

Use the already frozen 2010, 2011 and 2012 December-solstice symmetric **±k days, k=7..180**: 174 per year, **522** total paired calendar dates. Pair each local calendar day with only the **most recently fully completed** Terra 16-day source composite ending on or before that day, no future imagery, at most 20 days old. If its last composite is cloudy or marginal, return missing instead of reaching further back. Summarize falling-minus-rising paired NDVI only if >=60% of original 174 mirror pairs remain with both good images in a given year. Do not re-pair dates to maximize contrast; no NDVI/animal event values were read before this date/quality rule froze.

## New remote-sensing result

| December-solstice year-cycle | Complete good NDVI day pairs | Mean falling−rising NDVI | Median | Fraction of good NDVI pairs with positive difference |
|---|---:|---:|---:|---:|
| 2010 | 174/174 (100%) | **+0.1450** | +0.1726 | 90.23% |
| 2011 | 119/174 (68.39%) | **+0.2607** | +0.3109 | 100% |
| 2012 | 142/174 (81.61%) | **+0.1685** | +0.1461 | 96.48% |

Total **435/522** calendar date pairs have both satellite quality-eligible readings. Every cycle exceeded the pre-declared 60% source-quality floor. The prevalence and direction of greener falling-phase values is an observed property of this quality-filtered *single representative vegetation patch*, not a probability about all Serengeti sites. Repeated calendar dates map to the same 16-day composite: **435 is NOT the number of independent original NDVI samples or animal populations**.

Together with earlier externally sourced **regional ERA5** results, which showed falling-minus-rising 30-day rainfall differences of **+60.30/+44.55/+70.44 mm** in 2010/2011/2012, this supports a descriptive interpretation that astronomical daylength matching does not align regional hydroclimate or vegetation greenness. The rainfall observations are meteorological model outputs, not direct soil/forage measurements; the MOD13Q1 NDVI represents green vegetation reflectance including woody canopy, not available nutritional biomass.

## What this result DOES NOT prove

- An animal at a camera actually experienced a higher NDVI. Its camera site might be more/less green than this fixed sample patch, and vegetation can reduce a camera's detection probability.
- Wildebeest or zebra traveled to greener camera sites. This would require **camera-specific original pixel NDVI at matched source dates**, station/season effort and independent evidence of movement or occupancy.
- The original recorded PHOTO nighttime reweighting component `B` measures migration. It remains an algebraic difference in which camera stations contribute photo records, potentially due to species spatial distribution, unknown detector `q`, unobserved device operation hours, camera replacement, or real behavior.
- Strong or universal species' causal response to photoperiod, rainfall, temperature or NDVI. Three climatic year-cycles are temporally dependent and all part of one African landscape.
- A nominal inferential p-value from 435 pairs. All 83 source MODIS scenes, 522 date pairs, QA missingness, all cycle signs and source data fidelity are explicitly preserved.

### Next useful ecological test

Use the exact original **186 public-source physical camera locations internally**, quality-screen MODIS pixels at each actual source camera position for the same frozen original 24,290 site/date pairs, and test if each camera's change in observed photo share/within-camera nighttime PHOTO fraction is associated with its independently observed local vegetation change. Preserve all five pre-named large-mammal taxa and all cycles, hard-stop if the pixel/camera source cannot be verified, never export exact protected camera coordinates, and never interpret correlation as causal movement without ON-hour/q reference data. The linked-camera route is separately frozen, not a revision to this original environmental result.

## Full reproducibility

- Original first accepted source item [CI 38740896537](https://github.com/zuizui0223/odsp/actions/runs/38740896537).
- First all-series source HOLD [CI 38741760524](https://github.com/zuizui0223/odsp/actions/runs/38741760524).
- Valid historical-series source retry [CI 38742381644](https://github.com/zuizui0223/odsp/actions/runs/38742381644).
- `research/SERENGETI_REGIONAL_MOD13Q1_NDVI_2010_2013_SEASON_MIRROR_V0_CONTRACT.json`, `research/SERENGETI_MOD13Q1_PUBLIC_TOKEN_V1_SOURCE_ACCESS_CONTRACT.json`, source scripts/tests/workflows on ODSP #267.

All original RI, N2 Serengeti, Uljin and prior exploratory/photo outcomes stay frozen. **PR #267 remains DRAFT**.
