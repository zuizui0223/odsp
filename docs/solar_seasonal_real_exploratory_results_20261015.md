# 2026-10-15 empirical ecological update — two original published mammal camera sources

**Route:** exploratory, source-checked, post-original-publication. **Do not reclassify original N2 or RI terminals.**  
**Main question:** When daylength is matched between increasing and decreasing annual daylight branches at a physical camera station, is the **recorded time-of-detection distribution** still branch dependent, and is the sign/shape taxon-specific?

## 1. Original Serengeti source event data — new observed-record analysis

[Dedicated original-source CI 38677521888 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/38677521888); 5 pre-outcome synthetic source/geometry tests pass; both public original CSV checksums verified:
- `consensus_data.csv`: MD5 `5ed2d32fd09127c178cf9dca8ccfd623`; source **334,671** consensus rows.
- `search_effort.csv`: MD5 `27cb42f3feaa0642b17cbde24ba15fbd`; **225** distinct original site ID labels.
- Pre-animal date-only support published and frozen [CI 38677045328](https://github.com/zuizui0223/odsp/actions/runs/38677045328): 186 sites each with at least 20 December-solstice mirrored photo-valid calendar-date pairs in some year-cycle; 25,016 site×calendar-day candidate pairs.
- New solar-date geometry retained **186 source sites** and **24,290 site×date pairs** whose real NOAA-derived sunshine durations differ by **at most one minute**, from original public UTM coordinates projected internally only (no exact locations emitted).
- Original high-agreement consensus and same-site-species 30-min processing yielded **38,792 recorded mammal/other-taxon detections** on those matched dates; **43 source taxon labels** with any records. Prespecified `>=100` recorded detections on each branch and `>=10` site-cycle double-branch detection threshold admitted **15 source labels** for descriptive display; includes `guineaFowl` (a BIRD), so never present all 15 as mammals. `hippopotamus` null OR must remain null.
- Two photo record-time odds ratio comparisons:
    - falling/rising `edge/core`: first and last daylight quarter combined versus daylight middle half;
    - falling/rising `night/daylight`: outside sunset–sunrise versus all daylight.
  Mantel–Haenszel ratios are stratified by original physical camera SiteID × Dec-solstice calendar cycle; NO event-independence p-value or q calibration.

| Original source taxon | Matched-dates source records | Site-cycle MH edge/core OR | Site-cycle MH night/day OR | Site-cycles with both branches detected |
|---|---:|---:|---:|---:|
| Spotted hyena (`hyenaSpotted`) | 1,338 | 1.3357 | 2.6284 | 95 |
| Lion female (`lionFemale`) | 518 | 2.6333 | 2.7391 | 25 |
| Zebra (`zebra`) | 9,538 | 1.0839 | 1.4131 | 233 |
| Buffalo (`buffalo`) | 1,758 | 0.7026 | 1.3578 | 118 |
| Thomson's gazelle (`gazelleThomsons`) | 5,219 | 0.6180 | 0.7917 | 63 |
| Giraffe (`giraffe`) | 2,326 | 1.2132 | 1.0850 | 186 |
| Elephant (`elephant`) | 1,804 | 0.9777 | 1.0948 | 169 |
| Wildebeest (`wildebeest`) | 6,166 | 0.9639 | 1.3937 | 102 |

**New descriptive observation:** Distinct source taxa have contrasting *detected photograph-time* reallocations between opposite solstice-date branches even with nearly matched astronomical daylength; within a given taxon the core→daylight-edge contrast and overall daylight→night contrast need not agree (e.g., source-record Buffalo edge/core <1 versus night/day >1). Nothing here establishes biological photoperiod memory, thermal avoidance, independent animal events or stable behavioral chronotype. There is only ONE sampled ecological landscape, so **this is not 186 independent ecosystem replications**. Source opening detected 43 taxa including several nonmammals/low-support; full machine-readable archive holds ALL, with undefined cells unchanged. The headline 8 mammals are illustrative after-source examples, not a separately pre-frozen familywise selected analysis; all 15 original fixed-support taxa including `guineaFowl` and all 43 original taxa stay in original outcome artifact.

**Major camera observation limit:** Authors' first/last valid photo dates do NOT independently establish continuously powered hourly operation; same-day photoperiod does NOT ensure same branch camera sensitivity `q`, day zone ON-hours, animal passage opportunity, weather, vegetation, population composition or actual animal behavior. Condition on source recorded photographs, not true exposure. Site×calendar-cycle MH odds are descriptive not independent animal inferential p-values.

## 2. Independent Northern Ireland original study — external *source*, not qualified causal/ecological replication

Caravaggi et al. 2018, PeerJ DOI https://doi.org/10.7717/peerj.5827, tagged original public source https://github.com/arcaravaggi/PeerJ_mammal_activity/tree/v1.2.1 ; Zenodo https://zenodo.org/records/1470320 .

[Original source CI 38678277593 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/38678277593). All 5 synthetic checks pass; actual `all_data.csv` Git blob SHA1 exactly `2084dfac55acb75efe6e61c1abc306aeda0904eb`. It has **9,411** original rows. We independently reproduced original authors' exact **8,761** after dropping their four nonfocal `spp_1` labels (Sika, Muntjac, Hedgehog, Rat): 9,411−650=8,761, confirming published source accounting. Source has **25 rows with year 2001**, clearly outside the main 2013–2016 analysis window; never silently reinterpret those calendar years.

For original-author local sunrise/sunset duration within **10 min** at the SAME site and calendar year on dates ≥7 days before/after June 21, only **13 site×year units** had pairable dates containing ≥1 published mammal record on both branches, encompassing **353 source photograph-date pairs** and **988 original camera detection rows**. This differs from the earlier preliminary 14-unit number because the final frozen route uses proper CSV quoting, includes original 2016 data, applies the ≥7-day solstice gap, and applies original author taxon exclusions. **Most importantly those 353 pairs were selected from days with recorded animal events, NOT independently known camera ON-days**. They cannot provide unbiased branch activity/encounter rate effects. The SINGLE highest-support site×year contributes **51.56% of candidate pairs**. Northern Ireland is independent in geography from Serengeti but is weak in matched support and not a clean Tier-A biological replication.

Raw `species` labels are NOT standardized: `Badger` and `Badger `; `Grey Squirrel` and `Grey squirrel`, etc. The frozen first-route intentionally reports literal source values (**17 taxon label spellings**, not 17 biological mammal species) and does not retrospectively merge after observing outcomes. All source labels and zero/undefined odds are retained. Selected descriptive first literal-label photo odds:

| Raw source label | Matched original photo records | Site-year stratified edge/core | Site-year stratified night/day |
|---|---:|---:|---:|
| `Badger` | 507 | 0.5008 | 0.2015 |
| `Fox` | 63 | 2.8000 | 1.9750 |
| `Hare` | 128 | 1.1039 | 0.6002 |
| `Rabbit` | 200 | 0.5000 | 0.9167 |

These are only photo-time descriptive odds, not equivalent effort-corrected animal movements, fixed species effects or significant between-site biological support. Relative apparent change may be strongly dependent on site composition, sparse observations and device q. The original 2018 paper had already shown species-specific seasonal solar-time shifts; novelty CANNOT be claimed from the existence of fox/badger seasonal differences.

## 3. What the two-region pilot means and does NOT mean

**Supported new source-observation statement:** In one East African savanna camera dataset and one independent Northern Ireland temperate camera dataset, the **conditional distribution of ORIGINAL RECORDED photo times** between increasing and decreasing photoperiod branches can differ by taxon under roughly matched daylength. Multiple original taxon contrasts point in different directions. A temperature/photoperiod driver was NOT directly measured or differentiated, and the site/year/date selection and original observation systems differ.

**Not supported:** a universal mammalian law; season-memory mechanism; genuine animal latent daily timing independent of detector efficiency and camera uptime; source-selected Ireland as a rigorous external confirmation of Serengeti; a transferable environmental lag coefficient; independent-site sampling p-values; universality by mixing one ecosystem's 186 stations with another dataset's site-year detection-date pairs.

## 4. Next highest-value ecological source development

(1) Independently verify camera station×day×zone ON-hour exposure for BOTH branches in at least two landscapes, preferably different temperate and tropical climates; (2) extract independent branch-specific temperature, vegetation phenology or rainfall lag from true dates using source-approved coarse location exposure (no protected GPS); (3) test all predeclared taxa with a region-held-out prediction interval; (4) otherwise publish a narrow camera-record timing natural-observation paper or explicitly diagnose the source limitation. No extra synthetic q-PR proliferation is a substitute.

## Reproducibility

- `research/SERENGETI_SOLAR_SEASON_RECORDED_EVENT_V0_CONTRACT.json`, `scripts/run_serengeti_source_recorded_solar_season_v0.py`, [source-verified first CI 38677521888](https://github.com/zuizui0223/odsp/actions/runs/38677521888), aggregate-only artifact `serengeti-solar-season-recorded-event-source-v0`.
- `research/IRELAND_RECORDED_SOLAR_DAYLENGTH_V0_CONTRACT.json`, `scripts/audit_ireland_solar_daylength_recorded_v0.py`, [source-verified first CI 38678277593](https://github.com/zuizui0223/odsp/actions/runs/38678277593), aggregate-only artifact `ireland-observed-solar-daylength-photo-record-v0`.
- Both routes are separate exploratory, source-data-visible after historical paper publication. All earlier ODSP terminals and original Uljin matched date source hold unchanged. Keep PR #267 DRAFT.
