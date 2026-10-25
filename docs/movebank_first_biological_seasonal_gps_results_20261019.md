# First biological result from ODSP's own public-source seasonal GPS database

**2026-10-19; exploratory.** Provider-authenticated original Movebank animal-tracking CSVs. Not a reanalysis of previously published effect tables.

Primary source: [Action 39202860827](https://github.com/zuizui0223/odsp/actions/runs/39202860827), [frozen step-and-date contrast](../research/MOVEBANK_SOLAR_MOVEMENT_V0_20261019.json), [complete three-source result receipt](../research/MOVEBANK_SOLAR_MOVEMENT_V0_RESULT_20261019.json), [analysis](../scripts/movebank_solar_movement_20261019.py).

## Ecological question

At similar astronomical daylength, do free-ranging mammalian individuals redistribute *observed GPS displacement speed* between daylight and nighttime on increasing versus decreasing photoperiod dates, and does the direction differ among the source populations? This asks about ecology, not model prediction performance.

A source animal supplies a mean contrast across years where it has >=10 qualified *pairs of dates*. Every date pair is at least 30 days apart, daylength differs by no more than 5 minutes (observed date-latitude approximation), and both daylight and nighttime have at least three usable consecutive GPS step intervals of 0.5–2 hours in each branch. Each source file was independently checksum-replayed before measuring step distances.

The measured response is **falling − rising in [log(1+median NIGHT GPS straight-line km/h) − log(1+median DAY GPS straight-line km/h)]**. Each individual contributes equally within its source after averaging across date pairs and available years. To separate relative-change mechanisms, daytime and nighttime differences are also reported separately. Individual resampling gives 2,000-replicate descriptive percentile ranges and *does not* make many time-stamped fixes or multiple annual cycles independent ecological populations.

## Unselected results, including null/weak cases

| Source population (one archive each) | Original animals | Eligible animals (>=10 day pairs in a year) | Mean relative night−day change | DAY component | NIGHT component | Individual bootstrap 95% interval | Positive/negative animals |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Canadian elk (*Cervus elaphus*) | 175 | **12** | **+0.04500** | −0.02411 | +0.02089 | +0.02409 to +0.06187 | 11 / 1 |
| Florida wild pig (*Sus scrofa*) | 10 | **5** | **−0.00098** | +0.00170 | +0.00072 | −0.04009 to +0.03354 | 3 / 2 |
| Connecticut American black bear (*Ursus americanus*) | 21 | **20** | **−0.07717** | +0.06685 | −0.01032 | −0.08877 to −0.06591 | 0 / 20 |

The full source-authenticated 1,820,987 GPS fixes reduced to 485,921 valid, within-period adjacent GPS steps across all individuals. Only **12/175 elk, 5/10 pig and 20/21 black bear** individuals met the predeclared *movement analysis* sampling eligibility. Source populations are **three**, not 37: 37 is the sum of admitted individuals within three source archives. An archive may contain repeated individual-years and shares of broader recruitment programmes; source counts cannot be promoted to regional replications without provenance reconciliation.

### Biological reading

The exploratory seasonal response is **heterogeneous** rather than universally nightward. At matched daylength, elk show a positive night-relative difference on the decreasing-daylength branch (11/12 included marked elk), with *both* lower daytime and higher nighttime observed displacement. Black bears have a night-relative decrease (20/20 included individuals), driven mainly by higher daytime displacement; the nighttime component is mildly negative. Florida wild pigs show no coherent directional difference in this small admitted group.

These are genuinely new grouped outputs calculated on archived GPS event rows according to ODSP's fixed questions. They are NOT yet evidence that elk avoid heat, black bears follow vegetation or tourists, that any mammal changes its internal circadian phase, or that one clade generally behaves differently from another. This analysis did not join environmental conditions at the animal dates, observe actual human schedules or estimate continuous activity. GPS straight-line speed is a lower-bound displacement measure, not an animal's true traveled distance or physical activity budget.

**Important sensitivity boundary:** The within-source elk result is conditional on the 12 animals with qualified GPS interval/date support, not the full 175 originally archived elk; observation-cadence selection may be associated with movement ecology. The individual bootstrap intervals characterize uncertainty under this selected sample and measurement design, not population-wide generalization. Unmeasured GPS scheduling, duty cycle and step-classification errors may contribute to contrasts. The method does not pretend that a 45-minute step and an 8-hour gap measure the same ecological time.

## Next biological tests

To distinguish species from geography and telemetry programmes, the next fixed batch comprises eight additional single-taxon GPS source archives including within-taxon comparisons (two moose sites and a second elk archive). [Selection roster](../research/MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_20261019.json); retain every included source and zero/undefined result. Then relate admissible group and individual-date contrasts to environmental seasonal state (ERA5 thermal exposure, rainfall and independently derived vegetation phenophase), prioritizing **effect magnitude, signs, biological trait differences and uncertainty**, not out-of-sample predictive scores. Recruitment overlap must be checked before calling two archives independent populations.

Related independent environmental finding: [20-point matched-photoperiod macroclimate pilot](solar_season_macroclimate_database_pilot_20261019.md) shows that temperature and the precipitation-minus-reference-ET0 seasonal contrasts do not share a single universal sign. That macroclimate pilot is *not yet linked to these GPS animals*. The distinct optical camera results remain exploratory photographed-time contrasts, not animal GPS movement.

### Source and reuse attribution

- Elk: Movebank Data Repository [10.5441/001/1.5g4h5t6c](https://doi.org/10.5441/001/1.5g4h5t6c), CC0 in 2026-10-19 archive metadata.
- Florida wild pigs: [10.5441/001/1.719](https://doi.org/10.5441/001/1.719), CC0.
- Connecticut black bears: [10.5441/001/1.706](https://doi.org/10.5441/001/1.706), CC BY 4.0.

Keep original source creator attribution and complete license statements in the [Movebank source inventory](../research/seasonal_database_catalog/2026-10-19/movebank/README.md). Raw trajectories, exact GPS positions and individual event-level identities were neither committed nor uploaded.
