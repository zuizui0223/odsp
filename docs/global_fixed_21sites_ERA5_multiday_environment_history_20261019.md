# Same daylength, different hydrothermal histories: 1-, 15- and 30-day sensitivity at 21 fixed sites

**2026-10-19 | Original source-replayed exploratory ERA5 evidence; not an animal response, global land-area proportion, preregistered external experiment or causal ecological mechanism.**

## Ecological question

The first fixed-grid experiment found opposite changes in daily mean air temperature and shallow 0–7cm soil moisture between dates of nearly identical sunlit duration in 29/62 original ERA5-supported site-years. A biologically more important question is whether these are **environmental-history differences**, rather than changes on a weather-specific single day. We therefore retained the exact **21 original land-grid points**, all **63 original 2018–2020 year/endpoint date pairs** and the original one-day response and compared trailing **15-day** and **30-day** histories *including the matched endpoint*. The source dates were never re-paired to improve signs. This is a **post-first-result timescale sensitivity**, and its analysis contract was committed before reading the newly acquired daily histories; it is not independent confirmation of the original one-day effects.

## Fully original ERA5 source and quality conditions

- Source: Open-Meteo Historical Weather API with explicit `models=era5` and location-specific `timezone=auto`. Variables: daily mean and maximum 2m air temperature (°C), daily surface 0–7cm volumetric soil water (m³/m³), and daily accumulated precipitation (mm). All are reanalysis variables, NOT physically independent gauges, forage estimates or observed animal activity.
- Same six original north and six original south endpoint-date groups, yielding **12 official API 30-day daily responses** (six source points in the south, 15 in the north). Exactly 30 consecutive location-local dates and 30 original values for each variable are retained per source point; the shorter 15-day endpoint-including window is obtained only as the last 15 days of that same source.
- Original 2018–2021 raw source data and complete original API response URLs: [South 30-day source](../research/solar_global_equinoctial_pilot_20261019/era5_southern_30day_six_original_batches_v0.json) and [North 30-day source](../research/solar_global_equinoctial_pilot_20261019/era5_northern_30day_six_original_batches_v0.json). Original one-day source bodies and fixed land/cycle roster also remain in that directory.
- The source endpoint day in each new 30-day array was checked to reproduce the original one-day first-source **Tmean, Tmax and soil-water values exactly**, with no original weather-result reclassification. The original first source panel had 62/63 admitted and 29 opposed. A new date/point/model mismatch is a global source HOLD, never an alternate matching attempt.
- Each window has its OWN acceptance: every day must have real finite values, `Tmax>=Tmean`, physically possible `0<=soil_moisture<=1`, precipitation>=0. Invalid soil values such as tiny negative model values are **not clipped to zero**. No interpolation/gap-fill, no substitute climate model, no sampling-frame shrink to more interesting sites. Shorter W=15 can remain source-valid if invalid source weather lies outside its 15-day span, but W=30 is then unavailable.
- **Important solar limit:** the original *endpoint* pair's modelled daylength differs by <0.8 minute, but daylength is NOT held equal throughout these preceding 15/30 days. This is a test of the **ecological state that accumulated before near-equal-photoperiod endpoints**, not a fully photoperiod-matched thirty-day intervention.

## Source-derived numerical results: substantial heterogeneous history remains

| Fixed environmental endpoint window | Source-valid site × original year-cycle | Temperature/soil-water seasonal contrasts with opposing signs | Fraction of valid source comparisons |
|---|---:|---:|---:|
| Original single day | **62/63** | **29** (18 warmer/drier; 11 cooler/wetter) | **46.8%** |
| Mean previous 15 days | **59/63** | **26** (20 warmer/drier; 6 cooler/wetter) | **44.1%** |
| Mean previous 30 days | **57/63** | **26** (21 warmer/drier; 5 cooler/wetter) | **45.6%** |

The 30-day source-supported pairs show **52 warmer** seasonal thermal-history differences among 57; the source-admitted mean falling-minus-rising previous-30-day temperature contrast is approximately **+10.21°C**. Source-trailing 30-day average surface-water differences vary by location and year; some original sites/years are warmer/drier while others are cooler/wetter, even though the original astronomical endpoint is nearly matched. The 30-day precipitation TOTAL seasonal contrast averaged **+49.53 mm** over the unweighted valid pairs, and **12/57** site-years showed opposite changes of accumulated precipitation and mean shallow soil water. Precipitation and soil water are both products of the same ERA5 land/atmosphere system and their divergence should NOT be interpreted as an independently identified water-balance physiology mechanism.

### Crucial non-obvious result: stable counts, changing site×year identities

The broad aggregate proportion of opposed hydrothermal directions is similar at 1 and 30 days. **That does not mean the same original places and years retain their classifications.** On the **57 site×year pairs with valid data at all 1-, 15- and 30-day scales**, exactly **26** show opposing temperature/water signs at the original single day and **26** at 30 days. However:

- **Eight** original one-day opposing observations are **not** opposing at the thirty-day scale.
- A **different eight** original one-day nonopposing observations become **opposing** at thirty days.
- Thus **16/57** site×year classifications change (approximately 28.1%), even though the overall count remains exactly the same.
- Only **16/57** have opposite-sign temperature/water contrasts at **all three** environmental history scales (1, 15 and 30 days). This is the stricter *time-scale-stable* supported subset, not proof of a causal environmental state.
- On complete three-cycle original source sites, the all-three-years-opposed count changes from **five** at one day to **four** with 15 days and **four** with 30 days, with different geographic membership. The original single-day Brazil/Zambia/Egypt/Argentina stable-opposition anecdotes therefore cannot all be carried into 30-day ecological-history claims. For Egypt two 30-day source pairs are unavailable due physically negative modeled water and must remain explicitly HOLD, not negative seasonal ecological results.
- Original Argentina's three one-day contrasts all opposed, but the antecedent-15/30-day results differ in sign by year: this is a **temporal-grain warning**. The locally averaged sign alone does not preserve every yearwise trajectory.

**What is supported:** near-equal astronomical-daylength endpoints can sit within distinct multiweek temperature and shallow-soil-water histories, including warm/dry and cool/wet trajectories. Their joint seasonal classification is partly **dependent on environmental observation timescale**, even with site and endpoint calendar matching frozen. The point is ecological state and phenology context; not a demonstrated individual animal response or broad land-mass prevalence.

## Reanalysis and manuscript limits

The original 72-point grid retained 21 sites by a crude land mask on a few latitude lines, spanning six geographic region labels. It is **not** a random or area-weighted survey of Earth's terrestrial climates. Repeated 2018–2020 years at each point and neighboring climate regions are not independent draws. Daily source ERA5 modeled soil water can produce tiny physically invalid values; the 15- and 30-day admitted samples differ from original one-day sample. Therefore raw differences in the total number of opposing pairs at different time scales should NOT be read as temporal persistence without the **57-common-source** comparison above.

In addition, the 30-day "history" changes the mean calendar phase of the considered days around the endpoint and may have different average photoperiod in the two histories. It is not a controlled experiment isolating solar forcing, thermal cause, moisture cause or physiology. No independent animal observations or source camera ON-hour/detection-`q` were linked for these 21 locations. In particular, previous Serengeti NDVI/photos were taken in a different region/years; do not label them a new matched global animal dataset.

The scientific implication for the prospective database-first animal study is that environmental predictors should be **state vectors over an explicitly named time horizon**, not a universal `season=hot` binary or a selectively chosen instant. Use a single up-front environmental interval and the alternative temporal window as a prespecified sensitivity in a future independent individual/population cohort; do not select a window that gives the best animal effect after examining response values.

## Reproducibility and immutable prior results

- Frozen post-first-result temporal-history contract: [15/30d v0](../research/solar_global_equinoctial_pilot_20261019/era5_15_30_day_history_contract_v0.json).
- Original first 1-day source-checked [Actions 39201993065](https://github.com/zuizui0223/odsp/actions/runs/39201993065); original 21 fixed geography and 12 short-response batches preserved untouched.
- Source replay script `scripts/analyze_fixed_21site_era5_15_30day_history_v0.py`, seven dedicated known-truth tests and dedicated [15/30day source Actions](https://github.com/zuizui0223/odsp/actions/runs/39210495523). If the latter run remains queued, **do not describe it as passed**; numerical findings above are based on separately read and cross-checked immutable original daily source responses.
- Aggregated output provides every one of the 63×2 original site/year/window statuses, physical invalid reason, and complete same-support comparison. No source rows and prior Serengeti, RI or duck GPS terminal outputs were overwritten.
- PR #267 remains DRAFT; a true comparative ecology study still needs original animal dates/site or marked-individual movement measurements, verified sampling effort, and independent population-level replication rather than claiming that climate trajectory contrasts alone demonstrate universal animal timing change.
