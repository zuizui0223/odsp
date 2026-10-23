# Equal daylight does not imply a single kind of temporal niche shift

**2026-10-19 | ODSP original-public-source ecological synthesis (post-outcome descriptive, not an additional confirmatory test).** This memo combines previously verified source-level effects and keeps the original frozen analyses unchanged. Its purpose is biological explanation, not cross-validation or detection-method optimization.

## Central biological question

When astronomical daylength is approximately the same on two sides of a local summer solstice, **which part of animals' observed diel displacement changes**? Does a species move less during daytime, more during nighttime, both, or neither? Do nominally similar changes in *relative* nighttime use conceal different changes in the *absolute day and night components*?

The tracked response is source GPS great-circle **straight-line displacement rate** for qualified 30–120-minute intervals, as `log(1 + median km/h)`; it is NOT the total 24-hour movement distance, energetic activity, true hour-by-hour locomotion, or direct temporal niche occupancy. Source-specific photocamera counts are not pooled. Equal-photoperiod date comparison was predeclared before new source movement outcomes; this **cross-cohort sign typology is assembled after seeing those results**, so it is descriptive.

Let `D` denote the falling-minus-rising change in daytime source GPS displacement on this log1p scale, `N` the analogous change in nighttime GPS displacement, and `R = N - D` the **relative-night contrast**. These component means are calculated with equal weight across qualified animals within one source; repeated solar cycles are first averaged within animals.

## First 10 archived mammal source cohorts, with the day/night components exposed

| Source cohort (one recruitment/study context) | Eligible animals | Δ day, D | Δ night, N | Relative night, R=N−D | Observed signed component pattern |
| --- | ---: | ---: | ---: | ---: | --- |
| Canada wapiti (*Cervus elaphus*) | 12 | **−0.02411** | **+0.02089** | +0.04500 | Day down / night up |
| Wyoming mule deer (*Odocoileus hemionus*) | 118 | **−0.01657** | **+0.01457** | +0.03115 | Day down / night up |
| Connecticut black bear (*Ursus americanus*) | 20 | **+0.06685** | **−0.01032** | −0.07717 | Day up / night down |
| Florida wild pig (*Sus scrofa*) | 5 | +0.00170 | +0.00072 | −0.00098 | Both nearly unchanged |
| Virginia white-tailed deer (*Odocoileus virginianus*) | 33 | +0.00317 | −0.00002 | −0.00319 | Nearly unchanged |
| Alberta wolf (*Canis lupus*) | 9 | −0.01178 | +0.01663 | +0.02841 | Opposite-sign point means but large animal uncertainty |
| Southern Brazil lowland tapir (*Tapirus terrestris*) | 22 | +0.01279 | +0.00488 | −0.00791 | Small co-increase |
| Etosha black-backed jackal (*Canis mesomelas*), original-step v0 | 8 | +0.01638 | +0.07123 | +0.05485 | Both increase; night more |
| Etosha African elephant (*Loxodonta africana*), time-only hourly v1 | 14 | **+0.10664** | **−0.04348** | **−0.15013** | Day up / night down |
| Kruger African elephant (*Loxodonta africana*), time-only hourly v1 | 13 | **+0.05238** | **+0.02349** | **−0.02889** | **Both increase; day more** |

The two elephant populations' **relative dayward changes share a negative sign**, even though their **absolute-component signatures are qualitatively different**: Etosha decreases nighttime displacement while increasing daytime displacement; Kruger increases both day and night, with larger daytime increases. These components are robust descriptions of *observed GPS displacement* conditional on source and cadence, not direct evidence of resource substitution, circadian plasticity, heat-avoidance regulation or evolved species-specific strategy.

This is a nontrivial ecological consequence of the data: the relative night/day response is **not a sufficient biological summary**. It is impossible to tell whether night locomotion actually rose, fell or stayed about the same from relative-night sign alone.

For strictly **same hour-time selection** at Etosha, jackals have R=+0.04479 (Δday=+0.01923, Δnight=+0.06402; eight animals, 5 positive/3 negative; individual-bootstrap interval −0.00211 to +0.11922). Because that interval crosses zero, do **not** present stable opposing species-specific direction as established.

## Independent population and independent year checks

Two original African elephant archives were provider-MD5 verified before ecological analysis: Etosha original 2.93 million fixes ([source-run](https://github.com/zuizui0223/odsp/actions/runs/39207964106)) and Kruger original 283,688 fixes ([source-run](https://github.com/zuizui0223/odsp/actions/runs/39210827847)). Both use time-only per-UTC-hour GPS sampling to account for Etosha's unusually short raw fix intervals. That alternative Etosha route was separately defined following its original 30–120-min adjacent-segment infeasibility and **does not reclassify the failed original v0 endpoint**.

Under the previously identified **2009 and 2010 shared Etosha solar-year** restriction, elephant R remains negative in each year (2009: −0.26287 among 11 animals; 2010: −0.24226 among 5), while jackal R=+0.00926 with a bootstrap interval spanning zero among seven in 2009; only one jackal qualifies in 2010. The apparent strong elephant-jackal opposition in pooled time coverage weakens after the joint-year comparison. Independent source run: [39210319995](https://github.com/zuizui0223/odsp/actions/runs/39210319995).

## Environmental context and mechanism tests already completed

At identical local daylength, regional seasonal temperature and water-balance paths can be mixed. At the Etosha shared coarse ERA5 grid, the prior-30-day precipitation-minus-reference-ET0 index increases on the falling branch in both source cohorts (+99.63 mm in elephant-admitted dates, +107.85 mm in jackal-admitted dates); the observation years and actual dates partly differ. This index is **not measured forage, soil moisture, or waterhole access**. The specifically measured 2009 Etosha source windows also have positive climatic water-balance differences, while the GPS effects differ in clarity. Data: [matched-date Etosha ERA5](https://github.com/zuizui0223/odsp/actions/runs/39208971379) and [year-stratified Etosha GPS/ERA5](https://github.com/zuizui0223/odsp/actions/runs/39210319995).

**Direct thermal indicator at Kruger:** The original telemetry archive provides `external-temperature`, a collar thermochron measurement that the 2019 source publication interpreted only as a relative ambient thermal indicator with device and animal heat contributions. All 283,688 original source temperatures passed the broad preregistered QA range. In 1,787/1,787 GPS-matched same-photoperiod pairs, collar daytime temperature changed +1.0615°C, nighttime +1.5326°C, so the day-minus-night gradient changed −0.4711°C. The **within-elephant/year-centered association** of changing relative collar temperature gradient with R had an estimated mean slope **+0.001172 log1p km/h per °C**, individual-bootstrap interval **−0.00204 to +0.00415**, across 13 elephants. This did **not resolve a consistent linear relationship**. It does not disprove thermoregulation or temperature-dependent movement and does not reproduce a new result from the original paper: Thaker et al. 2019 already examined broad temperature–speed/water-shuttling associations. New source-specific match: [39211773115](https://github.com/zuizui0223/odsp/actions/runs/39211773115).

## Current falsifiable ecology programme and limits

The main question is **which seasonal ecological contexts coincide with absolute day/night movement components at equal light duration, and which biological traits differentiate those relationships**. The most informative next observations are climate/vegetation/water exposure actually *encountered* by source animals during the same observation windows and multiple studies per taxon. Source/cohort, capture protocol, sample year, sex and region still confound species-wide trait inference. The Canadian wapiti archive is female-only; the Kruger elephant archive contains 14 female tagged elephants from different herds. Sampled animal counts must not be treated as global species replicates.

This table contains 10 study-source cohort rows from nine wild mammal species. It is **not a taxonomically random global sample**. A separate [four-taxon public Utah cohort contract](../research/MOVEBANK_UTAH_FOUR_TAXA_SOLAR_V0_20261019.json) extends the registry-based ecological comparison inside one field-study package; its outcomes are not reported here before source workflow completion.

### Source receipts

- Initial Northern 3 source cohorts: [canonical machine-readable result](../research/MOVEBANK_SOLAR_MOVEMENT_V0_RESULT_20261019.json), run [39202860827](https://github.com/zuizui0223/odsp/actions/runs/39202860827).
- Eight additional Northern archives with positive, null, insufficient and source-HOLD values: [complete ledger](../research/MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_RESULT_20261019.json), run [39203695999](https://github.com/zuizui0223/odsp/actions/runs/39203695999).
- Southern Brazilian tapir and Etosha jackal: [southern source run](https://github.com/zuizui0223/odsp/actions/runs/39207354970).
- Two original elephant cohorts and relative temperature examination: source links above.

**Decision:** do not advertise a universal shift toward night (or day) or a causal heat/water mechanism. Do present the source-backed observation that temporally matched species/cohorts have heterogeneous signed day/night GPS displacement components, including opposite component architectures that can yield the same relative direction.
