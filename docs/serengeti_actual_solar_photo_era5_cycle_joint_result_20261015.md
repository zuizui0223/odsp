# Ecology result: do nightward photo-record reallocations simply follow hotter falling seasons?

**2026-10-15 | PR #267 | Source-verified post-first-result EXPLORATORY alignment, not an independent confirmatory ecology endpoint.**

## 1. Why this new question is biologically meaningful

The first Snapshot Serengeti original-source equal-daylength analysis found substantial and sometimes opposing temporal photo-record shifts among sympatric mammals. Two competing ecological scenarios are:

- **Simple warming/thermal displacement:** animals shift into night on falling-branch dates because those dates are persistently hotter.
- **Broader seasonal ecological reorganization:** light geometry is similar but food/vegetation/rainfall, large-herbivore movement, biotic encounters, reproduction, camera-detection and other weather change. Different taxa therefore reallocate PHOTO-detected time in nonparallel ways.

A measured recorded-time association alone cannot identify either behavior or causality. A useful falsifier for the *simplest* warmth account is whether falling-branch night shifts are visible in solstice cycles whose **regional observed/reanalysis daily maximum temperature difference is not positive on average**.

## 2. Independent source and exact previous outcome replay succeeded

**[New original-source & ERA5 joint GitHub Actions CI 38700484637 SUCCESS](https://github.com/zuizui0223/odsp/actions/runs/38700484637)**, all four synthetic known-truth tests PASS and MD5 of both original Snapshot Serengeti files independently reverified.

- Original first published source photo-date outcome from [CI 38677521888](https://github.com/zuizui0223/odsp/actions/runs/38677521888) was **independently re-executed exactly**, including **43 source taxon labels**, **24,290 accepted site×paired dates**, **38,792 matched-date CAMERA photo records** across **186 original camera station IDs**. Byte-exact first JSON output fingerprint SHA256 `0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3` was a fail-closed gate before joining new data.
- Independent [ERA5 regional weather first result CI 38699783443](https://github.com/zuizui0223/odsp/actions/runs/38699783443) was similarly re-downloaded and checked to frozen 2010–2013 daily-array SHA256 `aaa93eec1ac0fab3315bfc712020970746d47cd1d407b8a7778243b2f627bee7` before photo outcomes were opened.
- The join uses the **exact original site/date-pair sun geometry and <=1 minute photoperiod caliper** already frozen in the first animal source route. No favorable-date reranking, new taxa selection, source substitution, pseudo-counts or tests of independent animal samples were introduced.
- The source records are split by original December-solstice cycle (2010, 2011, 2012), not unrelated civil winter/year labels. The original all-taxon table is retained in full. The five focal mammals shown below are labeled as selected **after knowing the old pooled photo odds**, and therefore illustrative only.

## 3. The environmental difference at ACTUAL original photo-date mirror support

A SINGLE regional ERA5 air temperature/precipitation grid was matched against the source's frozen physical camera/date mirror supports. Report descriptive site×date weighted means, never significance from duplicated geographic weather cells.

| December-solstice cycle | Matched site×date pairs | Physical site IDs | Falling−rising daily maximum ERA5 air temperature (°C) | Falling−rising prior 30d rainfall (mm) |
|---|---:|---:|---:|---:|
| 2010 | 4,718 | 108 | **+0.160** | +61.158 |
| 2011 | 9,769 | 135 | **−0.060** | +11.848 |
| 2012 | 9,803 | 130 | **−0.566** | +48.751 |

**This is an important refinement:** the broad climate-only 522 symmetric regional calendar pairs and the original 24,290 photo-supported source pairs have different statistical populations. The above values reflect the actual ORIGINAL observation date support, without treating replicated climate dates across cameras as independent weather measurements. Temperatures do NOT show universal warmer falling branches; rainfall histories are higher on average on the falling branch in all three cycles in this one coarse cell.

## 4. Same-site photo-time evidence, split by independent calendar cycle

Odds are site-stratified *falling/rising* night-records relative to daylight-records. OR>1 = increased nightward fraction among photographed events; NOT higher night encounter rates per true camera-hour and NOT latent animal movement/chronotype.

| Source taxon | Cycle 2010 | Cycle 2011 | Cycle 2012 | Total original photo records in these three cycles |
|---|---:|---:|---:|---:|
| Spotted hyena (`hyenaSpotted`) | **3.367** | **2.498** | **1.380** | 1,338 |
| Zebra (`zebra`) | **2.017** | **1.249** | **1.505** | 9,538 |
| Buffalo (`buffalo`) | 0.848 | 1.468 | 1.444 | 1,758 |
| Thomson's gazelle (`gazelleThomsons`) | 1.111 | 0.408 | 0.741 | 5,219 |
| Female lion (`lionFemale`) | 10.55 | 1.238 | 7.045 | 518 |

Lion per-cycle estimates are particularly sparse: only 7, 11, and 7 photo-recording site IDs with lion detections on both seasonal branches per cycle, so large values and an undefined daylight edge/core comparison in 2012 must NOT be treated as precise effects. All **43 original source taxon labels** (including undefined/zero contrast cells and a bird label) are preserved in original machine-readable artifact. The selected focal five are not a corrected multiplicity-controlled family.

The **orthogonal within-day CORE→DAYLIGHT-EDGE shift** differs again from the NIGHT→ALL-DAYLIGHT signature. In the same three cycles, spotted hyena site-stratified daylight edge/core recorded ORs are 1.879, 1.089 and 0.479; zebra edge/core 1.060, 1.086 and 1.093; buffalo 0.554, 0.777, 0.694. A single solar-corrected mean event hour could conceal these differences.

### What can and cannot be concluded

The source shows a persistent **directional photographed-event nightward redistribution** for hyena and zebra in both years with average *falling-branch regional cooling* (2011 and 2012), not simply in warmer calendar seasons. This is **evidence against narrating the entire descriptive source pattern as mechanically caused by a universally hotter falling branch**. It is NOT evidence against more sophisticated thermal regulation: daily regional T_max is not local camera-zone temperature, nor is warmer/cooler a controlled heat treatment.

The rainfall-history contrasts and strong known Serengeti grazing-migration seasonality make ecological-resource/phenology and biotic spatial redistribution interesting alternative HYPOTHESES, but **no vegetation NDVI, forage, migration, independent animal trajectories or species×camera×hour q data were included**. A rainfall-mediated causal claim would be fabricated.

Three annual climate cycles, despite many sites and photo records, are NOT independent climatic replication or a credible environmental slope sample. Therefore no ecological p values, generic hysteresis theorem, novel solar biological clock, thermal coefficient, conservation generality or cross-region causal conclusion follows.

## 5. Scientific priorities to turn observation into explanatory ecology

1. Obtain independent **site×solar-zone actual camera-power ON intervals**, or an alternative robust individual GPS/accelerometry dataset with actual sampling effort. No causal or latent activity statement until independent detection calibration.
2. Test an independently specified ecological rain/greenness → herbivore movement → predator encounter-time network with time/space alignment, not just 30d rainfall at one representative cell. Satellite NDVI and measured herbivore migration are desirable independent indicators.
3. With true independent landscapes, use region-held-out prediction: effective independent sample size is the number of *study landscapes*, not photographed animals, camera sites, calendar pairs or 522 mirrored dates.
4. Stop if original data won't support these; a **carefully limited observational photo-time ecology** report may be defensible, but not a universal animal seasonal clock response.

## Reproducibility and source interpretation

- Previous v0 photo source-checked [CI 38677521888](https://github.com/zuizui0223/odsp/actions/runs/38677521888), [climate v0 CI 38699783443](https://github.com/zuizui0223/odsp/actions/runs/38699783443), and **[joint replay CI 38700484637](https://github.com/zuizui0223/odsp/actions/runs/38700484637)**.
- Immutable new after-outcome contract `research/SERENGETI_SITE_DATE_PHOTO_ERA5_ALIGNMENT_V0_CONTRACT.json`; new audit script `scripts/run_serengeti_photo_weather_cycle_alignment_v0.py`; tests and workflow run from PR #267, with original animal first result, external weather daily series and both original source MD5 checksums required to match.
- Artifact `serengeti-original-photo-era5-cycle-alignment-v0` stores weather cycle-level aggregates and **ALL original 43 source taxa × cycles source-photo counts**, no camera identifiers, GPS or raw timestamps.
- Old Rhode Island, earlier Serengeti N2 terminal inference, Uljin source HOLD and existing ODSP qualified methods remain unchanged. PR stays DRAFT pending independent ecology review.
