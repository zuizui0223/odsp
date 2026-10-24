# Cross-taxon biological generality — current state

## 2026-10-24 French wild *Gyps fulvus*: non-independent native height sensors and source-tag QA in progress

Original frozen native GPS and barometric height D1 source [run 39716885648](https://github.com/zuizui0223/odsp/actions/runs/39716885648): 27 scored wild-vulture bird IDs, 5,205 matched target bird-days, GPS mean gain +0.0407134 and barometric mean gain +0.0414526 nats/record, both 999/999 valid and Holm p=.002. The **two heights are on the same bird/tag/UTC GPS events**, not independent biological replications.

**New verified post-outcome instrument audit** [run 40057167210](https://github.com/zuizui0223/odsp/actions/runs/40057167210): original 27 scored birds, 26 have positive raw D1 height-identity gain under BOTH GPS and pressure-derived height. Bird-level gain ranks Spearman **rho=.9823**, 5,000 bird-resample 95% range **[.9275,.9957]**. The 5,854 jointly complete 28-bird source days show same-fix GPS vs barometric height Pearson median **.9246**, while the median of bird-day median ABSOLUTE *daily-median-centered* height discrepancies is **33 meters** (bird-cluster CI 31.25–35.5m). Thus the two native numerical height series are nonidentical, yet individual label scores align closely. Device/pressure-height calibration independence is **NOT proven**; within-cell topography, tag-ID and flight-state confounds remain. Source's original 999 GPS and barometric null CSVs were independently recalculated and unchanged.

**Critical source-quality caveat from Oct22/23 outcome-blind QA:** Original GPS source has the nonbiological label `Test géodésie ornitela` and one native tag `182208` mapped to TWO separate bird IDs (Peycare and Mostuéjouls). The geodesy test is absent from the original 5km eligible birds. **Mostuéjouls was scored in the original 27-bird native height study; Peycare was not.** Therefore the original 27-bird Holm p=.002 must **NOT** be represented as the re-fitted, tag-quarantined 26-bird result. Source-only clean eligible 5km roster after excluding both tag IDs and test is **27 birds**, SHA256 `d9feed17cd780ed1be1c5fcd275471a0f741dfa565aa5995cbd7d71841ded34c`; original 27 scored birds overlap this roster in **26** literal IDs.

**Exact-model source-QA sensitivity code and noheight 27-ID frozen contract** are committed in [diagnostic/france-gyps-clean-dual-height-20261024](https://github.com/zuizui0223/odsp/tree/diagnostic/france-gyps-clean-dual-height-20261024). GitHub Actions [40058052115](https://github.com/zuizui0223/odsp/actions/runs/40058052115) performs full refitting of the original unchanged 5km/ten-category/day-balanced own-vs-other D1 model and both original 999 label shuffles after removing these source labels, never subtracting a single bird score without recalculating donors. Initial monolithic source download failed 7 times near EOF (curl error 18); repaired transport uses original publicly verified HTTP 206 byte-range downloads, full published source MD5 unchanged. **No clean-numeric new result is claimed until that run completes successfully.** The first (source-only) root cohort correction itself is verified [run 39720327589](https://github.com/zuizui0223/odsp/actions/runs/39720327589).

Separate French 2019–21 regional CERRA wind source failed its prespecified weather-calendar floor: 912 valid days vs 1050 required because 2021 Jul–Dec were missing. Treat as **meteorological-source unavailable**, not biological no-wind-effect ([source receipt](https://github.com/zuizui0223/odsp/blob/prospective/france-griffon-5km-regionalwind-20261022/prospective/FRANCE_GYPS_CERRA_2019_2021_UNAVAILABLE_SOURCE_RECEIPT_V1.json)).

[Instrument audit math and ecological caveats](https://github.com/zuizui0223/odsp/blob/diagnostic/france-gyps-two-height-measurement-audit-20261024/prospective/FRANCE_GYPS_TWO_HEIGHT_MEASUREMENT_BIOLOGICAL_INTERPRETATION_V1.md) · [source machine-readable instrument QA receipt](https://github.com/zuizui0223/odsp/blob/diagnostic/france-gyps-two-height-measurement-audit-20261024/prospective/FRANCE_GYPS_2019_2021_TWO_HEIGHT_DEPENDENCE_RESULT_RECEIPT_V1.json).

---

## 2026-10-22 French wild *Gyps fulvus*: distinct tracker source, two height measurements, and corrected source metadata

New wild-vulture GPS source: Sassi et al. (2024) Dataverse [10.48579/PRO/IOSZNM](https://doi.org/10.48579/PRO/IOSZNM), public original 2019–2021 tracker ZIP 1,093,170,227 bytes (MD5 `b18cc8004d311d19ff24060f655178bf`), containing 9 native seasonal GPS tables with GPS elevation, barometric elevation, GPS HDOP and satellite-count metadata. Official ZIP/header workflow [39713936597](https://github.com/zuizui0223/odsp/actions/runs/39713936597). Study names differ from the previous 2026 Scacco `Gyps fulvus` parent studies 122120597 (*Griffon vulture - Bardenas Reales*) and 44080734 (*Scavengers and wild ungulates*). The original 30 French source ID strings show **zero exact animal-ID overlap** with both; numeric French Movebank parent ID, physical device independence and aliases cannot yet be fully excluded ([crosswalk 39715960239](https://github.com/zuizui0223/odsp/actions/runs/39715960239)).

Earlier, a separately frozen **dual GPS and barometric native-height D1 identity test** [39716885648](https://github.com/zuizui0223/odsp/actions/runs/39716885648) admitted 27 biological bird IDs, 5,205 matched scored bird-days, same original target times for both altitude sensors; raw mean individual shape gains GPS **+0.0407134** and BARO **+0.0414526**, 999/999 valid nulls each, Holm p **0.002** each. This supports original **bird-labelled repeated vertical shape** in the new French study. It does **not** test bird-specific wind reaction, prove independent devices, or identify behavior apart from devices/terrain; the two height series may share calibrations.

**Important outcome-blind source QA correction after the historical run:** original source counted 30 labelled bird IDs, but one literal source ID is a **nonbiological instrument-geodesy test** (`Test géodésie ornitela`). The QA-only rescan [39720327589](https://github.com/zuizui0223/odsp/actions/runs/39720327589) excluded this test before any new altitude or wind analysis: 29 wild source ID candidates, 742,078 first 5min GPS events, 5km **28 birds** and 50km **28 birds**. The original 5km bird roster SHA is **unchanged** (`031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928`), but its scorable events shift 608,202→608,109 and bird-days 12,360→12,357 because a few original source control fixes relied on the test record. **One native GPS tag `182208` is mapped to two different birds** (Peycare vs Mostuéjouls); one of those IDs, Mostuéjouls, was in the historical 27-bird dual-height result. Thus the historical 27-bird inference is **NOT independently recomputed for the clean source/tag-quarantined cohort**; do not mislabel its p values as a clean 26-bird test.

**New fixed goal — source-level regional wind eligibility only:** [France-CERRA 2019–2021 5km source contract](https://github.com/zuizui0223/odsp/blob/prospective/france-griffon-5km-regionalwind-20261022/prospective/FRANCE_GYPS_2019_2021_CERRA_5KM_WIND_CONTEXT_GATE_V1.json). A new branch excludes the instrumental test and both native tag-alias bird IDs, then joins independent 5km CERRA wind at published Grands Causses Cassagne site (44.20N,3.25E). Wind high/low is fixed by year-month ALL-calendar-day 24h mean 100m wind Q25/Q75, without using GPS heights. Eligibility asks at least 10 birds to have ≥2 different low days and high days in the SAME 5km cells, own other-day same-state and opposite-state donor fixes ≥10 each, and ≥2 other biological birds in same cell/year-month with both wind regimes for the population-wide shared response. The source wind eligibility is **NOT** an unobserved new biological effect. If inadequate, report unavailable; do not relax primary 5km grain, environmental boundaries or sample rules.

Previous 2026 Scacco *Gyps* 4 panels are separate evidence of Wstar-conditional prediction but show no supported individual reaction above shared-species response. The new French parent is a candidate for observing this missing higher-order phenomenon, but even a positive postheight result cannot establish causal wind flow at each bird's flight position or fully independent data-device provenance.

- [Original French source 5km GPS/baro result](https://github.com/zuizui0223/odsp/actions/runs/39716885648)
- [Fixed source test-tag corrections](https://github.com/zuizui0223/odsp/blob/prospective/france-griffon-5km-regionalwind-20261022/prospective/FRANCE_GYPS_2019_2021_SOURCE_NONBIRD_AND_TAG_ALIAS_QA_RECEIPT_V1.json)
- [New separate CERRA 5km source gate](https://github.com/zuizui0223/odsp/actions/runs/39721641241)

---

## 2026-10-21 mechanism diagnostic: shared species thermal response versus bird-specific Wstar conditioning

The earlier 38-taxon source screen still contains just **four source-specific Gyps study×species panels**, 2 positive source panels of **the same species Gyps fulvus**, one non-supported species panel and one unavailable panel. This does **not** establish three-taxon thermal reaction universality.

A **POST-OUTCOME exploratory mechanistic comparison**, explicitly excluded from confirmatory replication, was frozen as [contract](https://github.com/zuizui0223/odsp/blob/diagnostic/gyps-common-vs-individual-thermal-20261021/prospective/GYPS_SHARED_VS_INDIVIDUAL_WSTAR_MECHANISM_PLAN_V1.json) and fully run as [GitHub Actions 39598530973](https://github.com/zuizui0223/odsp/actions/runs/39598530973). It compared (A) each bird's own Wstar-conditioned centered altitude distribution, versus (B) its own Wstar-pooled shape *adjusted by species-wide thermal-response odds learned from other birds at the same original 50-km cell and YYYY-MM*, leaving out the whole target UTC day and focal bird. Same original study-species IDs, GPS source, category edges, Wstar thresholds, source-quality support and 999 bird×month whole-session shuffles. Original four-panel tests and their supported/non-supported/unavailable conclusions **unchanged**.

| Original study / species | Same GPS target birds in common-response diagnostic | Days | Additional bird-specific vs shared Wstar raw gain | Observed−null mean | Valid null | Exploratory Holm p | Boundary |
|---|---:|---:|---:|---:|---:|---:|---|
| 122120597 / *Gyps fulvus* | 24 | 688 | +0.000035 | **−0.014031** | 999/999 | 1.000 | No extra bird-specific gain supported |
| 44080734 / *Gyps fulvus* | 24 | 1194 | +0.028133 | +0.007626 | 999/999 | 0.268 | Positive raw direction, not supported after exchange/multiplicity |
| 352166254 / *Gyps africanus* | 0 | 0 | unavailable | unavailable | not run | 1 placeholder | Too few OTHER birds from both Wstar states in same month-cell |
| 972560688 / *Gyps coprotheres* | 8 | 144 | +0.01024 descriptive | unavailable | not run | 1 placeholder | Below fixed 10-bird matching gate |

**New cautious biological conclusion:** Current source data support *environment-dependent prediction of individual vertical-use shape* in *G. fulvus* in two source studies; they do **not** demonstrate that Wstar reaction norms are inherently different for each bird beyond a shared species thermal response. Source 122120597 observed eligible birds 24 vs null 14–23 — permutation eligibility changes, so nominal negative p cannot prove ecological absence. A truly independently recorded animal×thermal×flight-state source with known height calibration is required.

- [Post-outcome ecological and mathematical synthesis](https://github.com/zuizui0223/odsp/blob/diagnostic/gyps-common-vs-individual-thermal-20261021/prospective/GYPS_SHARED_VS_INDIVIDUAL_WSTAR_BIOLOGICAL_SYNTHESIS_V1.md)
- [Full exact result evidence receipt](https://github.com/zuizui0223/odsp/blob/diagnostic/gyps-common-vs-individual-thermal-20261021/prospective/GYPS_SHARED_VS_INDIVIDUAL_WSTAR_DIAGNOSTIC_RESULT_RECEIPT_V1.json)
- [New external source access and nonduplication audit](https://github.com/zuizui0223/odsp/blob/diagnostic/gyps-common-vs-individual-thermal-20261021/prospective/INDEPENDENT_CROSS_TAXON_SOURCE_ACCESS_GATE_20261021.md) — Dryad crane GPS requires OAuth in current access, other publicly archived Gyps candidate has only 2 and 3 tracked birds per species.

**Next prospective ecology:** replicate in untouched flight source, with population-shared environmental context as baseline and independently identified behaviour/terrain/calibrated altitude as negative controls. Do not change the original 4-study evidence ledger or treat diagnostic p as a new biological replication.

---

## 2026-10-21 newest: thermal-updraft context and individual height-shape prediction across a 38-taxon source database

The new, version-locked source is [Scacco et al. 2026, Zenodo 10.5281/zenodo.21915776](https://zenodo.org/records/21915776) (CC BY 4.0; Data.zip MD5 e1f116e6576cf20e54dad16d2c91a26d). It contains 38 bird/bat taxa and 853 tracked animals, but these are **source-universe counts**, not 38 positive independent species. The source already contains author-derived flapping, transport-cost, ERA5 wind/uplift annotations; our NEW endpoint is held-out daily-median-centered *GPS altitude distribution shape*, distinct from the original paper's cost-of-transport analyses.

**Prospective sample pathway:** source archive manifest [39543940270](https://github.com/zuizui0223/odsp/actions/runs/39543940270); 72 study×species metadata panels ->16 first-stage panels across 11 species [39544432716](https://github.com/zuizui0223/odsp/actions/runs/39544432716); 1.524 million per-point GPS x-y/Wstar/flapping records outcome-blind scanned [39545718549](https://github.com/zuizui0223/odsp/actions/runs/39545718549): **2 studies** with ordinary 5-km individual-ID support, **zero** with strong/weak Wstar contextual support at 5km, and **four Gyps study×species panels across three species** eligible at the separately frozen 50-km grain. Frozen before opening native GPS heights were source study IDs 122120597, 352166254, 44080734, 972560688; 50-km regime-eligible birds **25/11/26/14**.

**Predeclared 4-study native-height test** used one biological bird as the unit, the same study/bird/cell with other-day low/high Wstar donor profiles, 999 whole bird-day Wstar label shuffles WITHIN bird×year-month, and Holm across all four studies including unavailable placeholders p=1. The original run [39593226775](https://github.com/zuizui0223/odsp/actions/runs/39593226775) and Holm-display-corrected FULL source rerun [39594223949](https://github.com/zuizui0223/odsp/actions/runs/39594223949) reproduced all four source Wstar-null CSVs BYTE-IDENTICALLY; corrected artifact 12343146957 / ZIP SHA256 e54a722ea28cb936217699885853b3fa87ccd5b3341bb9e865acd68ba6bef29c.

| Taxon / study | Birds | Bird-days | GPS fixes | Raw contextual gain (nats/fix) | Observed − null mean | Permutation draws valid | Final Holm p | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| *Gyps fulvus* / 122120597 | 25 | 1610 | 50,981 | +0.005871 | **+0.015539** | 999/999 | **0.004** | **SUPPORTED** |
| *Gyps fulvus* / 44080734 | 26 | 2621 | 97,740 | +0.015439 | **+0.017185** | 999/999 | **0.004** | **SUPPORTED** |
| *Gyps africanus* / 352166254 | 11 | 960 | 26,385 | −0.012436 | +0.012378 (descriptive) | 845/999 | **1.000 placeholder** | **UNAVAILABLE, not negative** |
| *Gyps coprotheres* / 972560688 | 14 | 882 | 25,130 | −0.032347 | +0.014800 | 990/999 | 0.146 | **NOT SUPPORTED** |

Native GPS altitude quality exceeded 99.97% in all four, and all archived source height entries in the four study panels are ellipsoid heights, not terrain-relative AGL. The unavailable *G. africanus* panel failed the planned minimum 950 valid null shuffles (only 845), not the original native height QC. The observed 4-panel sample is 76 birds, 6,073 bird-days and 200,236 GPS records; don't treat individual fixes as independent tests.

**Biological interpretation:** Under broad ERA5 updraft context, individual GPS vertical shape shows extra day-heldout predictability in **two tracking studies of *G. fulvus***. It is not supported as a universal property of three vulture species, all soaring birds, or bats. More importantly, this **does not identify individual-specific wind reaction norms**: a response shared by all birds can make per-bird Wstar-conditioned profiles predictive. Route/terrain, behavioural flapping mixture, source tag-altitude errors and day-shared weather remain possible mechanisms. Historical *mina* penguin monitored breeding-area concentration is a DISTINCT population-level endpoint, not part of this bird flight effect.

**Durable documents:**
- [Full 4-study ecological interpretation](https://github.com/zuizui0223/odsp/blob/prospective/gyps-thermal-50km-20261021/prospective/GYPS_4_STUDIES_WSTAR_VERTICAL_BIOLOGICAL_SYNTHESIS_V1.md)
- [Complete evidence and source-bounded numeric receipt](https://github.com/zuizui0223/odsp/blob/prospective/gyps-thermal-50km-20261021/prospective/GYPS_50KM_WSTAR_4STUDIES_RESULT_EVIDENCE_RECEIPT_V1.json)
- [Source-bounded preheight contract](https://github.com/zuizui0223/odsp/blob/prospective/gyps-thermal-50km-20261021/prospective/GYPS_50KM_WSTAR_CONTEXT_TEST_FREEZE_V1.json)

**Next honest test:** shared-species-wide thermal response against bird-specific thermal reaction, holding fine horizontal location and independently classified flight state constant in NEW prospective independent studies. Do not reopen these 4 outcomes and tune Wstar bins/grain to rescue unsupported species.

---

## 2026-10-21 outcome: repeated fine horizontal flight corridors versus repeated vertical shapes

A new post-outcome exploratory reanalysis compared the **same 25 Rotics 2013 storks and 11 Flack 2014 storks** as the archived 50-km height studies, reading only source GPS x-y/time/identity/speed, without opening altitude values. Source-eligible biological bird lists and 50km bird-day counts were byte-fingerprint checked before any link to frozen per-bird height scores.

**Reference correction was essential.** The initial raw x-y diagnostic compared one focal bird's 5km subcell revisit to an *ANY-of-many OTHER birds* union; its other-fix matches (~70.8%, ~75.0%) were inflated by the number of birds. The corrected metric uses one uniformly weighted, eligible OTHER bird observed in the same 50-km coarse cell on another date.

| Fine 5-km revisit INSIDE qualified 50-km cells | Rotics 2013 | Flack 2014 |
|---|---:|---:|
| Focal bird repeats fine subcell on another UTC day | 54.88% | 47.09% |
| One equally weighted other bird does so | 24.93% | 29.18% |
| **Focal − single other bird** | **+29.96 pp** | **+17.91 pp** |
| Previously frozen centered-height bird-identity signal | positive, p=.001 | unsupported, p=.998 |

The 2013 minus 2014 bird-equal fine-route advantage difference is about **12.04 pp**, but an exploratory 5000 bird-bootstrap 95% interval **−1.07 to +25.32 pp includes 0**. Do not claim a significant between-cohort ecological effect.

The equal-other reference's bird-level geographic advantage is positively rank-associated with previously fixed bird height ID scores in the 2013 cohort (Spearman **rho +0.398**, bird bootstrap95 **+0.065 to +0.626**, exploratory age-block label p **0.0426**). The 2014 cohort gives rho **+0.527** but bird bootstrap95 **−0.256 to +1.0** and exploratory label p **0.0953** (11 birds), so there is **no replicated statistically secure rank association**. Both effects are POST-OUTCOME exploratory; do not promote p values as prespecified mechanism evidence. Other bird tracks may have differing GPS effort, so reference correction is not perfect donor-matched calibration.

**Key biological boundary:** Cross-day fine horizontal route reuse is present in both migration studies, yet fixed individual vertical shape identity is supported in only one. Thus route recurrence alone does not guarantee temporal recurrence of the altitude distribution; atmospheric opportunity, travel stage, nestling experience, terrain, sampling support and tag errors remain competing, **untested causal** mechanisms.

[Corrected mechanistic synthesis](https://github.com/zuizui0223/odsp/blob/diagnostic/stork-fine-route-equal-bird-20261021/prospective/STORK_ROUTE_VS_VERTICAL_INDIVIDUALITY_BIOLOGICAL_SYNTHESIS_V1.md) · [machine-readable result and source audit](https://github.com/zuizui0223/odsp/blob/diagnostic/stork-fine-route-equal-bird-20261021/prospective/STORK_EQUAL_OTHER_BIRD_CORRECTION_RESULT_RECEIPT_V1.json) · [source run](https://github.com/zuizui0223/odsp/actions/runs/39530359254).

**Next legitimate scientific test:** In a new independent tracking source, compare date-heldout `P(relative altitude | fine GPS location, date/airmass wind & uplift, flight behavior)` with the addition of animal ID and then animal×weather interaction. Freeze matching/quality/thresholds before opening that source's height values. Do not re-mine the opened 2013/2014 height data in search of a preferred conclusion.

---

## Latest boundary: independent stork cohorts do not show uniform vertical-shape individuality

The original Rotics 2013 migration-specific 50km test (Movebank study 150450794) showed an age/date-block null-relative gain +0.194850 nats/event (25 birds, 111 bird-days, 6,951 scored fixes, p_upper=0.001; archived run 39409175819). A deterministic rerun (39413456822) exactly reproduced all original JSON and CSV evidence members byte-for-byte.

A **different 2014 white-stork study** (Flack / Weinzierl, Movebank study 332044860, DOI 10.5441/001/1.bj96m274) was admitted before opening heights: 60 source reference birds (all labelled nestling), 59 birds with selected flight-speed GPS records, 50km comparable source roster **11 birds / 33 bird-days / 2,040 bins**, while 5km has **zero**; source preheight run [39415189033](https://github.com/zuizui0223/odsp/actions/runs/39415189033).

Its numerically identical, separately preregistered 50km D1-balanced centered-height-shape / 999 exact-date-stage session exchangeability test returned **NOT SUPPORTED** [run 39416255916](https://github.com/zuizui0223/odsp/actions/runs/39416255916): 11 birds, 33 bird-days, 2,039 scored GPS fixes, observed gain **−0.26989281**, null mean **−0.13523669**, observed-minus-null **−0.13465612**, all 999 null valid, one-sided p_upper **0.998**. Only **2 of 11** individual raw scores were positive. Native altitude completeness 58,959/58,971 = 99.980%.

Source reference animal IDs: 2013 122 and 2014 60 with **zero exact animal-ID overlap**. One GPS tag ID occurs in both full source reference archives, used on distinct birds in 2013/14, and is not among the 2014 final 11 birds. The two source populations are independently tagged at the literal tracked-bird ID level, but this is not a controlled experiment of cohort biology.

**Interpretation:** The original positive evidence in a mixed-age eastern-Germany migration cohort is not uniformly reproduced in an independent all-nestling southwestern-Germany tracking cohort under the same 50km test. Positive p=.001 vs p=.998 is not a formal significant cohort-by-context interaction. The latter is an unsupported positive hypothesis, **not proof of biological zero**: n=11 and 33 observed sessions, cohort/stage/site/tag differences, unadjusted topography and identification-via-tag limitations remain. Both null randomizations change the eligible-bird denominator (2013 observed25 vs null36–53, 2014 observed11 vs null13–28), limiting exchangeability interpretation.

**Ecological question newly sharpened:** What ecological conditions make individual vertical-use shape recur across days? Stable vs changing flight opportunities, wind and thermal uplift, juvenile experience, behavioural mode and geographic migration stage are candidates, not supported causal explanations. Gull 2016/2017 provides independent *regional wind predictive context* but does not prove individual-specific wind response. Do not reopen either stork archive with outcome-tuned alternative spatial grains to rescue the 2014 result.

Durable evidence:
- [Two-cohort biological synthesis](https://github.com/zuizui0223/odsp/blob/prospective/stork2014-independent-cohort-20261020/prospective/WHITE_STORK_2013_2014_CROSS_COHORT_BIOLOGICAL_SYNTHESIS_V1.md)
- [2013 source result receipt](https://github.com/zuizui0223/odsp/blob/prospective/stork2013-50km-vertical-identity-20261020/prospective/WHITE_STORK_2013_50KM_RESULT_EVIDENCE_RECEIPT_V1.json)
- [2014 source result receipt](https://github.com/zuizui0223/odsp/blob/prospective/stork2014-independent-cohort-20261020/prospective/FLACK_STORK_2014_50KM_RESULT_EVIDENCE_RECEIPT_V1.json)
- [Cross-guild claim map](https://github.com/zuizui0223/odsp/blob/prospective/biological-generality-20261019/prospective/CROSS_GUILD_VERTICAL_PROBABILITY_SYNTHESIS_V1.md)

---

## Latest evidence: wind-conditioned vertical shape recurs in two breeding years

The cross-taxon biological-generalization lane advanced from the previous 2021 DELTATRACK individual identity experiment to **two fixed yearly tests of environmental context**, in the distinct `LBBG_ZEEBRUGGE` Movebank tracking study (one species, `Larus fuscus`). Source 2016 and 2017 native GPS, CERRA regional 100m winds at four archival colony centers, exact-identifier site join, and all altitude-blind support screens were independently anchored before opening each year's height outcomes.

| Breeding year | Original altitude-blind wind candidates | Scored birds | Bird-days | GPS fixes | Wind-conditioned vs pooled raw gain | Mean null | Null-calibrated excess | p-upper |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2016 | 41 | 39 | 744 | 31,002 | +0.0110375 | −0.0234812 | **+0.0345187** | **0.001** |
| 2017 | 25 | 24 | 422 | 18,348 | +0.0217185 | −0.0210897 | **+0.0428082** | **0.001** |

Both years used the same frozen numerical algorithm: within-individual, same 5-km horizontal cell, different-day ten-bin height-shape distributions centered by each day's median; compare conditional same-regional-wind group vs wind-pooled reference on identical held-out GPS fixes. Within-grid and month whole-wind-day permutations (999 each) yielded **999/999 valid** and 0 null observations at least as high. Count bird-level, not GPS fixes, as biological replication; site/date null exchangeability remains observational.

The 39 and 24 birds share **11 exact animal IDs**. Unique union **52 birds** across both years. Individual-level raw gain is positive in 27/39 (2016) and 18/24 (2017); among the 11 reappearing birds, 7 have positive gains in both years. The year-specific raw gain rank of an individual is **not established** as stable across years (the shared 11 show only weak descriptive alignment). No combined or meta-analytic p value is calculated because same study sites, tags and partly the same birds.

**Biological statement:** This provides one species / one Movebank study / two consecutive years of evidence that the shape of individual-level vertical flight-use probabilities is **environment-context dependent rather than fully fixed by identity alone**. It does not establish causal wind-driven flight decisions; source wind is a regional 100m site measure, not actual 3D air flow at each GPS location. Speed-based filtering does not validate flapping or soaring, and tag-specific non-additive altitude noise remains unresolved. Penguin colony-count concentration in MINA remains a separate population-level endpoint.

**Auditable evidence:**
- [2016 biological result](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_BIOLOGICAL_RESULT_V1.md) — run [39401802547](https://github.com/zuizui0223/odsp/actions/runs/39401802547).
- [2017 temporal validation receipt](https://github.com/zuizui0223/odsp/blob/prospective/zeebrugge-2017-temporal-wind-test-20261020/prospective/ZEEBRUGGE_2017_CERRA_WIND_RESULT_RECEIPT_V1.json) — preregistered preheight run [39403638754](https://github.com/zuizui0223/odsp/actions/runs/39403638754), full test [39404195393](https://github.com/zuizui0223/odsp/actions/runs/39404195393).
- [Two-year ecological synthesis](https://github.com/zuizui0223/odsp/blob/prospective/zeebrugge-2017-temporal-wind-test-20261020/prospective/ZEEBRUGGE_2016_2017_WIND_HEIGHT_BIOLOGICAL_SYNTHESIS_V1.md).

**Next unique goal:** move beyond this single species/network. Prefer an independent taxon/study with externally derived flight/dive behavior and/or device-calibrated vertical state, prespecifying the identical conditional-probability transfer question. Do not continue source/year mining to amplify p values.

---

## New independent ecological context result: 2016 regional wind and height shape

A new, separately checksum-pinned `LBBG_ZEEBRUGGE` GPS source (2016) was joined to independently obtained 100m CERRA wind at four source-defined colony centers **before inspecting GPS heights**. Outcome-blind screening run 39391834277 passed 41 candidate birds. The frozen within-bird, same-5km-cell, held-out-day wind-context analysis run [39401802547](https://github.com/zuizui0223/odsp/actions/runs/39401802547) completed successfully.

- **Larus fuscus: 39 qualifying individuals, 744 bird-days, 31,002 target flight-height fixes.** Altitude quality 133,497/133,693 = 99.853%.
- Conditional same-individual/same-cell wind-regime shape vs that individual's wind-pooled profile: observed gain +0.01103752 nats/fix.
- Wind-regime date permutations within CERRA grid and month (999/999 valid): null mean −0.02348120, **observed minus null +0.03451872**, one-sided Monte Carlo **p=0.001**.
- Bird-level raw gain is positive in 27/39 birds. A **post-outcome descriptive** site join finds mean gain positive in all four colony groups (n=3, 8, 7, 21), but site-specific effects are not separate independent tests.
- Core ecological contribution: **A particular individual's vertical-use probability shape carries additional environmental context**; it need not be a single invariant shape. The wind regimen used here is regional colony-site weather, not personally experienced flight air-flow.
- Limits: observational association, no causal wind attribution, same-bird device error, within-cell micro-paths, accelerometer-defined flight mode missing for this archive, site-month/date exchangeability assumption. This is a new individual shape estimand, distinct from published studies of wind-linked habitat selection or flapping/soaring rates.

Auditable result and biological interpretation:
- [Wind-height outcome report](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_BIOLOGICAL_RESULT_V1.md).
- [Machine-readable result receipt](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_RESULT_RECEIPT_V1.json).
- [Frozen model](https://github.com/zuizui0223/odsp/blob/prospective/gull-wind-behaviour-context-20261020/prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_TEST_FREEZE_V1.json).

**Next independent-horizon question:** does this wind-context shape information transfer to the next consecutive archive year (2017) under a new year-level freeze, while explicitly accounting for shared individual tags and site/weather correlation? Do not try to improve 2016 p values by searching alternative weather grids, bin cutoffs or seasons.

---

## Latest completed next-step: matched flight–stationary individual comparison

A further **post-outcome exploratory** test has now linked the exact same birds' frozen flight (5-km) and low-speed 100-m individual ID score gains. It did **not** alter either original endpoint or re-run a new independent taxon replication.

- [Matched context workflow 39383667556](https://github.com/zuizui0223/odsp/actions/runs/39383667556): completed successfully; archived evidence artifact 12247305470 (ZIP SHA256 8f304f4709f9ae27ae49af5dbfbbc2c917a914efd7db622b9fee6780d76381bf).
- **33 birds** overlap the originally eligible flight (40) and stationary (46) sets. In these 33, flight raw bird scores are positive for 30 and stationary raw bird scores for 20.
- Rank concordance of bird-level raw gains across contexts is **weak**: Spearman rho **+0.10227**; 9,999 matched-bird random permutations, two-sided p **0.5672**; bird-level bootstrap 95% interval **−0.2641 to +0.4256**. An independent scipy calculation agrees (rho=0.10227).
- Original stationary 46 birds/590 bird-days/51,960 fixes/mean score +0.008155 was reproduced to machine precision; original flight numerical model/results were imported by pinned SHA256 without refitting. New synthetic tests passed.
- Raw gain levels are **not directly biologically comparable across 5-km flight and 100-m slow-motion contexts**. The two contexts' effects have descriptive associations with their own number of scored bird days (flight rho≈0.331, stationary rho≈0.433), so effort-related heterogeneity remains.
- **Interpretation:** a single shared bird/tag-related *ranked* propensity across both contexts has no positive empirical support here, but the broad confidence interval and context-dependent measurement errors prohibit claiming that the flight signal is free of instrument error. Both contexts separately retain ID-associated distributions; the 2021 bird-to-tag aliasing is still perfect.
- Cross-context correlation is exploratory and cannot identify the biological or instrumental fraction; not a second external replication, not a universal flying-animal law, and not directly comparable to MINA's penguin breeding-site concentration.

Durable report: [Flight–stationary matched synthesis](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-matched-context-20261020/prospective/DELTATRACK_2021_FLIGHT_STATIONARY_SYNTHESIS_V1.md).

Machine-readable receipt: [33-bird result ledger](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-matched-context-20261020/prospective/DELTATRACK_2021_MATCHED_CONTEXT_RESULT_RECEIPT_V1.json).

**Next scientific boundary:** An independent, non-constant vertical instrument or actual within-bird tag switch (or validated behavioural states/known perch microtopography) is required. Repeatedly reshaping this already opened source would not solve the causal identity problem.

---

Updated 2026-10-20. Latest completed step: a prospectively fixed external tracking-study test in DELTATRACK 2021. Prior MEDGULL exploratory results and unavailable original endpoints remain unchanged.

## Latest external-study result

Branch: `prospective/deltatrack-2021-identity-20261020`.

Using the unchanged MEDGULL D1 balanced estimator, **Larus fuscus: 40 individuals, 899 bird-days and 66,811 scored five-minute flight records** retain individual-label-associated cross-day centered altitude shape beyond exact-date session relabeling.

- Observed mean log-score gain: +0.0456739261.
- Null mean: -0.0278862764.
- Observed minus null: +0.0735602025 nats/record.
- 999/999 valid permutations; none at least as large as observed.
- One-sided Monte Carlo p=0.001; Holm p=0.002 across the TWO prespecified species.
- 37/40 positive individual point scores, not 37 significant individual tests.
- Null eligible birds 49–59 versus observed 40; full support re-estimation and this difference are retained.

Larus argentatus: 14 individuals had valid flight heights but only 1 individual / 7 bird-days / 449 records passed the full comparison support. Its endpoint is **unavailable**, not a negative biological result. It stays in the multiplicity family with placeholder p=1; no biological p-value is reported.

The dataset is an external study relative to MEDGULL, not an independent study for each DELTATRACK year. The two species share site/instrument context. The supported external result is one species, not two successful independent species.

## Frozen design and execution

Source DOI 10.5281/zenodo.22102508; DELTATRACK-gps-2021.csv.gz; MD5 1a3145234cccd1a48b280b0fb485d679. Target two-species raw count 3,637,037; valid thinned height count 216,407.

Plan saved before this 2021 height analysis: commit abd6416013cf8aedf0acff9b91782964ce947228. Successful run 39375585874, execution commit 089194d368ca43554d3ea681d008d01e5ce51008, artifact 12242743398.

First attempt failed at Numba cache loading after parsing heights but before emitting an identity statistic. The error was reproduced with synthetic data; only the production cache directory was separated. No year, model, threshold, seed, source or numerical kernel changed.

Durable report and receipt on the external-test branch:
- prospective/DELTATRACK_2021_IDENTITY_REPORT_V1.md
- prospective/DELTATRACK_2021_IDENTITY_RECEIPT_V1.json
- prospective/DELTATRACK_2021_IDENTITY_PLAN_V1.md
- prospective/DELTATRACK_2021_RUNTIME_RECOVERY_V1.json
- prospective/deltatrack_2021_identity.py
- prospective/test_deltatrack_2021_identity.py

The complete result JSON, all 999 null draws, all per-bird comparisons and executable code are saved in the verified run artifact and the conversation reproducibility package.

## Interpretation and remaining scientific boundary

Evidence now extends from the post-outcome MEDGULL discovery to a pre-specified test in a different gull study/species. The safest claim concerns **individual-label-associated vertical-use shape**, not biological personality or adaptive specialization free from instrumentation.

Tag-specific non-additive altitude errors, effort, unobserved behavioral mixtures, within-cell routes and the substantive exact-date exchangeability assumption remain limitations. Day medians use the heldout session itself; this is shape matching, not online absolute-height prediction. Do not compare raw calibrated-score magnitudes as directly comparable biological strengths across datasets.

No inference of resource partitioning, central-place causation or universal mammal–bird equivalence. MINA penguin breeding-component concentration is a different response variable; do not combine the two into one demonstrated law.

Next scientific boundary: measurement/context attribution and extension beyond a narrow colonial-flying comparison. Do not continue changing thresholds on already-viewed MEDGULL or treat the excluded L. argentatus panel as a biological negative.

## Preserved MEDGULL sensitivity

Branch sensitivity/medgull-donor-days-20261020. MEDGULL 2022 I. melanocephalus: 11 birds, 258 bird-days, 17,054 records under D1. D1 pooled observed -0.0296285 vs null -0.0945509; D1 balanced +0.0362684 vs null -0.0167478. Both Holm p=0.002 across those two exploratory comparisons. This remains post-outcome sensitivity, not an independent confirmation. Balanced uses different smoothing level as well as weighting.

Original D50 pooled reproduced: 9 birds, 241 days, 15,904 records, gain -0.014494591842618162. Its original minimum-10 primary stays closed as unavailable.

## Preserved structural diagnosis

MEDGULL 13 -> 11 after correcting the individual/cell Counter key; 11 -> 11 after same-date exclusion; 11 -> 9 after removing short donor days. Earlier attribution solely to same-date exclusion was wrong.

DELTATRACK 2020 stays below its original minimum-10 rule: L. argentatus 6, L. fuscus 9. Its code did not have the Counter-key defect. Schiermonnikoog 2018 had 6 correct shared-cell candidates, 4 after short-donor-day removal. These are support findings, not ecological negatives.

## Verification closeout

New and reused module tests: 15 passed, 1 optional source integration test skipped. Independent dictionary reference agrees in 96 irregular synthetic cases; max score difference 6.67e-16. Saved real-data individual aggregates, full null means/tail counts/p values and Holm adjustment rechecked independently; artifact file hashes verified.

Full default repository suite rerun in 39374955129: 1,514 passed, 2 failed, 1 skipped, 0 errors. The two unresolved historical failures are test_final_receipt_rebuilds_manuscript_and_anonymous_bundle and test_closed_empirical_workflows_are_path_filtered. They had previously been reproduced on the unchanged parent. Scientific job success does not mean the entire repository suite is green.


## 2026-10-20 measurement attribution and low-speed negative control (new)

Post-outcome diagnostic branch: [diagnostic/delta2021-device-context-20261020](https://github.com/zuizui0223/odsp/tree/diagnostic/delta2021-device-context-20261020). **The frozen DELTATRACK 2021 flying-height primary test remains unchanged.**

On the exact same 2021 GPS source, the 2021 flight panels have 64 L. fuscus birds/64 unique tags and 14 L. argentatus birds/14 tags, with zero within-year same-bird cross-tag replication. All paired `bar:barometric-height` values are constant zero (189,598 GPS-valid L. fuscus events; 26,809 L. argentatus), preventing an independent altitude-channel check. GPS HDOP is completely reported, median 1.2, but measures horizontal precision and cannot remove tag-specific vertical-error differences. Device-vs-animal causation is thus structurally unidentified.

A stationary/very-low-speed (0–0.5 m/s) GPS negative control was frozen after the flying outcome, with x-y modal 100 m cells, identical centered-altitude bins, unchanged balanced donor kernel and 999 date-matched session-label permutations. [Run 39380619623](https://github.com/zuizui0223/odsp/actions/runs/39380619623) completed.

- **Larus fuscus:** 46 eligible birds, 590 bird-days, 51,960 scored GPS events. Observed matched-vs-other centered shape score +0.008155; null mean -0.025646; excess **+0.033801 nats/record**; 999/999 valid draws, 0 exceedances, Holm p=0.002 across the two species.
- **Larus argentatus:** 8 eligible birds at final >=50 scored-bin/day criterion, below min 10. Remains **unavailable**, no null p. Descriptive score +0.01790 is not inferential.
- 63/12 birds had met an earlier less demanding 20-bin/day structural same-cell screen; this does not override the later 50-bin evaluation-day criterion.

**Biological implication:** The individually associated GPS-height distribution shape signal is detectable in low-speed records as well as flying records. Therefore, the positive flying result alone cannot be interpreted as a *flight-specific* individual strategy. Near-stationary signals could arise from tag-dependent error, bird-specific perches/nest microtopography, or both. The negative control **does not prove tag artifact**; the two context effect magnitudes are not directly comparable because sampling, states and conditioning differ. No new bat or penguin claim follows.

Durable receipts:
- [Device QC](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-device-context-20261020/prospective/DELTATRACK_2021_DEVICE_QC_RECEIPT_V1.json)
- [Stationary control](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-device-context-20261020/prospective/DELTATRACK_2021_STATIONARY_NEGATIVE_CONTROL_RECEIPT_V1.json)
- [Cross-project ecological generality boundary](https://github.com/zuizui0223/odsp/blob/diagnostic/delta2021-device-context-20261020/prospective/ODSP_DESCENDANTS_BIOLOGICAL_GENERALITY_BOUNDARY_V1.md)

Next unique identification axis: same-bird different-device tracking or an actually variable independent altitude sensor, plus properly controlled within-bird movement-state/micro-perch data. Repeated mining of the same bird-tag observations cannot by itself estimate the biological versus device-origin fractions.
