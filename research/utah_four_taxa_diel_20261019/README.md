# Four ungulates, one public study: diel displacement and solar-daylength structure

**Original-source, hypothesis-led observational ecology — 2026-10-19.** Run [39216810610](https://github.com/zuizui0223/odsp/actions/runs/39216810610) finished successfully; original provider MD5 and six independent synthetic tests passed. This report introduces no new hypothesis tests or source reclassification.

## Biological finding

At source-reported GPS intervals standardized to one original location per UTC clock-hour, all four sampled terrestrial ungulate cohorts had **higher observed movement displacement speed during day than night** on an equal-*animal*-weighted scale. But they differed appreciably in their **degree** of dayward displacement and in within-individual year associations with astronomical daylength.

| Taxon | Qualified animals | Night–day log1p displacement | 95% animal-bootstrap interval | Within-animal-year slope per additional hour daylength | Slope 95% interval |
| --- | ---: | ---: | --- | ---: | --- |
| *Antilocapra americana* (pronghorn) | 215 | **−0.11717** | [−0.12175, −0.11259] | **+0.00490** | [+0.00156, +0.00801] |
| *Cervus elaphus* (wapiti/elk) | 337 | −0.03189 | [−0.03577, −0.02763] | **+0.00960** | [+0.00714, +0.01195] |
| *Odocoileus hemionus* (mule deer) | 1,723 | −0.02185 | [−0.02321, −0.02047] | **+0.00562** | [+0.00439, +0.00692] |
| *Ovis canadensis* (bighorn sheep) | 343 | **−0.06576** | [−0.06902, −0.06273] | −0.00341 | [−0.00652, +0.00061] |

Totals: **2,618** eligible animals for source-specific diel contrast, **2,567** with individually estimable daylength associations. Sampled original field individuals are clustered within ONE study, and none are independent population or ecosystem replications. Mean per-animal observations and animal-bootstrap uncertainty are descriptive. Interpreting the slope as direct daylength *causation*, circadian entrainment or true activity-budget change would exceed source evidence.

### Does the pattern disappear on shared geography and calendar support?

Six source taxon pairs have overlap at original reported **1° latitude × 1° longitude × calendar year-month** scale. A cell-month enters per taxon only where at least 3 tracked animals contribute at least 3 admitted days each. Compare matched **grid-month** means, not independent sample GPS points. Results are in [six-pair CSV](shared_gridmonth_species_contrasts.csv).

| Taxon A − taxon B | Shared eligible grid-month cells | Relative night/day displacement difference A−B |
| --- | ---: | ---: |
| Pronghorn − wapiti | 16 | **−0.11040** |
| Pronghorn − mule deer | 50 | **−0.10504** |
| Pronghorn − bighorn | 27 | −0.04988 |
| Wapiti − mule deer | 76 | +0.00319 |
| Wapiti − bighorn | 24 | +0.05351 |
| Mule deer − bighorn | 92 | +0.03853 |

**Supported pattern in this one published study:** Pronghorn records were considerably more daytime-biased than elk and mule deer even when coarse locality and calendar year-month were the same. Elk and mule deer showed almost no contrast at that support scale; bighorn had an intermediate relationship. The observed `q=log(1+night GPS km/h)−log(1+day GPS km/h)` is a speed difference, **not the proportion of activity that occurs at night**.

The geographic grid is large (~1°), the dates and individual sampling frequencies within each grid-month need not match, and spatial-month cells repeat across years and individual recruitment clusters. The six pairwise contrasts **have no independent cell-cluster uncertainty interval yet**, cannot demonstrate true sympatric encounters or causal habitat-independent trait differences, and are **not six independent ecosystem replications**. Sensitivity to nested sites/year and standardized common-cell weighting remains a separate quantitative test.

### Solar-calendar implication

Within individuals, the association between lengthening daylight and nighttime-relative GPS speed is positive for pronghorn, elk and mule deer; bighorn slope on this same scale spans zero. In this study the *ranking* of diel displacement among taxon cohorts and the within-individual daylight relationship appear biologically heterogeneous. Environmental temperature, plant phenology, predation and capture-area effects remain alternative explanations; their contributions are **untested**.

**Crucial distinction:** This is not proof of spring/autumn seasonal hysteresis at *matched photoperiod*. The independently frozen strict opposite-branch Utah analysis [39212935666](https://github.com/zuizui0223/odsp/actions/runs/39212935666) qualified **zero** individual-years in each of the four taxa and remains source-sampling **UNAVAILABLE**, not a negative biological effect. The present analysis answers the separate question of day/night displacement **and daylight associations**, under the source's actual sampling opportunities.

## Publicly reusable derived database and provenance

Source package: [Movebank Utah UDWR GPS 2019–2020, DOI 10.5441/001/1.711](https://doi.org/10.5441/001/1.711) (source metadata declares CC0). The original archive appears in the complete [437-package public Movebank census](../../research/seasonal_database_catalog/README.md) and includes the four taxa without sign-based recruitment. Provider ORIGINAL ZIP bytes **63,369,773**, original MD5 `08200c9dbdf7989fb5a35467213b7e5a`, bitstream UUID `9c4aaf76-7476-4305-8b14-9a6d8886e39a`.

The [taxon summary CSV](taxon_daylength_summary.csv) and [co-observed location-month taxon contrast CSV](shared_gridmonth_species_contrasts.csv) are source-derived **group aggregates**, not unlicensed redistribution of precise animal movements. Recompute using [v0 source and ecology program](../MOVEBANK_UTAH_DIEL_PHOTOPERIOD_V0_20261019.json), [runner](../../scripts/movebank_utah_diel_photoperiod_20261019.py) and [known-truth tests](../../tests/test_movebank_utah_diel_photoperiod_20261019.py).

Data-curation principle: these summaries are a component of ODSP's own systemically enumerated public-observation ecological database. No new analysis was chosen because its result appeared attractive. Negative, near-zero and unsupported source outcomes remain present.


## Added geographically blocked ecology analysis (2026-10-19)

A separately source-registered, **post-outcome descriptive robustness route** repeated the entire original provider-MD5 Utah ZIP read and **reproduced all six previous common grid×year-month night/day contrasts and cell-month counts exactly before computing anything new**. Six independent synthetic controls and the full [GitHub Actions run 39218494366](https://github.com/zuizui0223/odsp/actions/runs/39218494366) passed.

The new [source-derived geographic-block CSV](spatial_block_day_night_components.csv) holds all six paired-taxon results with their actual number of repeated grid-months, **distinct 1-degree geographic blocks** (3, 7, 5, 10, 6, 13), and decomposed night- versus daytime source GPS step-speed differences. One geographic cell with records in several months counts as **one** geographic block. Each block receives equal weight for the new comparison; the first pre-existing equal-grid-month comparisons are preserved separately. Each sample still comes from one published Utah source, and geographically adjacent 1-degree cells are not independent ecosystems.

**Most informative positive finding:** Pronghorn minus mule deer has equal-block `q` difference **−0.09837** across **seven** separate 1-degree geographic blocks (95% geographic-block bootstrap −0.11505 to −0.08192). Its **daytime** log1p GPS movement-speed difference is **+0.09649**, whereas the **nighttime** difference is **−0.00187**. Thus, in the *coarsely matched original source space and month*, the pronghorn's greater relative dayward movement is driven primarily by greater **observed daytime displacement**, not a pronounced deficit of nighttime displacement relative to mule deer.

The corresponding pronghorn minus bighorn contrast is −0.04846 over **five** distinct geographic blocks, with day +0.09196 and night +0.04350; the geographic-bootstrap interval is −0.05477 to −0.04358. In contrast, wapiti minus mule deer is close to zero: equal-block +0.00956 over **ten** geographic blocks, interval −0.00419 to +0.02478. Pronghorn minus wapiti is −0.11397, but with only **three** geographic blocks it has **no accepted spatial-bootstrap interval** (leave-one-grid-range −0.14743 to −0.08818 is not a confidence interval).

**Scope ceiling:** the intervals are conditional on the sampled broad geographic blocks and *not* independent species/biome replicates. Shared grid-month does not prove synchronous species encounters or remove source sex/age, detection, GPS schedule, microhabitat, grazing intensity or individual recruitment confounding. We have **not yet tested forage/vegetation or field-measured thermal causes**. The source study did not support the distinct original within-individual spring-versus-autumn matched-daylength test; that previous source-unavailable outcome remains unchanged.
