# Calendar-conditioned public-data ecology: four Utah ungulates

**2026-10-22 | Source-backed exploratory ecological synthesis | PR #268 Draft.**

## Biological finding and what changed

This supplement evaluates an ecological question, rather than a model forecast: **does the taxon contrast in observed day/night movement rate vary with hydrothermal conditions, after considering the annual solar calendar?** The original four-ungulate GPS source (Movebank DOI [10.5441/001/1.711](https://doi.org/10.5441/001/1.711), provider MD5 `08200c9dbdf7989fb5a35467213b7e5a`) and original 1° geographic-grid × year-month observation eligibility are unchanged.

The completely executed [GitHub Actions 39722195796](https://github.com/zuizui0223/odsp/actions/runs/39722195796) **reproduced all six previous same-place/month GPS species effects and all six previous ERA5 marginal temperature and climatic water-balance slopes**, then computed the new daylight-conditional and joint-source environmental associations from original MD5-verified movement records. All 19 ERA5 geographic grids were available (no source HOLD). Synthetic known-truth solar/confounding tests passed.

### Strongest exploratory association: mule deer versus bighorn sheep

`q` denotes source individual/day aggregation of **log(1+median NIGHT GPS km/h) − log(1+median DAY GPS km/h)**; the species difference is *mule deer minus bighorn*. A positive q difference means *more relative nightward observed displacement* in mule deer; it is **not** the fraction of the 24h day when the species is actually active.

| Comparison | Equal-geographic-block mean slope | Conditional bootstrap 95% interval | Source geographic blocks |
| --- | ---: | --- | ---: |
| **ERA5 mean air T**, controlling just astronomical daylight | +0.004103 / °C | **+0.002854 to +0.005498** | 7 |
| ERA5 mean air T, controlling daylight **and P−ET0** | **+0.000954 / °C** | −0.000878 to +0.002750 | 6 |
| **Monthly climatic P−ET0**, controlling just daylight | **−0.019072 / 100 mm** | −0.024972 to −0.013775 | 7 |
| **Monthly climatic P−ET0**, controlling daylight **and ERA5 mean T** | **−0.016754 / 100 mm** | **−0.024743 to −0.007943** | 6 |

All **six** geographic blocks with estimable joint-water slope were **negative**. The earlier positive marginal temperature slope **attenuated toward zero** in the joint model and had an interval spanning zero. Thus a *simple* claim that the source diel contrast is explained by warmth alone is not supported by this specific joint model. The remaining water-related association is exploratory: the unit is **monthly precipitation minus FAO reference evapotranspiration (P−ET0)**, **not real soil moisture, waterhole access, vegetation phenology, or plant quality**.

The astronomical daylight covariate is the modeled length of day on the **15th of each calendar month** at the coarse grid-center latitude; it is not individual animal thermoregulatory or light exposure.

### Independent-calendar diagnostic limits the strength of the claim

A stricter observational contrast matched the **same calendar month within the same geographic grid across distinct sampled years** (for example, 2019 vs 2020), largely holding annual solar geometry fixed. For mule deer and bighorn there were **32 interannual same-month source contrasts**. The equal-geographic-block water slope across six estimable blocks was **−0.031625 / 100 mm**, but its bootstrap interval **−0.08355 to +0.000536 includes zero**. Thus the prior joint water association is **not an independently confirmed driver**.

For other taxon comparisons the new partial association is often unidentified because only **1–4 geographic blocks** meet fixed joint-variation conditions. Do not report these small-block point estimates as broadly supported, and **do not infer no climate effect** from inadequate support. In wapiti–mule deer, the joint model retains 7 blocks but the temperature, water and daylight confidence intervals overlap zero. This is consistent with their small within-source shared-place/month speed contrast.

The complete **six-source-pair registry** including negative/null/undefined association results, source per-pair block counts, marginal predictors, solar/daylength-only and joint slopes, and same-calendar-month interannual check is archived in [`era5_calendar_adjusted_associations.csv`](era5_calendar_adjusted_associations.csv). Blank interval fields mean **insufficient identified blocks**, not an observed zero.

## Ecology interpretation

**Supported at the level of this original public data source:** species/cohort nighttime-versus-daytime GPS displacement differences vary among ungulates under some common geographic and seasonal observation opportunities; pronghorn shows a particularly stronger daylight displacement component than mule deer. With monthly coarse reanalysis weather, the mule deer–bighorn contrast has a detectable **observational association** with monthly P−ET0 after adjusting for modelled astronomical daylength and ERA5 mean temperature, whereas a temperature-only explanation loses independent support in this joint screen.

**Not supported:** water causes a behavioral switch, grass availability mediates the pattern, specific predator-prey partitioning, heat avoidance, circadian daylength memory, cross-biome universality, or genuine animal activity budgets. In a two-year observational tracking source, calendar, habitat, seasonal food, reproduction, individual recruitment and climate remain dependent. The geographic bootstrap describes seven or fewer independent-ish *coarse geographic blocks* for the focal partial analyses, not an ecosystem population sample.

The original, distinct **spring versus autumn same-daylength** Utah branch was source-UNAVAILABLE (0 qualified individual-years for all four species) and remains unchanged.

## Source and workflow provenance

- Full public discovery frame: [Movebank 437-package registry](../seasonal_database_catalog/README.md).
- Observed Utah 4-taxon source and diel evidence: [39216810610](https://github.com/zuizui0223/odsp/actions/runs/39216810610).
- Six original location/month species comparisons and night/day components: [39218494366](https://github.com/zuizui0223/odsp/actions/runs/39218494366).
- Original 19-grid ERA5 marginal associations: [39220101404](https://github.com/zuizui0223/odsp/actions/runs/39220101404).
- Calendar-adjusted 6-pair source-replay: [39722195796](https://github.com/zuizui0223/odsp/actions/runs/39722195796), original result artifact `utah-original-ungulates-ecology-calendar-conditioned-v0-20261022`.
- Reproducible [fixed analysis contract](../MOVEBANK_UTAH_CALENDAR_CONDITIONED_V0_20261022.json), [script](../../scripts/movebank_utah_calendar_condition_20261022.py) and [six known-truth tests](../../tests/test_movebank_utah_calendar_condition_20261022.py).

Only taxon-pair aggregates are retained here, never original location tracks or individual identifiers.
