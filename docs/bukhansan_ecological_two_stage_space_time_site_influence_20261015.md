# Ecological result: observed spatial localization and station-conditioned diel timing can coexist

**Updated 2026-10-15 | Postpublication secondary analysis | ODSP PR #264 | NOT independently replicated animal behavior**

## Biological question

Do Water deer and Wild boar in Bukhansan National Park show a single fixed species-specific chronotype, or are their **recorded** clock-time differences intertwined with unequal representation at physical camera stations?

Source: Jeong, Shin & Kim (2025), *Journal of Agriculture & Life Science* 59(5):111–118. DOI https://doi.org/10.14397/jals.2025.59.5.111, original author-uploaded [PDF](https://www.researchgate.net/publication/397496454_Daily_Activity_Patterns_of_Wild_Boars_and_Water_Deer_in_Forest_and_Wetland_Habitats_of_Bukhansan_National_Park_Implications_for_Human-Wildlife_Conflict_Mitigation). Original printed Tables **1 and 2** supply each of 11 camera IDs and each of 24 clock-time row frequencies for BOTH focal taxa. Tables **3 and 4** give original published 2×2 species×habitat day/night counts. All site-derived numerical analyses below reconcile with the published 24-hour species row totals, four habitat subtotals and grand total 457.

Study: 9 forest and 2 wetland camera stations, June 14 to September 5, 2019 (83 reported days). Author methods classified **day vs night using daily sunrise/sunset reported for Seoul by Korea Astronomy and Space Science Institute**; repeated captures of the same individual within 30 minutes were excluded, but different animals from one photograph could each contribute. Those daytime/nighttime counts **cannot** be reconstructed by assigning each pooled hour row to solar day/night, since exact dates are unavailable. Source hourly ON/OFF operating effort, species-specific detector sensitivity and animal identity are also unavailable. We deliberately use the printed `01:00–06:00` versus `19:00–24:00` row labels solely as a **clock-bin descriptive contrast**.

The previous abstract-only v0 rounded-percent inverse problem was superseded as *source evidence*: the exact day/night source counts were actually printed by the original authors. Keep its methodological demonstration separate and do NOT claim a novel first discovery of those counts.

## Stage one: unlike an abstract species-wide clock, detected space use is strongly uneven

| Direct author-table feature | Water deer | Wild boar |
|---|---:|---:|
| Source records across 11 cameras | 184 | 273 |
| Public camera stations with positive records | **7 of 11** | **11 of 11** |
| Fraction of all species records at wetland **M2** | **50.00%** (92/184) | **17.95%** (49/273) |
| Inverse-Herfindahl effective camera count of *records* | **3.034** | **7.439** |

The Schoener-style **overlap of the species' detected-camera record distributions**, `1−0.5 Σ_s |p_W(s)−p_B(s)|`, is **0.6521**. Here `p_species(s)` is the fraction of that species' published *recorded detections* at the public camera code s. This is NOT habitat-selection probability, true spatial occupancy, animal abundance, camera effort or a comparison with the temporal KDE overlap metric. The inverse-Herfindahl statistic is a descriptive concentration index, NOT an ecological independent-sample-size estimator.

**Ecological interpretation within evidence limits:** The apparent observed ecological niche has at least TWO stages: whether a species is recorded at a camera at all, and *conditional on recording* when it is detected. Water deer records are spatially more localized across this particular camera network than Wild boar records.

## Stage two: paired-camera clock-time signatures and their actual sensitivity

At the **seven camera codes where both animals were recorded**, in the author-publication 01–06 plus 19–24 clock windows only:

- Water deer: **74/158 = 46.84%** of recorded early/late events are in 01–06.
- Wild boar: **73/190 = 38.42%**.
- Observed *same-roster* pooled difference: **+8.414 percentage points**.
- Exactly five of the seven sites show a positive within-site fraction difference; two are negative. A naive independent-site sign diagnostic **p=0.453**, which itself cannot be automatically treated as independent spatial replication.
- Exact symmetric *record composition* Kitagawa identity for THIS contrast: **+10.220 points** from mean within-site recorded time-profile differences and **−1.806 points** from differing source-record camera weights. This is an **arithmetic decomposition, NOT two independently identifiable causal effects**.
- Equal-weight mean of all seven published shared-camera time-share differences: **+6.289 points**. Two forest sites G12 and G21 each contribute only ONE Water-deer early/late clock-bin registration, making even such site-balanced descriptive means extremely unstable.

The conventional **source-count Mantel–Haenszel** cross-species 01–06 versus 19–24 conditional odds-ratio estimate is **1.615826**. It must NOT be described as a valid biological population model, because the calculation assumes an observation process not independently calibrated, and may double-count visits/animals.

### Leave exactly one *original published camera* out, 11 times

| Omitted public camera | Habitat | Source-count MH odds ratio | Shared-site observed 01–06 difference, percentage points |
|---|---|---:|---:|
| G1 | Forest | 1.616 | 8.414 |
| G3 | Forest | 1.616 | 8.414 |
| G4 | Forest | 1.610 | 7.675 |
| G9 | Forest | 1.616 | 8.414 |
| G12 | Forest | 1.664 | 9.066 |
| G17 | Forest | 1.616 | 8.414 |
| G19 | Forest | 1.695 | 8.307 |
| G21 | Forest | 1.589 | 8.792 |
| G22 | Forest | 1.644 | 9.433 |
| M1 | Wetland | **1.725** | 9.226 |
| M2 | Wetland | **1.332** | **6.613** |

**What holds:** The observed source-count MH odds-ratio direction remains above 1 under **all 11 single-camera exclusions** (range **1.332–1.725**); the shared-camera pooled late-share contrast remains positive (range **+6.613 to +9.433 points**). Removing any of the 4 stations without Water-deer observations does not change the paired MH estimate; retaining their zero detections in the source roster remains essential to correctly describe site occurrence.

**What does not hold:** This is not evidence of a well-replicated species effect. M2 supplies **64.21%** of the total conventional CMH score deviation for the published source counts, and the usual **unvalidated event-independence** chi-square p-value shifts from ~0.0466 with all sites to ~0.3562 without M2. These are NOT valid p-values for independent animals, camera clusters, causal temporal segregation, or new population inference. At equal camera weights, dropping only **G21** reduces the descriptive mean contrast to **+0.194 points**, while dropping **G12** raises it to **+14.480 points**. Such extremes expose how tiny record cells destabilize ostensibly balanced site comparisons.

**One context-relevant within-habitat detail:** The wetland M1 camera shows near-equal Water/Boar late fractions (5/14 versus 8/22); wetland M2 shows 40/88 versus 13/47. The two wetland stations are not independent study regions and do not support a new habitat interaction test. Both may differ by placement, detection and visitor exposure.

## Astronomy comparison clarified by source paper

The authors DID classify their published day/night totals using **date-specific Seoul sunrise/sunset** (method p.112). A broad *sunset-to-sunrise night* definition can therefore be matched **categorically** in the other public Uljin study by combining Uljin's *civil crepuscular + strict night* detections (but not by assuming the studies have identical station-specific astronomy or observational effort):

| Public field aggregate | Water-deer fraction at sunset-to-sunrise-type night | Wild-boar fraction |
|---|---:|---:|
| Uljin Jeon & Lim 2026, pooled 2022–2023 (*civil twilight + strict night*) | (51+499)/814 = **67.57%** | (37+172)/684 = **30.56%** |
| Bukhansan Jeong et al. 2025, original forest source | 52/74 = **70.27%** | 141/199 = **70.85%** |
| Bukhansan 2025, original wetland source | 92/110 = **83.64%** | 57/74 = **77.03%** |

This shows a **large context-associated change in reported Boar night registrations**, even after resolving the main civil-twilight label difference. It does NOT demonstrate nocturnal behavioral plasticity, adaptation or a season/human disturbance mechanism, because Uljin combines a different year and network, source sampling rules differ, and neither provides site-hour effort or calibrated detection. The public Uljin night fractions are based on source-released pooled Supplement 3, NOT the frozen original 2022 41 photoperiod mirror dates.

## Why this is a useful ecological paper result rather than another clock algorithm

The substantive result is a **joint observed-space and observed-time ecological heterogeneity**: (i) Water deer records are concentrated at fewer cameras, (ii) a conditional 01–06 versus 19–24 event-time difference persists in the estimated direction after every single station omission, but (iii) its strength, site-balanced magnitude and numerical evidence are fragile, especially M2 and tiny sample cells. Together with other Korean field studies, these observations argue **against presenting one region's pooled nocturnal percentage as an invariant species chronotype**.

They do NOT prove competition, human avoidance, altered thermoregulatory timing, solar entrainment or a movement strategy. An ecology manuscript should use this as a **postpublication observational reanalysis**, not as a preregistered new field discovery.

## Reproducible route and frozen original study boundary

- Primary source full text: https://doi.org/10.14397/jals.2025.59.5.111, Tables 1–4, particularly reported station×clock-time source counts.
- Input source-derived, independently margin-checked contract: `BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json`.
- Separate post-data design: `BUKHANSAN_PUBLISHED_CAMERA_SITE_INFLUENCE_V2_CONTRACT.json`.
- Calculations: `scripts/run_bukhansan_published_camera_site_influence_v2.py`; tests `tests/test_bukhansan_published_camera_site_influence_v2.py`.
- [Successful dedicated GitHub Actions source-checked test/analysis run 38633390210](https://github.com/zuizui0223/odsp/actions/runs/38633390210), **6 regression tests passed** (the source table is cross-checked using all original 24-hour published column totals plus habitat totals).
- Original Uljin 2022 41 fixed daylength pair testing still **HOLD** pending genuine NIE EcoBank v1.1 event archive, public release provenance, hourly independent camera operation records and independent q. Do not treat the Bukhansan source as Uljin mirror-pair observations; refer to issue #265. PR #264 stays Draft.
