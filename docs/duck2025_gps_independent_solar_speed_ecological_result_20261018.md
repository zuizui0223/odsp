# Independent GPS corroboration across a new animal clade — real 2025 duck sensor result

**2026-10-18 · ODSP PR #267 · Source verified first numerical GPS movement result.**
**Do not mislabel GPS ground-speed as latent activity, photo encounter rate, or causal photoperiod memory.**

## Ecological question and why this route is genuinely different

Serengeti mammalian camera-detected event time distributions differed between astronomical daylength-matched rising/falling periods. To test whether that temporal-branch phenomenon could generalize beyond one savanna camera system, a 2025 source containing individual GPS sensor data from seven species of dabbling ducks tracked across multiple Northern Hemisphere countries was identified. Here the response is **within-individual day-versus-night GPS ground.speed (m/s) change**, not camera photo-time proportions or relative frequencies of GPS fixes.

Independent original published source: **van Toor & Waldenström (2025)**, [Zenodo DOI 10.5281/zenodo.16940654](https://doi.org/10.5281/zenodo.16940654). Original source **`250823_LNU_dabbling_ducks_hourly.csv`** MD5 `1972d0ef08b83c2b88a169ba07bb48b3`. The publisher describes UTC sensor timestamps, individual IDs, taxon, source WGS84 location, GPS ground speed and battery/model-variable ~1h/2h schedules.

## Strict first-source archive admission BEFORE numerical speed results

[**GPS original source date-only CI 39090010649 SUCCESS**](https://github.com/zuizui0223/odsp/actions/runs/39090010649), with five known-truth/source tests and exact original 46.3 MB CSV MD5. The dataset includes **294,683 original GPS fixes**, across **seven original source taxon labels**. In the source-only first stage, **36 distinct birds** from the seven species had at least seven observation dates and fifteen original source fixes **on both daylight-increasing and daylight-decreasing sides of the same December-solstice cycle in the same 0.5° geographic cell**; this says nothing about valid day/night movement-speed effects or actual equal photoperiod, as no original ground speed magnitude was opened.

Source original independent fix intervals were strongly heterogeneous: approximately 204,897 intervals between >0 and 1.5 hours, 78,898 between >1.5 and 3 hours, 6,208 from >3 to 6 h, 2,701 between >6 and 12 h, 1,542 over 12 h; 256 duplicate/nonincreasing timestamps. Therefore an analysis counting original GPS fixes in different solar phases would be substantially biased by observation timing and battery schedule, not necessarily wildlife activity.

## Frozen first numerical GPS endpoint and independent run

Before any original GPS numerical ground-speed values were examined, the source-only first eligible cohort led to the [immutable GPS speed contract](../research/DUCK_GPS_2025_SOLAR_MATCHED_SPEED_V0_CONTRACT.json). It registers:

- **Same physical individual**, same 0.5° lat-long cell and same December-solstice cycle. An individual may recur across cells/year cycles, but taxon-level summary weights each animal only ONCE (mean of its qualifying local groups).
- A correct Northern/Southern Hemisphere increasing/falling daylength branch, and actual instantaneous NOAA apparent-sun day/night classification from the ORIGINAL fix UTC timestamp and location; not civil fixed time bins.
- One-to-one deterministic astronomy-based rising/falling day pairs, **original modeled daylength mismatch ≤5 minutes**, no date reuse. For each date require ≥3 original valid `ground.speed` observations on BOTH sides of sunrise/sunset, and for both night and day require falling/rising fix-sampling count ratios between **0.5 and 2**. A local individual-cycle must have **≥5** unique duty-balanced astronomy-paired dates to estimate its sensor response.
- Sensor ground-speed values must be finite 0–60 m/s (three of 294,683 source records excluded above 60 by the **predefined** validity filter; no other GPS speed rows missing/invalid). Within each date/phase use median `log(1+ground.speed[m/s])`, then contrast NIGHT minus DAY; the predeclared seasonal outcome is **falling-(night minus day) − rising-(night minus day)**. The unit at species level is a distinct individual, not the number of GPS fixes, date-pairs or photographs.
- Original seven species and low/zero/undefined results all reported; ≥5 independent animals in a taxon needed for minimal descriptive support. No post-hoc window or taxa filter changes, inferential p-values, legitimate energy expenditure or clock causality claimed.

[**First GPS outcome CI 39090601348 SUCCESS**](https://github.com/zuizui0223/odsp/actions/runs/39090601348) ran all SIX known-truth checks, verified the original source MD5, reproduced all **294,683** source original rows and **36** source-only preliminary individual calendar supports before opening a sensor speed outcome, and archived exact aggregate-only result `duck2025-7species-real-gps-solar-matched-speed-v0` (artifact 12122960943). GPS source coordinates, exact time and individual identity were not exported.

## Genuine cross-clade, independent-sensor observed result — not a universal-law replication

| Original source species label | Independent birds with a qualifying GPS solar/day-night sample | Matched date pairs | Individual-mean double contrast, log(1 + m/s) | Positive/negative individual directions | Species-level descriptive support |
|---|---:|---:|---:|---:|---|
| `Anas acuta` (Northern pintail) | **5** | **57** | **+0.02969** | 4 positive / 1 negative | **YES (minimal n=5)** |
| `Anas clypeata` (Northern shoveler; original label) | 1 | 10 | −0.02451 | 0 / 1 | no |
| `Anas crecca` (Eurasian teal) | 1 | 8 | 0.00000 | 0 / 0 (one tied) | no |
| `Anas penelope` (Eurasian wigeon; original label) | 0 | 0 | undefined | no sample | no |
| `Anas platyrhynchos` (Mallard) | 0 | 0 | undefined | no sample | no |
| `Anas querquedula` (Garganey; original label) | 1 | 13 | 0.00000 | 0 / 0 (one tied) | no |
| `Anas strepera` (Gadwall; original label) | 1 | 98 | +0.02602 | 1 / 0 | no |

After the new astronomy, within-individual cell, paired-date, day/night sample count and battery-duty balance controls, only **9 individuals** from **5 species** remained with an estimable effect, despite the original 36 animals from all seven species appearing eligible at the initial source-calendar stage. Only *Anas acuta*, with five individually sampled animals, reached the predeclared minimal source support; four of five birds pointed to a marginally larger falling-branch nocturnal-relative speed. The **mean double contrast was +0.02969 in log1p(m/s) units**, with an individual leave-one-out mean range **[+0.01961,+0.04478]** (NOT an inferential CI; very small n). The median individual effect was +0.03934. The measured value should NOT be interpreted as 3% of daily animal activity; it is a sensor-specific transformation of FIX-INSTANTANEOUS speed.

The other six source species are INSUFFICIENT for species-level population interpretation, and zero empirical photo-to-speed comparative slopes across ecosystems are estimated. The original full-source valid satellite/animal photo analysis and all seven original 2025 GPS taxon labels remain unchanged.

**Critical ecological conclusion:** This genuinely new bird GPS sensor source did NOT produce sufficient cross-taxon source-valid observations to confirm a universal seasonal behavior/chronotype response. Small positive pintail summary does not establish annual seasonal memory, temperature/refuge regulation, individual behavior budgets or statistically meaningful effect. The negative/zero/insufficient-source cases must be carried into the paper, and no after-result threshold relaxation is allowed to “rescue” a cross-clade hypothesis.

## Implications for manuscript architecture

1. **Supported environmental observation (Serengeti):** approximate same solar daylength does not imply same thermal/rain/green-vegetation seasonal state. Across **322 satellite-QA-qualified original camera-year records**, falling branch NDVI was higher than rising branch. This is vegetation reflectance, not direct grazed biomass.
2. **Supported observational decomposition (Serengeti):** source camera photo-night changes split into within-camera recorded-time and between-camera photo weight redistribution, sometimes with opposing signs, while true camera-hour operations and `q` remain unknown.
3. **Independent sensor trial (seven duck taxa, multiple countries):** confirms possibility of real solar-date fixed location and daypart GPS movement measurements, but rigorous sample admission left only n=5 in one bird species. There is no verified generalized animal seasonal-hysteresis law or mixed-model transfer from Serengeti photo odds to duck GPS speed.
4. **Publication ceiling:** A measured ecological branch asymmetry in phenology/recording does not permit an endogenous photoperiod-memory claim. If submitted now, paper must be reframed as an *observational, explicitly noncausal case study of site-time-season confounding* and external sensor feasibility, rather than demonstrating multi-clade universality.
5. **Biologically decisive future evidence:** multi-region population tracks with known continuous hourly device duty cycle, or real site×hour camera power and species×zone calibration, tested with previously frozen matched-daylength protocol and held-out geography. GPS speed and camera event fractions are distinct estimands.

## Citations and source integrity

- van Toor & Waldenström 2025 public 7-taxon archive, https://doi.org/10.5281/zenodo.16940654 .
- [Original GPS source-only feasibility CI 39090010649](https://github.com/zuizui0223/odsp/actions/runs/39090010649), [first actual independent-sensor outcome CI 39090601348](https://github.com/zuizui0223/odsp/actions/runs/39090601348). First numerical speed route fixed in original GPS source contract; all 6 source/scientific guards passed.
- Previously published original Serengeti source photo/NDVI results [observational ecology report](./serengeti_original_camera_modis_ndvi_photo_link_20261015.md), plus [relative NDVI metrics](./serengeti_ndvi_level_vs_rank_photo_ecology_20261016.md).

**ODSP PR #267 remains DRAFT.** Original RI, Serengeti N2 and Uljin fixed routes unchanged, no previously discovered outcome reclassified.
