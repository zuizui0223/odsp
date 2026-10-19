# A public-data ecology programme: solar and ecological calendars

Date: 2026-10-19  
Status: central hypothesis and first complete source inventories; animal-level database assembly and hypothesis tests are not yet complete.  
Companion: [source inventory](../research/seasonal_database_catalog/README.md) · [existing Serengeti evidence](../manuscript/SOLAR_SEASONAL_HYSTERESIS_ECOLOGY_PAPER_v0.md)

## 研究の中心

**太陽の暦と、その動物が経験する環境の暦のずれは、動物の昼夜の移動配分をどう変えるか。**

同じ個体を、日長がほぼ等しい年内の二時点で比べる。それでも温度や植生の生育段階が違えば、移動する時間帯も変わるという仮説を立てる。目標は、その差を春・秋という区分だけで記述することを越え、独立した個体群や地域について予測することである。場所を変えて環境を追える個体が、時間帯の変更を少なくできるかは、関連する第二の問いとする。

自前で構築するものは、公開された原観測に、出典・個体・観測機会・太陽位相・環境の季節進行を結び付けた比較データベースである。原観測の採集者の著者性とライセンスを維持し、ODSPの貢献を独自の仮説、系統的な統合、比較単位、解析、再利用可能な派生データとして明示する。

## 1. Central hypothesis

**At matched photoperiod within an individual, differences in experienced thermal conditions and vegetation phenophase predict diel movement redistribution across independent populations beyond solar geometry and calendar season alone.**

This is a hypothesis about ecological organization of a temporal niche. The response is when an animal moves; the proposed explanatory state is the seasonal environment where it lives. It does not assume all species become more nocturnal in one calendar season. A wet-season landscape and a cold-season landscape can show different directions for the same increasing/decreasing-daylength label.

The scientific target is a transferable relationship: which environmental contrasts lead to a change in daytime versus nighttime movement, how large that change is, and where the relationship fails. A good global fit without prediction of independent populations is insufficient.

### Why the existing positive results motivate this question

The [Serengeti satellite linkage](serengeti_original_camera_modis_ndvi_photo_link_20261015.md) found greater declining-branch NDVI in all 322 supported camera-site × annual-cycle comparisons at near-equal daylength. Annual mean differences were +0.1646, +0.2727 and +0.2224. Thus the astronomical match did not make the vegetation states equivalent in that landscape. The [camera decomposition](serengeti_within_photo_time_versus_station_mix_ecology_20261015.md) also found repeated within-camera changes in zebra photo timing, although changing station contributions could reinforce or oppose those changes in other taxa.

These results generate the question; they do not establish the mechanism. The [NDVI association analysis](serengeti_ndvi_level_vs_rank_photo_ecology_20261016.md) did not find a consistent vegetation–photo response across the few supported taxon-years. The [duck GPS audit](duck_gps_identifiability_and_next_ecology_20261019.md) found zero median instantaneous speed in 709 of 744 day/night blocks. That endpoint is not a sound basis for a general movement-allocation result. The subsequent [two-part sensor description](duck_gps_reported_speed_occurrence_and_magnitude_20261019.md) separates relative night/day changes from absolute changes within each time window, but adds no independent animals or validated activity measurement. Serengeti, Rhode Island, and the previously inspected duck archive are discovery data, not untouched confirmation data.

The next empirical object is therefore a database of repeated individuals and their environments, assembled across source registries. Camera information supplies a separate observation channel where deployment support permits a comparable seasonal question.

## 2. Predictions and competing explanations

| Prediction | Test | Evidence against it |
| --- | --- | --- |
| **P1: environmental season transfers.** Thermal and vegetation state explain seasonal redistribution beyond the solar and calendar baseline. | Compare prespecified predictive distributions in a completely held-out population, and then a held-out region. Give populations equal influence in the principal comparison. | Environmental terms fail to improve independent prediction, or improvement is confined to one source/population. |
| **P2: ecological contrast matters more than a universal branch sign.** Equal-daylength pairs with different environmental contrasts have different predicted movement contrasts. | Predict the within-individual difference from independently derived environmental features; compare with a branch-only prediction. Examine regions in which the environmental ordering across branches reverses. | A common branch effect predicts equally well, environmental differences add no reproducible information, or the learned environmental response fails when the calendar–environment relation changes. |
| **P3: conditional heat avoidance.** When daytime thermal burden increases relative to nighttime conditions, movement shifts away from hot daylight hours. | A prespecified directional thermal term, with separate species/guild responses and measured risk modifiers where available. Night/day and daylight core/edge are distinct contrasts. | A precise null or opposite association in the specified stratum, or a pattern explained by observation cadence rather than thermal exposure. |

P1 is the central test. P3 is one mechanism within it, not an explanation already proved by the Serengeti pilot. Vegetation greenness does not imply a universal positive or negative effect on night use. The initial vegetation representation is level plus independently estimated phenophase/change, with prespecified guild interactions; interpretation concerns vegetation state, not directly measured forage quality.

An endogenous annual state, breeding, migration stage, moonlight, predation, and human use can also produce seasonal differences. Matching daylength does not remove these explanations. In particular, [Daan and Aschoff (1975)](https://doi.org/10.1007/BF00345851) already reported unequal spring/autumn activity duration at equal photoperiod in captive finches. We retain calendar branch in the baseline and report any residual branch effect after measured environmental predictors.

**Human-clock question.** Where a source contains measured visitor, vehicle, livestock, or human-detection timing, test whether wildlife timing follows that schedule after solar and environmental conditions are included. A civil time zone, daylight-saving label, road map, or human-footprint score alone is not a measurement of the human daily schedule. Static human-pressure variables may modify responses but cannot identify a clock-entrainment mechanism.

**Secondary spatial question.** Does changing location reduce the environmental contrast an individual experiences, and is this associated with less temporal redistribution? Compare used locations with an explicitly defined accessible or reference environment. This is initially an observational association: habitat is chosen by the animal. Keep moving individuals in the cohort. A same-cell-only restriction would remove much of the proposed response and cannot by itself test a spatial/temporal substitution mechanism.

## 3. Sampling frame: enumerate databases before choosing studies

The first inventory was retrieved on 2026-10-19. It is a dated discovery frame, not an estimate of the number of eligible animals or independent ecological studies.

| Registry | Frozen scope | Retrieved records | Role |
| --- | --- | ---: | --- |
| Movebank Data Repository | All records in the **Data packages** collection, UUID `e1ae0743-5f80-4700-b21f-0535a10daee9` | 437 packages, 437 distinct package UUIDs; 18 pages | Primary individual movement / activity-sensor discovery frame |
| GBIF dataset registry | All records returned by `endpointType=CAMTRAP_DP` | 26 dataset records, 26 distinct dataset keys | Complementary camera/deployment discovery frame |

The Movebank inventory includes 258 packages explicitly listing GPS and 47 listing acceleration; these labels can overlap. Publication dates are not tracking dates. There are 413 distinct nonblank source study-ID strings across the 419 packages reporting that field; a study ID still does not define an independent population. The GBIF registry contains heterogeneous monitoring designs; a Camtrap DP endpoint does not establish a suitable mammal camera series.

Every source remains in the registry through screening. Acquisition decisions use source permissions, modalities, temporal/geographical coverage, and the ecological scope defined here, not an article's reported sign or statistical significance. Existing abstracts and pilot results have been read, so this is outcome-independent selection by rule, not a claim that investigators have never seen published outcomes.

Begin with free-ranging terrestrial mammals for the primary biological comparison. Keep birds as a separately specified extension and do not pool flight movement, terrestrial displacement, accelerometer activity, and camera detections into a common numeric activity endpoint. Domestic, captive, marine, and incompatible-sensor records remain in the inventory with explicit scope labels. Resolve multi-taxon packages at the animal level. No source is removed merely because its effect is null, heterogeneous, or opposite to the hypothesis.

### What the own database will contain

| Table / unit | Required content | Scientific purpose |
| --- | --- | --- |
| Source package | Stable source DOI/key, version, license statements, file hashes, source study IDs, original attribution, screening state and reason | Reproducible sampling frame and provenance |
| Population / cohort | Recruitment study, taxon, geographic population, years, overlap group | Define independent comparisons and avoid counting archive versions twice |
| Individual / deployment | Source-qualified individual ID, sensor, deployment dates, capture context, sex/age if supplied | Preserve repeated individuals and known scope |
| Timed observation opportunity | UTC time, location, observed/missing fix, expected cadence, valid sensor measurements | Separate missing observation from zero displacement |
| Individual-day / solar interval | Solar geometry, actual available day/night hours, observed displacement or validated activity, temporal coverage | Estimate an interpretable timing response |
| Environmental exposure | Versioned temperature and vegetation estimates, acquisition date, QA, spatial/temporal resolution, phenophase and uncertainty | Relate the animal's used environment to seasonal response |
| Opposite-branch contrast | Individual, cycle, paired dates, daylength mismatch, environment differences, movement contrast and support | Test the central within-individual hypothesis |

Deduplicate original event keys or study-qualified individual/time records after resolving versions and overlapping studies. Do not sum package-level animal/location counts and call them unique animals or fixes. Retain raw source values and an explicit mapping to normalized variables.

Public metadata do not settle raw-file reuse terms: preserve all license statements and resolve conflicts before redistribution. A raw-source license need not match the code license. When redistribution is unavailable, release the lawful derived tables plus source references and acquisition code. The inventory contains no newly published precise animal trajectories.

## 4. Analysis decisions before new biological effects are opened

### Outcome and observation unit

GPS measures displacement between positions. It is not total activity or energetic expenditure. Use ground displacement over elapsed time on a declared, source-compatible cadence, with day/night availability and coverage; acceleration may supply a separate validated activity outcome where calibration is documented. Do not reuse the old median-instantaneous-speed endpoint or choose a speed threshold because it yields a positive result.

For the first GPS analysis, target 60-minute displacement intervals from sources with reliable timestamps, positions, and a compatible schedule. Select fixes by time only; retain actual elapsed intervals and avoid filling long gaps with artificial straight-line hourly fixes. Estimate distance per observed hour separately for night, daylight core, and daylight edge. Day/night exposure differs by season, so raw fix counts or total distances alone are not allocation measures. A two-part observation model may handle zero and positive displacement, but its measurement-error rule must be fixed from sensor documentation or independent calibration, not the desired ecological contrast. Sources unable to support this cadence remain documented for other resolutions.

Basic repeated unit: individual × annual cycle. Independence for generalization: biological population and recruitment study, then region. Use whole-source/population holdouts where archive overlap or recruitment links exist. Resampling individual fixes would understate the independent-sample uncertainty.

### Daylength and environmental state

Compute solar geometry from actual date, UTC time, and location. For mobile animals, distinguish astronomical daylength at the used location from the seasonal branch at a fixed study reference latitude. Latitude changes during movement can change experienced daylength; do not label that as a change in the Earth's seasonal branch. Define individual-cycle pairing using increasing/decreasing daylength at that fixed reference, match actual experienced daylength, and keep the distance/latitude difference as part of the ecological record. Analyze cross-hemisphere migrants separately if a single reference cycle is unsuitable.

Within a cycle, match opposite-branch dates using daylight and observation support without reading movement magnitude. Start with a five-minute daylength tolerance and at least 30 days between paired dates; use each day once with a maximum-cardinality, minimum-mismatch assignment. This prevents adjacent near-solstice dates from supplying a nominal opposite-season comparison. Report the supported daylength range; at near-equatorial sites daylength alone provides little separation, making the explicit date/phase separation especially important.

Screen timestamp/cadence/deployment coverage before examining effect signs. The initial support table reports qualifying pairs under 5/10/20 paired-day and 50/75/90% scheduled-fix coverage thresholds. These are design feasibility summaries, not nine alternative hypothesis tests. Select and commit one primary support rule using precision simulations and coverage only, before computing new animal movement effects. Record the final independent population roster and split at that same point. This document is the programme specification, not a claim that this later event-level freeze has already occurred.

Join a versioned temperature series and satellite vegetation product to used locations and dates. For the primary interval prediction, locate environmental predictors at the interval's starting position or a pre-response reference area; do not use a location reached during the movement being predicted. Reserve whole-track experienced conditions for descriptive exposure and the secondary spatial analysis. This prevents the response trajectory from supplying its own predictive features; independent-population holdouts alone would not resolve that problem. Derive daylight-versus-night temperature, vegetation level and growth/senescence phase, with one predeclared contemporary representation and one fixed lag representation. Use environmental data to derive phenophase without fitting to animal response. NDVI is a vegetation index; no direct forage-quality claim follows. Regional air temperature is an exposure proxy; it is not measured body temperature or the animal's selected microclimate.

### Models and an interpretable decision

Use the same outcome, observations, observation model, and temporal resolution for all candidate models:

1. **Solar baseline:** solar phase, photoperiod, taxon and individual/population structure.
2. **Solar + calendar:** the baseline plus annual phase/branch, including known biological season variables when independently supplied.
3. **Solar + calendar + environment:** the same baseline plus the prespecified thermal/vegetation terms and limited guild interactions.

Compare model 3 with model 2 for the central claim. Model 1 describes how much season adds beyond solar geometry but is not the decisive environmental test. Select flexibility only inside training data and compare held-out predictive density/calibration with population weighting. Report effect sizes, uncertainty, heterogeneity, and the populations where the hypothesis fails. A positive mean alone does not justify universality; a failed population does not erase valid estimates in other populations.

Show the predicted ecological contrast in familiar units alongside model scores: change in night-versus-day displacement rate, and separate displacement of daytime movement toward its cooler edges. These are the scientific results the programme seeks; improving camera processing or building a catalog is supporting work.

Camera data use their own effort-aware detection endpoint and model. Agreement of independently measured channels can strengthen interpretation; their numerical values are not interchangeable. Lack of opposite-season support in a camera archive does not block the primary movement analysis.

## 5. Prior work and the intended contribution

Equal-photoperiod seasonal differences are not a new observation: [Daan & Aschoff 1975](https://doi.org/10.1007/BF00345851) explicitly studied them. Solar transformation is also established ([Vazquez et al. 2019](https://doi.org/10.1111/2041-210X.13290)). Broad comparative diel plasticity has a recent large-scale treatment ([Devarajan et al. 2025](https://doi.org/10.1126/sciadv.ado3843)). Resource phenology and spatial movement tactics already have cross-population tests ([Aikens et al. 2020](https://doi.org/10.1016/j.cub.2020.06.032)). Recent biologging studies also analyze temperature, vegetation, and daily or seasonal activity ([2025 antelope study](https://doi.org/10.1186/s40462-025-00604-y); [2021 ibex study](https://doi.org/10.1111/ele.13750)).

The intended contribution combines an explicitly enumerated public-source cohort, repeated-individual opposite-season contrasts, experienced environmental state, and independent-population prediction. The empirical question is whether the environmental explanation survives changes in how calendar season maps to actual conditions. This is a proposed contribution to establish with data; this source review does not justify a claim of being the first study.

## 6. Work completed and next concrete analysis

Completed in this revision: central hypothesis, competing explanations, predictions, database units, the 437-package Movebank discovery snapshot, and the 26-record GBIF Camtrap DP snapshot, with source receipts and reproducible catalog preparation. No new animal-effect estimates are claimed.

The next analysis begins by resolving native file inventories for the frozen registry and constructing an individual × deployment × cadence coverage table. This establishes the actual mammal cohort and independent population split, after which the predeclared displacement/environment analysis can run. Acquisition follows the registry rather than selecting another paper with an attractive positive result. A public database article may later describe the resource, but the first scientific target remains the ecological prediction above.
