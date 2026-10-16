# Equal-photoperiod weather is not equal ecological season: first external ERA5 result

**2026-10-15 | PR #267 | One public Serengeti-area coarse regional grid; NO CAMERA/ANIMAL RESULTS DERIVED FROM WEATHER.**

## Why this is a relevant biological test

Previous source-verified Snapshot Serengeti photo-time comparisons found different *recorded event* seasonal branch ratios among mammals at nearly matched astronomical daylength. A plausible ecological narrative was daytime thermal avoidance. We test a **necessary, but not sufficient, environmental prediction** for a simplistic “falling photoperiod = hotter” interpretation: is the falling branch actually consistently hotter than the rising branch at the same approximate astronomical daylength?

This test cannot establish physiological regulation, vegetation-driven behavior or true animal activity. It is an independently measured **regional climate context** with an observational calendar contrast.

## Source and preregistered comparison

Original published data provider: [Open-Meteo Historical Weather API, ERA5 model](https://open-meteo.com/en/docs/historical-weather-api); underlying ECMWF ERA5 atmospheric reanalysis. Coarse **public regional study representative** coordinate **2.50°S, 34.75°E**; chosen BEFORE inspecting the full weather result; it is not the location of any camera and no camera GPS was accessed. Returned grid uses Africa/Dar_es_Salaam UTC+03:00 at model elevation 1,555 m.

- Original daily data range: **2010-01-01 through 2013-06-30**; full **1,277 daily rows**.
- Sixteen-source-data handling: actual variables frozen were *mean 2-m air temperature, maximum 2-m air temperature, daily precipitation, daily shortwave radiation*. Four original variable series returned without missing days.
- Astronomical natural-pair surrogate: December 21 ± k days, k=7,...,180 for each of original cycle years **2010, 2011, 2012**. **174 mirror-date pairs per year**, **522 across 3 annual cycles**. These are NOT the original camera-specific 24,290 accepted site×day-pairs and NOT 522 independent climates.
- Wetness history = accumulated daily rainfall from the target date plus the preceding **29 days**, not rainfall only on the photograph date.
- All four environmental response signs, all pairs and all cycles retained. No selection of unusually hot/cold dates.
- Frozen contract: `research/SERENGETI_ERA5_EQUAL_PHOTOPERIOD_ENVIRONMENT_V0_CONTRACT.json`; source reader/test `scripts/run_serengeti_era5_environment_v0.py`, `tests/test_serengeti_era5_environment_v0.py`.
- **[Independent GitHub Actions CI 38699783443 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/38699783443)**, all five negative/known-truth tests PASS. Exact source DAILY DATA arrays SHA-256: `aaa93eec1ac0fab3315bfc712020970746d47cd1d407b8a7778243b2f627bee7`; source-transport hash separate.

## Real independent environmental contrasts

Every reported value is **falling-branch minus rising-branch** *regional reanalysis weather at symmetric dates* (NOT animal behavior).

| December-solstice cycle | Date pairs | Daily mean air temperature mean Δ (°C) | Daily max air temperature mean Δ (°C) | Trailing 30d rainfall mean Δ (mm) | Shortwave radiation mean Δ (MJ/m²) |
|---|---:|---:|---:|---:|---:|
| 2010 | 174 | +0.232 | +0.398 | +60.299 | +0.904 |
| 2011 | 174 | −0.417 | −0.763 | +44.553 | +1.541 |
| 2012 | 174 | −0.171 | −0.491 | +70.444 | −0.159 |
| All original 3 cycles (descriptive, not n=522 IID) | 522 | **−0.119** | **−0.285** | **+58.432** | +0.762 |

The overall **daily maximum temperature** δ had 10th–90th percentiles **[−4.08, +3.10]°C**, with only **46.74%** of mirror pairs having δ>0. Annual mean δ_max changed sign: warmer falling branch in 2010 but *cooler* in both 2011 and 2012. Similarly the 30d precipitation contrast is not uniformly positive within all pairs (75.1% positive, 24.9% negative); there is substantial seasonal rainfall variation.

### Appropriate biological interpretation

A **universal hotter-falling-branch explanation is inconsistent with the observed regional meteorological context**. The observed pooled source photo-time changes cannot all be described as a mechanical consequence of the season always being hotter after December 21. Independent annual cycles and same-day environmental matching are necessary before any mechanistic claim.

Rainfall-history shifts can be much larger and offer a plausible alternative hypothesis involving vegetation greenness, resource access, herd migration and animal exposure—but the regional precipitation index is **not NDVI/food biomass or proof that rainfall drove behavior**. The original Snapshot Serengeti publication emphasizes strongly seasonal large-herbivore migration following rainfall; this biological context supports including resources and composition as competing explanations.

### Strict ecological inference ceiling

1. These pairs are astronomically approximated **regional calendar mirror dates**, not fully site-photo-admitted matched days. A follow-on **separate exploratory source** analysis aligns exact original eligible site dates, keeping the original source first-locked result and annual cycles, without reselecting responsive taxa; do not substitute its result unless independently verified.
2. Just **one ERA5 grid** and **three temporally dependent climate years**. Do not treat 522 mirror pairs, 225 physical cameras or 186 original observation stations as 522/225/186 independent landscapes.
3. The weather is modeled temperature/radiation and rainfall, not microclimate on the animal skin, vegetation productivity, individual heat stress or telemetry. Cannot fit a credible independent-environment generalizing response regression.
4. Underlying photos lack an independent station×solar-hour camera ON/OFF history and time/season-specific detection q. Previously reported camera **recorded-time odds** cannot be promoted to latent mammalian activity changes or adaptive thermal/night refuge.
5. No inferential p-values, causal mediation, independent ecological replication, pre-declared supported global law or new species response is claimed.

## Reproducibility

- [Exact original first-weather workflow](https://github.com/zuizui0223/odsp/actions/runs/38699783443).
- The metadata+numbers are reproduced by the source-pinned script in PR #267; archived `serengeti-regional-era5-seasonal-environment-v0` JSON has source daily digest and all original-year statistics.
- Earlier Rhode Island, Serengeti N2 and Uljin source HOLD remain unchanged.
