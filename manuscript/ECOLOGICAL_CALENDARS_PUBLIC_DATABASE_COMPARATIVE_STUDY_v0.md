# Ecological calendars and diel displacement in terrestrial mammals

**Comparative ecological working manuscript v0 — 2026-10-25 | ODSP source-original public-data programme | DRAFT, not submission-ready**

**Working title:** *Same daylight, different ecological calendars: contrasting daytime and nighttime displacement among terrestrial mammals*

## Abstract

Astronomical daylength provides a repeatable seasonal reference, but animals at comparable daylength can experience different food, water and thermal environments. We assembled a transparent observational source frame from a public census of **437 Movebank Data Repository packages** and separately inventoried 26 GBIF camera-trap-data-package records, rather than beginning with published statistical effect estimates. We reprocessed source-original MD5-verified GPS tracking under common solar-daylight and within-animal observation criteria; a separate Serengeti camera route was kept on its own photographic-detection scale. Source-admitted original mammal cohorts show heterogeneous seasonal changes in relative nighttime versus daytime GPS displacement, and **distinct daytime/nighttime displacement changes can generate a similar relative response**. Both independent African elephant source cohorts showed relative daytime-shifted displacement at matched astronomical daylength, though their absolute day/night components differed. In a four-ungulate Utah source, pronghorn showed greater daytime GPS step displacement than mule deer in shared coarse geographic/calendar strata; an independently archived Wyoming source reproduced a positive raw association between longer days and relative nighttime displacement in mule deer. Conditioning on original source ERA5 Tmax and antecedent climatic P−ET0 revealed different source-specific associations, but **not a demonstrated hydrologic or thermal mechanism**. The ecology-facing finding is structured heterogeneity of observed diel displacement at common solar references; animal activity duration, ecology-driven mediation and universal causal responses remain unidentified.

**Keywords:** ecological calendars, daylength, seasonal phenology, diel movement, GPS telemetry, resource seasonality, ungulates, public biodiversity data, comparative ecology

## Central ecological hypothesis

> **Astronomical time does not uniquely determine organisms' ecological state. At the same solar daylength, the season's environmental history and species' ecological strategies can correspond to different day/night movement reallocations.**

This is **not** the claim that all mammals become nocturnal with warmth, all species have photoperiod memory, or a prediction model must generalize.

**Three discriminating ecological questions**

1. **Same solar geometry, different animal time use:** At equal daylength across rising/falling seasonal branches, does the **within-individual** nighttime-minus-daytime GPS displacement speed change? How does its sign vary among independent original study cohorts?
2. **Different architectures of the same apparent temporal niche shift:** Is a more night-relative response due to a nighttime displacement increase, daytime decrease, both, or neither? Do these architectures differ across species or habitats, rather than forming a universal diel score?
3. **Different ecological calendars:** Are conditional daylight associations related to daily thermal conditions, water-balance/vegetation phenophase and movement strategy *within populations*, and do those associations differ between study regions? This third explanation remains **hypothesis-generating** until independent experienced-environment measures are joined and replicated.

### Falsification logic

If independent populations observed under comparable schedules and solar conditions show no within-individual diel reallocation or ecosystem/species heterogeneity beyond source observation uncertainty, Question 1 does not support a meaningful biological calendar effect. If observed night-relative changes have identical day/night component structures within source/area, Question 2 loses its intended ecological novelty. If climate and independently observed vegetation/habitat conditions do not correspond to repeatable variation in movement responses under sampling-controlled within-individual comparisons, the resource-calendar pathway should be rejected in its current form. **No predictive score is needed for these ecological tests.**

## Source design and inference units

The original **437 Movebank packages** are a *discovery frame*, not 437 valid independent animal populations or a globally representative sample. One 2026-10-19 source archive audit resolved 1,677 ORIGINAL bitstream metadata objects. Each admitted original GPS source retains DOI, original provider MD5 and dataset license; every candidate with provider-integrity mismatch or inadequate observational support remains held, not selectively replaced. The independent GBIF camera-trap registry is an additional candidate frame, not an animal dataset already included in the following GPS numerical comparisons.

For GPS, the preserved source estimands use **real successive geolocated GPS step distance per observed time** within solar day/night periods, after a timestamp-only hour-sampling adjustment where necessary, all with animal identity retained internally for within-animal aggregation. The `q` score is `log(1+night GPS displacement km/h) − log(1+day GPS displacement km/h)`. The solar-daylength date-matched seasonal change is `q_falling−q_rising`. The daylight slope is `q ~ local astronomical daylight duration` estimated within source individual-calendar years. These **distinct estimands must not be conflated**. They are not locomotor active-minute fractions, foraging time, or independent observations of animal competition.

Each original source individual—not each fix, day, matched date, or telemetry population—is the lowest unit in source-level individual bootstrap summaries. Across-source ecological generalization additionally depends on source-population counts and independence, which remain limited.

## Source-backed observational results

### A. At equal daylength, different mammal populations have different seasonal displacement structures

Across ten early mammal source cohorts, source-verified within-animal date-matched comparisons show positive, negative and near-zero relative-night changes; **not a universal positive nightly shift**. For example, Canadian wapiti (12 admitted animals) had `q_falling−q_rising=+0.04500` (11/12 positive), while Connecticut black bears (20) had `−0.07717` (20/20 negative). Florida pigs' source mean was near zero. These are different ecosystems/study years, not controlled species effects.

Two originally independent *Loxodonta africana* source studies yielded a **negative** nighttime-relative change under a common time-only hourly GPS resampling rule: Etosha `−0.15013` (14 animals, all negative), Kruger `−0.02889` (13 animals, 11 negative). Yet **Etosha's nighttime absolute displacement decreased while its daytime increased**, whereas **Kruger's daytime and nighttime both increased**, with a larger daytime rise. In Etosha's same-supported 2009 and 2010 cycles, elephant negative point estimates remained `−0.26287` (11 animals) and `−0.24226` (5). The contemporaneous jackal source's 2009 mean was near zero with an interval spanning zero, not secure proof of opposing species-specific behavior.

A Kruger original source collar-relative external-temperature indicator supported 1,787 temperature-complete matched GPS daylength pairs and a **weak unresolved** within-elephant thermal-gradient versus diel-GPS contrast slope `+0.001172 per °C` (13 animals; 95% animal-bootstrap `−0.002041 to +0.004154`). Original Thaker and colleagues already studied broader elephant thermal-speed behavior; this matched-photoperiod **distinct** analysis does not establish a new temperature-causal mechanism.

### B. Within one public Utah four-ungulate study, day/night components differ by taxon

In the original Utah UDWR GPS archive (Movebank DOI 10.5441/001/1.711), **2,618** individually eligible source animals across pronghorn, wapiti, mule deer and bighorn sheep contributed to signed night/day GPS displacement means. All four mean `q` values were negative (higher observed daytime step speed), but their magnitudes differed.

Under original source-support matching on **1° geographic grid × calendar year-month**, pronghorn minus mule deer had a day/night `q` difference `−0.10504` across 50 original shared grid-month strata. Reweighting equally across **seven distinct coarse geographic grids** gave `−0.09837`, with a descriptive grid-bootstrap interval `−0.11505 to −0.08192`. The source contrast was generated mainly by pronghorn's **higher daytime** source GPS log1p step speed (`+0.09649`), not a large **lower nighttime** speed (`−0.00187`). This is an ecological movement-architecture observation in one study, not an evolved species-specific foraging niche or actual encounters.

### C. Similar raw daylight slopes can conceal different conditional ecological calendars

Source-original mule deer observations gave **very similar positive raw daylight slopes**: Utah `+0.005619` (1,683 qualified animals), Wyoming `+0.005538` (118). In separate *original October 23* verified daily ERA5 analyses using a common source/date-level adjustment for modelled Tmax and preceding 30-day climatic precipitation minus reference ET0, the Utah daylight slope was `−0.001340` (1,653 animals, interval `−0.002489 to −0.000107`), while Wyoming remained `+0.004238` (117 animals, interval `+0.002854 to +0.005660`). Bighorn slopes were unresolved in both original sources.

This difference is **ecologically intriguing but not causal**: raw and adjusted estimates have partly different admitted animals and dates; landscapes, climatic regimes, individual migration, source collar schedules and phenotype differ. **Two sources do not define a species-wide empirical law**, and there is not yet independently measured vegetation phenophase for those animals.

A separate Utah **source-grid/month** analysis detected an exploratory bighorn-versus-mule deer association with regional monthly P−ET0, even after adding modelled astronomical daylength and air temperature (`−0.01675 per 100 mm`, 6 geographic blocks, source-bootstrap `−0.02474 to −0.00794`). But the same-month different-year comparison's interval included zero. ERA5 P−ET0 is **not measured soil water, biomass, vegetation greenness or forage quality**.

### D. Crucial original weather source replay HOLD (October 25)

On October 25, a separate diagnostic attempt to decompose the source daylight associations into thermal/water seasonal covariance terms passed GPS source MD5 and original GPS group-effect replays, but the source-original October 23 **ERA5-adjusted** means were not bit-numerically reproduced when weather was re-fetched. The *unchanged original adjustment algorithm*, using the newly retrieved Wyoming ERA5 source for the same 117 mule deer, gave **+0.004304305** instead of original **+0.004237831**. Utah similarly had a small new-versus-old source discrepancy. No original animal inclusion rule was relaxed, old published source means were NOT overwritten, and no decomposition result from that route is accepted in this manuscript.

Raw ERA5 response hashes also differed, which can happen from changed source values and/or response metadata; the precise cause has not been isolated. To pursue ecological mediation credibly, archive/version the actual atmosphere/land and satellite response data before opening explanatory outcomes rather than relying only on current provider queries. This is a source/reproducibility **limitation**, not proof that climate is irrelevant.

## Contribution and limitations

The manuscript's strongest positive contribution is a cross-source empirical observation: **matching solar reference alone is insufficient to predict/define one universal ecological displacement schedule**, and simple day/night labels conceal biologically distinct *absolute* displacement components. Repetition across two elephant populations and raw mule deer daylight responses across two original independent surveys motivates testing a common ecological-calendar framework. No photo trap camera-hour calibration or human civil-clock entrainment is inferred. The Serengeti *source camera photograph* observations and one source environment pilot can provide a separate phenomenon-level case study but cannot be numerically pooled with GPS speed or counted as repeated independent animal populations.

The source archives were collected by other original authors; our methodological contribution is a **hypothesis-first, systematically enumerated original-data database** and new fixed ecological contrasts. Public archive accessibility, tag coverage, sex/age and habitat sampling are selection mechanisms; the current analysed subset is not all 437 original packages, 254 animals do not mean 254 independent populations, and species coefficients confound recruitment study when only one source per taxon.

## Research programme before submission

The logically required next ecological data connection is **source-date- and GPS-observation-matched independent satellite NDVI / vegetation phenophase**, together with archived weather source values (not raw source hash only), within-individual daylight and measured daytime/nighttime displacement components. Test whether forage-greenness conditions and biologically relevant resource demand explain any of the source-specific seasonal patterns, while retaining nulls, ecological guild differences, population/year hierarchy and environmental source availability. Do not substitute predictive transfer performance for identifying ecological relationships.

## Direct source and execution references

- [Systematic public-source registry and source-original inventory](../research/seasonal_database_catalog/README.md).
- [Ten mammal-source sign and day/night component synthesis](../docs/solar_calendar_multispecies_ecological_results_20261019.md).
- [Kruger independent original elephant temperature + matched-photoperiod analysis](../docs/kruger_thermal_gradient_matched_solar_ecological_results_20261019.md).
- [Utah first four-ungulate source GPS run](https://github.com/zuizui0223/odsp/actions/runs/39216810610), [spatial-grid component sensitivity](https://github.com/zuizui0223/odsp/actions/runs/39218494366).
- [Wyoming original two-ungulate study](../research/wyoming_two_ungulates_20261022/README.md) and [source run](https://github.com/zuizui0223/odsp/actions/runs/39723531890).
- [Utah original daily Tmax+30d P−ET0 source](https://github.com/zuizui0223/odsp/actions/runs/39878716871), [Wyoming independent daily source](https://github.com/zuizui0223/odsp/actions/runs/39878174016).
- [Complete six original source×taxon ecosystem-calendar contrast table](../research/solar_ecological_calendar_cross_source_20261025/source_level_daily_climate_daylight.csv), [interpretation and replay caveat](../research/solar_ecological_calendar_cross_source_20261025/README.md).
- [Original October 25 exact-replay route contract](../research/ODSP_TWO_STUDY_ECOLOGICAL_CALENDAR_COUPLING_V0_20261025.json), [source runner](../scripts/movebank_ecological_calendar_coupling_20261025.py), [known-truth tests](../tests/test_movebank_ecological_calendar_coupling_20261025.py).

**Scope:** Hypothesis-generating public-database comparative ecology. Original tracking/remote-source copyrights and restrictions remain acknowledged. Do not publish original animal GPS/IDs/date-wise trajectories or claim causal water/temperature/solar mediation. Keep PR #267 and #268 in Draft.
