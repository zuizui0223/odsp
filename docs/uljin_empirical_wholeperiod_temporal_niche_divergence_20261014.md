# Ecological result from authentic published diel-period counts — four ungulates, Uljin

**2026-10-14 | PR #264 | post-publication exploratory comparison, not a preregistered study outcome**

## Ecological question

Are the four sympatric ungulates using the same *detected temporal niche* across their pooled year, or is one pair consistently separated in **night relative to daylight** when the different durations of those periods are accounted for?

This is a **descriptive ecological question** with authentic 2026 published data, distinct from the unobserved 2022 original 41 early-growing-season vs midsummer matched-daylength comparisons.

## Authentic source and independent recomputation

Jeon J-H & Lim A (2026), *Biodiversity Data Journal* 14:e191556, Supplementary material 3: https://doi.org/10.3897/BDJ.14.e191556.suppl3. Official public host https://zenodo.org/records/21319408, file `oo_1559451.zip`, independently listed MD5 `085afc8382ae5668edfa8ad74122a68e`, downloaded and MD5 checked by [GitHub Actions run 38492475055](https://github.com/zuizui0223/odsp/actions/runs/38492475055). SHA256 of the public journal supplement ZIP `00b33fa08bad7f67619b3f5a07c1bd43e9ddceba00f4cd12554b23aebe3a5219`; **this is NOT an EcoBank original source ZIP hash.**

Within the journal supplement ZIP: `EA02_DielRate_Table_BySpecies.tsv` and one PNG; the TSV is **12 public aggregate rows** (4 species × 3 solar-related periods). All four species sum to the publication's **4,623** released detections. This is an externally published primary *aggregate summary*; it is **not** raw dated event, station identifier or camera-operation data.

The journal defines daylight as sunrise–sunset, civil crepuscular as civil dawn→sunrise plus sunset→civil dusk, night as civil dusk→next civil dawn. The published crepuscular category lies **outside direct sunrise–sunset daylight**. It is NOT the earlier frozen PR #264 H1 daylight-edge interval (first/last 25% of sunrise-to-sunset daylight).

The [separate scientific CI 38492757442](https://github.com/zuizui0223/odsp/actions/runs/38492757442) verified the external MD5, original 12 TSV rows, all four species totals, published period-hours arithmetic, and all six pairwise night/day rate-ratio contrasts. No estimation of inferential p or independent site variance was attempted.

## Original published counts and recomputed period-normalised detection signatures

| Species | Daytime n | Civil-crepuscular n | Nighttime n | Total n | Night/day period-rate ratio | Civil-crepuscular/day period-rate ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Long-tailed goral | 1325 | 139 | 853 | 2317 | 0.7343 | 1.3862 |
| Siberian roe deer | 463 | 73 | 272 | 808 | 0.6701 | 2.0834 |
| Water deer | 264 | 51 | 499 | 814 | **2.1559** | **2.5527** |
| Wild boar | 475 | 37 | 172 | 684 | **0.4130** | 1.0293 |

The SOURCE'S common published period-duration denominators are daylight **4757.1675 h**, civil twilight **360.0144444 h** and night **4170.8180556 h**, giving precisely **9288 h = 387 × 24 h**. Those are shared across species and cannot be substituted for the actual station×date×hour camera on-time (the publication separately lists **29,850 functional camera-trap nights**). Our reproducible summary explicitly **does not** claim that the 9288 hours are verified physical station-specific camera exposure. The period-normalised values are descriptive detected-event timing per published period hour, NOT latent behavioral intensity.

For each taxon, the relative night/day event-detection rate is:
`(night_events/night_period_hours)/(day_events/day_period_hours)`.
For a comparison of two species, the same period-duration denominators cancel exactly. Thus, for Water deer versus Wild boar:

`[(499/4170.8181)/(264/4757.1675)] / [(172/4170.8181)/(475/4757.1675)] = (499/264)/(172/475) = 5.219895...`.

This is the **largest absolute night/day contrast among the six species pairs** in this pooled published sample, selected *after seeing the source*. It is a ratio of **observed pooled event-time ratios**, not a ratio of population abundances or an estimated conditional effect of one species on another.

Additional ecological specificity: water deer account for **61.3%** of their pooled events at night, whereas boar account for **25.1%** at night and **69.4%** by day. Water deer and wild boar show opposing detected daypart profiles. The paper's introduction cites a background literature tendency for nocturnal wild boar, but the **local Uljin pooled detection profile** is more daytime-heavy. This is a context-dependent pattern to explain, **not** evidence of a genuine behavioral reversal across sites or a causal effect of people.

## Interpretation: one supported observation and several competing biological mechanisms

**Supported, measured, new secondary contrast:** The observed whole-period water-deer-to-boar difference in relative night versus daylight event detection is about **5.22** after period-duration normalisation, and this is the strongest of the six pair contrasts. Published Table 4 independently reports the **lowest pooled KDE activity overlap** for Water deer–Wild boar (Δ4=0.653), a directionally coherent **different descriptive summary of the SAME underlying dataset**, *not a second independent biological replication*. **Do not** interpret Δ4 or its confidence interval as a 41-matched-date result.

**Possible ecological reasons to test, not established:** (i) species-specific thermal/seasonal refuge use, (ii) different habitat or trail/camera composition and landscape/human exposure, (iii) seasonal phenology/foraging, or (iv) unequal species/time-specific camera detection and passage-distance distribution. Annual `frequency_of_people` cannot represent instantaneous visitor contact; one year's pooled counts cannot isolate temperature from photoperiod or station mixing.

**Explicit competing hypotheses for the *authentic original source* once admitted:**

- **Differential diel allocation:** Within the same physical camera × same matched daylength calendar pair, Water deer have a larger night/day change between May/early June and July/August than Wild boar, **after independently verified camera hours**. This is a prospective test, NOT deducible from this supplement.
- **Stable species differences:** Whole-period night/day contrast persists but **no within-station seasonal contrast** is detectable. Would favor stable or habitat-dependent species-level differences over seasonal reassembly.
- **Station composition and detection confounding:** Pooled 5.22 can occur with little within-station differentiation if species occupy different cameras or camera sensitivities vary through the day. This remains possible without station-specific event and operation records.
- **Differential response to human use:** Requires independent temporal human activity data and explicit controls; the annual people-frequency covariate by itself cannot establish human-triggered temporal avoidance.

## Strict source and inference limitations

1. **Whole-period pooled aggregate, no station replication:** There are 82 cameras in two study regions, but this TSV has only 4×3 rows. Cannot compute a site-clustered CI, independent-station effect, within-camera species difference or a permutation test valid for the camera network. Do not compute a naive Fisher/Poisson significance p by treating 4,623 repeated detections as independent animals.
2. **Calendar period durations are not validated camera ON-time:** 9288 h equals 387×24 h, not the sum over 82 real camera deployments. The original independent operation log is still required for true 41-pair station-hour exposure and downtime.
3. **Solar definitions differ:** The supplement's civil twilight dawn/dusk category is not the planned daylight-edge category of the original H1. Never use one to claim a positive original H1.
4. **No seasonal effect identification:** The published Supplement 3 pooled rates and the published Table 3 summer-vs-winter fitted model p come from the **same broader field dataset** and different models/aggregations; they cannot jointly establish seasonal redistribution at original matched 2022 days.
5. **Detector bias and mechanisms remain unresolved:** Detector optical q, passage distance, environmental conditions, and interspecific competition cannot be inferred from these 12 rows.
6. **Post-source analysis:** Comparisons were formed after reading the public supplement. The strongest pair is a descriptive discovery, not a frozen pre-data confirmatory test.

## Reproducibility and continuation

- Exact unmodified public aggregate source: https://zenodo.org/records/21319408.
- Data-read-only checksum and privacy inspection: `scripts/inspect_uljin_published_supp3_aggregate_v0.py` with [CI 38492475055](https://github.com/zuizui0223/odsp/actions/runs/38492475055).
- Verified source-to-contrast analysis: `ULJIN_PUBLISHED_SUPPL3_DAYPART_SIGNATURE_V0_CONTRACT.json`, `scripts/run_uljin_published_supp3_daypart_signatures_v0.py` and [CI 38492757442](https://github.com/zuizui0223/odsp/actions/runs/38492757442).
- Original NIE EcoBank Source Version 1.1 **remains HOLD** in issue #265; only a genuine user-category and research-use-purpose declaration through the provider UI can complete the file acquisition. No bypass or fabricated declaration. Once authenticated raw data and operation are supplied, evaluate the **original fixed 41 paired dates** using the established camera-hour and station roster gates; never reclassify the post-publication analysis into that preregistered result.
