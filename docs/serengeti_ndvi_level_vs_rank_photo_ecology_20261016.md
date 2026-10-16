# Does greening magnitude, absolute vegetation or relative habitat rank better explain camera-recorded seasonal shifts?

**2026-10-16 · ODSP PR #267 · New exploratory PHOTO/NDVI predictor contrast; original source preserved. NOT a confirmatory sensor-validated animal-activity analysis.**

## Biology: two different uses of a greener landscape

All **322** original quality-qualified Serengeti source camera×December-solstice-year units had positive falling-minus-rising MODIS greenness differences in the [first original NASA camera-NDVI source route](https://github.com/zuizui0223/odsp/actions/runs/38744196749). However, their PHOTO record count changes were only weakly and inconsistently correlated with the magnitude of greening. This motivates two new questions that should NOT be treated as after-data confirmations:

1. **Habitat level**: Is a physical camera in a *usually greener* habitat, independent of its seasonal greening amplitude? NDVI level mixes woody foliage and herbaceous greenery and is not a measured edible forage quantity.
2. **Relative seasonal rank**: Does a physical camera become *greener relative to all other satellite-quality-qualified original camera locations* on the falling versus rising side of the same photoperiod? When every site greens up by the same amount, the relative habitat rank need not change at all. This is distinct from the within-site NDVI increase.

A stronger photo-count correlation to either could justify a follow-up field/movement hypothesis about spatial sorting. It cannot itself establish herd migration, camera uptime, optical detectability or nutritional forage preference.

## Strict source and sample replay BEFORE reading new predictors

[**First GitHub Actions CI 38909877810 SUCCESS**](https://github.com/zuizui0223/odsp/actions/runs/38909877810) ran all five known-truth tests and recomputed the source evidence with these independent checksum gates:

- Original `consensus_data.csv` MD5 `5ed2d32fd09127c178cf9dca8ccfd623` and `search_effort.csv` MD5 `27cb42f3feaa0642b17cbde24ba15fbd`.
- First source Serengeti PHOTO receipt SHA256 `0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3`, retaining **38,792 original photo detections**, **24,290 astronomy-matched source site×paired dates**, **186 original physical camera sites** and original 43 source taxon labels.
- Original 83-scene MOD13Q1 Terra 2010–2013 QA source receipt SHA256 `e0e3c57de8d6a3ab9996412886e9733ea572cf9989f88a68b5c3ac5fb5557f11`, original 2012 individual NDVI=0.5484 source QA event replay, and all original 83 satellite item/date IDs and pixels at the public reference point.
- Crucially, prior complete **15 original photo/NDVI taxon×year source outcomes** were recovered with *identical original camera counts, support labels and previous Spearman correlations* (replay tolerance 1e−10), against original first camera/photo NDVI receipt SHA256 `b6ed0294d6e4c6277f07ef9327f536c564c33c79265570bf7b37197eb951c25f`. The only original taxon-years qualifying for follow-on displayed associations remain zebra 2011 **n=53**, zebra 2012 **n=31**, and wildebeest 2011 **n=27**. The original 12/15 insufficient-support outcomes remain undefined.

The new source-specific variables were frozen AFTER original PHOTO and green-up outcomes became known: (a) `ΔNDVI_i = F_i−R_i`, the unchanged earlier local green-up; (b) `mean_level_i = (F_i+R_i)/2`; (c) `relative_rank_shift_i = percentile_rank(F_i)−percentile_rank(R_i)` among the SAME year's **full 98/112/112 NDVI-quality-qualified camera sites, chosen without animal photo positivity**. For each source camera/year, F_i and R_i average exact original >=10 good satellite date pairs with >=60% source date coverage, 3×3 250m original Terra NDVI QA=0, last complete 16-day composite within 20 days, no imputation or future imagery.

Two source observation outcomes, unchanged from earlier original route: `log PHOTOcount_F / PHOTOcount_R` and `PHOTO night-fraction_F − PHOTO night-fraction_R` at the same originally qualified source camera/date supports. All predictor/outcome combinations, both signs, nulls and undefined cases were retained; no new thresholds, taxon selection, p-values or cross-ecosystem transfer.

## New genuine source PHOTO + remote-sensing descriptive results

**Spearman rho** of each camera's NDVI variable against its PHOTO-count change (not individual animal abundance and not a camera-hour rate):

| Source species and cycle | Distinct source cameras (same as old sample) | ΔNDVI rho | mean NDVI level rho | seasonal percentile-rank shift rho |
|---|---:|---:|---:|---:|
| Zebra 2011 | 53 | **+0.1141** | **−0.0003** | **−0.0139** |
| Zebra 2012 | 31 | **−0.0488** | **−0.5657** | **−0.1368** |
| Wildebeest 2011 | 27 | **−0.0015** | **+0.3005** | **−0.1770** |

For the second, temporally distinct PHOTO-night-fraction response:

| Source species and cycle | ΔNDVI rho | mean NDVI level rho | percentile-rank shift rho |
|---|---:|---:|---:|
| Zebra 2011 | +0.1288 | +0.0879 | +0.0544 |
| Zebra 2012 | +0.3121 | +0.1508 | +0.3355 |
| Wildebeest 2011 | −0.0706 | +0.2739 | −0.2315 |

The strongest single PHOTO-count correlation was **zebra 2012 versus mean vegetation NDVI (ρ=−0.5657)**, with original physical-camera leave-one-out range **[−0.6000, −0.5253]**, not an inferential confidence interval. The closest 2011 zebra response to mean vegetation NDVI is essentially zero, and 2011 wildebeest mean-level rho is **+0.3005** with leave-one-camera range **[+0.2185,+0.4053]**. This is species/year heterogeneous observational PHOTO spatial reweighting. Possible ecological interpretations include habitat architecture (denser green woody vegetation versus open grazing plains) and season-dependent spatial activity/detection; **neither the observation nor individual migration is established**.

Relative percentile-rank shifts can have considerable spatial spread despite every station greening (2010 `[-0.722,+0.763]`, 2011 `[-0.793,+0.946]`, 2012 `[-0.766,+0.820]` across all satellite-admitted original stations). Still, the photo-count association with rank-shift was small-to-negative in all three previous photo-qualified comparisons. Zebra 2012 rank-shift correlation with the NIGHT PHOTO-fraction change was `+0.3355` (leave-one-camera `[+0.271,+0.420]`, NOT CI), but not repeated comparably for 2011 zebra (`+0.0544`) or wildebeest 2011 (`−0.2315`).

Original camera NDVI spread matters: the mean-level NDVI min–max across independently QA-qualified sites was **0.241–0.523 (2010)**, **0.293–0.639 (2011)** and **0.366–0.600 (2012)**. Thus the all-positive seasonal greenup does NOT imply all cameras had the same original vegetation level, nor any monotonic relation of local greenness changes to photographed counts.

## Biological interpretation: separate season, place and time

Under approximately equal daylight, greenness can change *everywhere* while relative green habitat rank changes nontrivially. But which sites PHOTO-record migratory mammals and the apparent night-time PHOTO niche cannot be reduced to one greenness predictor, and different animal taxa/year-cycles do not share a simple response direction. Spatial survey mixing can obscure within-site photographed-time changes; the previous exact W/B decomposition still describes PHOTO records only.

The 2012 zebra negative mean-level correlation is **not a significant animal habitat preference test**. Source photo-positive camera rosters were conditioned on wildlife detection, the camera system's flash/hardware was changed from 2010 through 2012 (per Swanson 2015), true station×hour operation and separate camera detection probability by species/solar zone/season were not verified, and the mapped 250-m greenness includes woody canopy instead of edible grass. No p-values, multiple-testing selection, 57-individual GPS corroboration, nighttime behavior causal coefficient or broad eco-region universal claim is warranted.

The original paper's strongest *independent observation* remains: satellite-measured vegetation NDVI is consistently higher on the falling branch **at matched daylength within quality-supported Serengeti camera positions**; the ecological/animal consequence remains observationally uncertain.

## Independent-sensor frontier, not yet a result

Masolele et al. **2026** (JAE DOI https://doi.org/10.1111/1365-2664.70435) published a separate **57 individual, 143,168 GPS fix** Serengeti wildebeest study during **2019–2023**, dataset DOI https://doi.org/10.5061/dryad.rn8pk0ps8; official first-party Dryad metadata registers CSV `WB2019_2023_data.csv` **13,481,100 bytes**, SHA256 `9631aa94bda8b9efd7adbe8ca0004e58f22c98d03b729fcab4df40434a0fc148`, under CC0. GPS fix spacing is variable (published ~65% 4h, ~19% 1h, ~15% 8h), and the publisher filtered 1h≤dt<24h. One cannot equate GPS FIX timing to activity. A separate original `GPS_HEADER_ONLY_SOURCE_GATE` workflow was added to verify legal original-source download and assess date+sample-cadence metadata without reading a single animal point. **No GPS animal outcomes are asserted**, no additional biome replication has occurred. In fact the [official public source-only header CI 38910468356](https://github.com/zuizui0223/odsp/actions/runs/38910468356) passed four integrity/claim tests but returned **HTTP 401 / `HOLD_ORIGINAL_GPS_2026_SOURCE_NOT_ADMITTED`** for original CSV download; not one protected GPS row or individual point was opened. CI completion does **not** imply the telemetry data were obtained. Source usage will require provider-authorized original bytes and signed provenance, before any movement analysis.

## Reproducibility

- NDVI relative-level/rank first committed pre-new-outcome [CI **38909877810** success](https://github.com/zuizui0223/odsp/actions/runs/38909877810); contract `research/SERENGETI_MODIS_RELATIVE_GREENNESS_V0_CONTRACT.json`, implementation `scripts/run_serengeti_modis_relative_greenness_photo_v0.py`, five known-truth/source tests `tests/test_serengeti_modis_relative_greenness_v0.py`, full 15-row raw aggregate artifact `serengeti-photo-source-ndvi-absolute-and-relative-rank-v0`. No protected camera location or raw wildlife timestamp was exported.
- GPS source official page, file checksums and permission status in 13-source feasibility matrix; `research/MASOLELE_2026_WILDEBEEST_GPS_SOURCE_GATE_V0.json` and source-only script/workflow.
- All first PHOTO, satellite greenness, stationary-site W/B, trophic-photo and previous RI/Serengeti N2/Uljin results immutable; PR #267 remains DRAFT.

**Scientific decision:** do not multiply exploratory NDVI thresholds or fit new 3-year ecological slopes. Next meaningfully independent biological evidence requires GPS step-duty-cycle source admission or authentic camera ON-hour + q calibration, and ultimately a new ecosystem held out from model development.
