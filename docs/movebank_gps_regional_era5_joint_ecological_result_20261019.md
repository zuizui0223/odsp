# Same-daylength seasonal timing and independent regional hydrothermal context

**ODSP ecological programme, 2026-10-19. Exploratory public-database integration; NOT a thermoregulation or water-balance causal test.**

## Biological question

When animals face similar daylength on the increasing and decreasing branches of an annual solar cycle, do their *observed* night-versus-day displacement rates shift in one common direction? If declining-daylength dates are warmer in the source region, does that automatically imply a shift toward nighttime movement?

This is an ecology-centered comparison, **not a machine-learning prediction exercise or a detector/camera improvement exercise**.

## Sources and separation from earlier outcomes

The three independent publicly archived Movebank movement cohorts were selected from a dated **437-package** registry census and pinned by provider ORIGINAL bitstream UUID + MD5. Their original three-source movement analysis was frozen independently before opening movement magnitudes:

- Wapiti / elk, `Cervus elaphus`, Banff / Ya Ha Tinda region, [Movebank source DOI](https://doi.org/10.5441/001/1.5g4h5t6c).
- Free-ranging wild pig, `Sus scrofa`, southern Florida, [Movebank source DOI](https://doi.org/10.5441/001/1.719).
- American black bear, `Ursus americanus`, Connecticut, [Movebank source DOI](https://doi.org/10.5441/001/1.706).

The ORIGINAL-CSV movement comparison used 30–120-minute consecutive GPS intervals not crossing mean-solar day/night boundaries, great-circle minimum step distance per hour, date pairs at <=5-min photoperiod mismatch and >=30-d separation, at least three qualified steps per daypart on both dates, a predeclared sample-balance rule, and >=10 matched day pairs per individual-year. Its endpoint is falling-minus-rising [log(1 + median night GPS speed km/h) - log(1 + median day GPS speed km/h)], averaged within animal before source group results. This is **observed GPS displacement**, not continuous activity or energy expenditure. It is not a log percentage change.

The **regional weather connection was designed after the first numerical GPS results were observed**, and is therefore **post-outcome exploratory**. A separate [registered weather-join contract](../research/MOVEBANK_REGIONAL_ERA5_MOVEMENT_LINK_V0_20261019.json) fixes the three public coarse regional climate reference points, provider, original movement-effect reproduction requirement and climate variables. Weather values were then retrieved from historical Open-Meteo ERA5 using fixed standard local calendar dates; prior 30-day climate water balance proxy is summed precipitation minus reference FAO evapotranspiration (P - ET0). It is **not measured soil water**.

The [new workflow run 39203998039](https://github.com/zuizui0223/odsp/actions/runs/39203998039) **PASSED**. Its nine source-independent arithmetic/timezone tests and source MD5 controls succeeded, and before returning the climate summary it **reproduced exactly the previous three frozen group movement means**. All three regional ERA5 source queries succeeded. Original weather retrieval URLs, source response hashes, number of days and provider grid coordinates are retained in its grouped JSON artifact. There were **zero climate-date matching failures** in this source comparison.

## Ecological results

All contrasts below are **decreasing-daylength minus increasing-daylength**, at previously matched GPS-sampling dates. Climate values are population-region summaries giving each admitted individual equal influence (and their years equal weight).

| Source population | Qualified unique GPS animals | Matched within-animal calendar pairs | Δ regional mean air T (°C) | Δ preceding-30d regional P-ET0 (mm) | Δ relative night-vs-day log1p GPS speed | Source-individual bootstrap 95% interval for GPS contrast |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Banff / wapiti | **12** | **436** | **+9.751** | +5.577 | **+0.04500** | +0.02409 to +0.06187 |
| Southern Florida / wild pig | **5** | **321** | **+1.794** | +112.014 | -0.00098 | -0.04009 to +0.03354 |
| Connecticut / black bear | **20** | **962** | **+9.865** | -66.457 | **-0.07717** | -0.08877 to -0.06591 |

All **12/12**, **5/5**, and **20/20** admitted individuals were paired across dates for which the *coarse study-region* temperature was higher on the decreasing-daylength side. The reported thermal means are based on weather at named study-region reference grids, **not reconstructed fixes' microclimates**. An identical +10°C regional seasonal context is not a controlled experiment: source region, species, year, habitat, physiological state, life history and sampling design remain confounded.

The components of the original GPS result are ecologically revealing:

| Cohort | Falling-rising **day** log1p speed | Falling-rising **night** log1p speed | Source animals with relative-night positive/negative |
| --- | ---: | ---: | --- |
| Wapiti | **-0.02411** | **+0.02089** | 11 positive / 1 negative |
| Wild pig | +0.00170 | +0.00072 | 3 positive / 2 negative |
| Black bear | **+0.06685** | **-0.01032** | 0 positive / 20 negative |

Thus in this *sampled* wapiti population the relative nighttime shift combines lower daytime and greater nighttime displacement; the sampled Connecticut black bears show the reverse, dominated by higher daytime displacement. Wild pig has a near-zero contrast on this scale.

**Supported biological observation:** at nearly equivalent astronomical daylength, stronger temperature on the decreasing-daylength side **does not uniquely determine the direction of within-animal observed diel movement redistribution** in these three independent source populations.

**Not yet supported:** that temperature does not matter for the animals; that water balance directly mediates their activity; that wapiti are universally more nocturnal on one branch or bears generally become diurnal; that different feeding guilds explain the relationship. Three sources give one population per taxon, not a population-replicated comparative evolutionary trait analysis. The temperature sign itself is expected to vary with geography and pairing date, and no microclimate is measured.

## Why this is a research finding rather than a prediction benchmark

The result is a physically matched, independently sourced contrast showing **contrasting signs** in actual animal displacement at constant nominal daylight geometry, and the components that generate each contrast. It falsifies only an overly strong *universal observed pattern* (that a warmer declining daylength necessarily co-occurs with relative nightward displacement) in these source cohorts. It does not falsify a conditional thermoregulatory process.

In the wider [Movebank eight-source extension](https://github.com/zuizui0223/odsp/actions/runs/39203695999), Wyoming mule deer (`Odocoileus hemionus`, 118 admitted animals) showed a positive relative-night contrast **+0.03115** (103 positive individuals), while Virginia white-tailed deer (`Odocoileus virginianus`, 33) was close to zero (**-0.00319**); Alberta wolves (`Canis lupus`, 9) were mixed (**+0.02841**, source-bootstrap interval spanning zero). Four additional original files had **provider checksum mismatches** and were kept SOURCE HOLD, while one moose archive had inadequate date-pair support. These sites **have not received matched-day regional ERA5 analyses**. The first three-source climate table must not be projected onto them.

## Main ecological next test (not performed here)

Across a larger set of independent populations and tracked individuals, use weather and phenology actually encountered during their sampling dates rather than assigning one coarse climate grid per taxon. Estimate within-population associations separately from between-population differences, while accounting for observed fix schedules, sex/age, and reproductive or migratory state where supplied. Compare whether *temperature change*, *water/vegetation state* and *movement strategy* correspond to day-versus-night reallocation; report variable and null relationships rather than requiring every taxon to exhibit the same sign.

This is a hypothesis-led **public-database comparative ecological analysis**. Transfer/prediction to novel regions may later be useful but is **not** the scientific endpoint.

## Provenance and scope

- Original 437-package metadata registry: [source inventory](../research/seasonal_database_catalog/README.md).
- Original 437 packages / 1,677 native bitstream metadata and 3-source GPS file QA: [GitHub Actions 39202214632](https://github.com/zuizui0223/odsp/actions/runs/39202214632).
- Frozen original animal speed results: [GitHub Actions 39202860827](https://github.com/zuizui0223/odsp/actions/runs/39202860827).
- Region-level ERA5 weather linked to *same observed animal dates*: [GitHub Actions 39203998039](https://github.com/zuizui0223/odsp/actions/runs/39203998039).
- Existing [Solar-season ecology programme](database_seasonal_ecology_programme_20261019.md) and [field-source Serengeti draft](../manuscript/SOLAR_SEASONAL_HYSTERESIS_ECOLOGY_PAPER_v0.md).

This report is descriptive and observational, not a preregistered independent confirmation, species-wide significance test, or globally representative sample. The camera and GPS routes are not numerically pooled. No sensitive source trajectories or animal identifiers are re-exported.
