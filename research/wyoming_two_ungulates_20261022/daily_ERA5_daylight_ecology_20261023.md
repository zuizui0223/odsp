# Original Wyoming mule deer and bighorn: daily climate-conditioned diel displacement

**Source-replayed ecological analysis, 2026-10-23.** This report is about an **observational animal/ecological relationship**, not GPS methodological model performance.

## Observational discovery

The original [Movebank Wyoming 2-species archive 10.5441/001/1.703](https://doi.org/10.5441/001/1.703) source MD5 `bd1c02734b6de3ddc9207fc1251edd66` was verified, and the **two previously frozen original source night−day GPS step-speed contrasts and astronomical daylight slopes were reproduced exactly BEFORE any ERA5 climate lookup**. The original source metadata declares CC BY-NC 4.0.

The fixed monthly climate-adjusted route was previously **source-INELIGIBLE** for both species because no individual-year provided six complete observed months; this was preserved. The distinct, subsequently registered **day-level ecological route** uses original accepted GPS observation dates (10 or more per individual-calendar-year, at least 3 qualified daytime and 3 nighttime original 30–120-min GPS steps per date) and a regionally modelled 1°-grid ERA5 **daily Tmax** together with prior **30-day precipitation minus reference FAO ET0** (climate water-balance proxy). It does not interpolate failed dates.

**All six GPS-observed grid cells were covered by source ERA5, with zero weather-source holds;** mule deer 17,402 individual-days and bighorn 7,675 individual-days were fully climate-matched. The unchanged initial unadjusted daylight slopes and new temperature/water-adjusted daylight slopes are:

| Source taxon | Original / day-level daylight slope (per daylight hour) | Joint daytime Tmax + 30d P−ET0-adjusted daylight slope | 95% **individual** bootstrap interval | Slope-qualified animals |
| --- | ---: | ---: | --- | ---: |
| *Odocoileus hemionus* (mule deer) | **+0.005538** | **+0.004238** | **[+0.002854, +0.005660]** | **117** |
| *Ovis canadensis* (bighorn sheep) | +0.000217 | −0.000516 | [−0.006482, +0.009909] | 41 |

The response is **night-minus-day** log(1+median GPS step km/h); source daylight is modeled astronomical *sunlit duration*, not individual light perception. An independently positive **mule deer daylight association remains after adjustment for two coarse hydrothermal indicators**. Bighorn's similar association is not resolved in these source animals. All 117 individual mule deer adjusted estimates are grouped at the animal level; bootstrapping the thousands of within-animal dates as independent is prohibited.

### Does a simple temperature or water mechanism explain the slope?

Source mule deer partial **Tmax** slope conditional on daylight and water = **+0.000548** per °C, individual bootstrap **[+0.000177,+0.000896]** (118 animals). Source mule deer prior-30-day climatic P−ET0 slope conditional on daylight and Tmax = **+0.006877 per 100 mm**, interval **[−0.002621,+0.016134]** (94 animals). Neither is a controlled treatment or direct plant water. The daylight coefficient decreases from +0.005538 to +0.004238 under adjustment, so temperature and water may correlate with the seasonality, but **the original positive association does not disappear under this model**.

**Crucial boundary:** All weather values come from coarse ERA5 source GPS-observed 1° grid centers, not on-animal thermometers, and water balance is a derived rain-minus-reference-evapotranspiration *climatic* proxy, not measured soil moisture, drinking-water, foliage or grazing biomass. Light duration, temperature and animal breeding/foraging state all covary seasonally, and this observational association is not evidence for direct sunlight regulation, thermal physiology, or a global evolutionary species effect. Within-individual regression removes static between-animal differences but not time-varying confounding.

### Separation from earlier hypotheses

The *original Utah* strict rising-versus-falling, same-photoperiod within-individual route qualified **no** individual-years; that is SOURCE UNAVAILABLE, not evidence of no biology. The source daytime/daylight result here is a **different estimand**. The old Wyoming monthly-adjusted route remains unidentifiable, not retroactively relabeled.

## Public data and reproducibility

- Original Wyoming population source study: [DOI 10.5441/001/1.703](https://doi.org/10.5441/001/1.703), original provider-MD5 contract [source](../MOVEBANK_WYOMING_TWO_UNGULATES_SOURCE_V0_20261022.json).
- Original **GPS day/night and sunlight source results** [39723531890](https://github.com/zuizui0223/odsp/actions/runs/39723531890).
- Unavailable month-level ERA5 route [39877584634](https://github.com/zuizui0223/odsp/actions/runs/39877584634).
- **Successful original date-level GPS + Tmax/30d water** [39878174016](https://github.com/zuizui0223/odsp/actions/runs/39878174016), 6 known-truth tests and 0 source grids held.
- Locked [day-level contract](../WYOMING_DAILY_ERA5_DAYLIGHT_V1_20261023.json), source pipeline [script](../../scripts/movebank_wyoming_daily_climate_20261023.py) and [synthetic tests](../../tests/test_movebank_wyoming_daily_climate_20261023.py).
- [Complete machine-readable cohort × endpoint CSV](wyoming_individual_era5_daylight_associations.csv). All source-limited results and negative/undefined effects retained; no original animal GPS IDs, coordinates or source event timestamps published.
