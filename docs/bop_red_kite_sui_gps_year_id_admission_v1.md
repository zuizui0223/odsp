# Swiss red-kite source GPS quality and biological-group multiplicity

**Freeze before access:** `research/BOP_RED_KITE_SUI_GPS_YEAR_ID_ADMISSION_V1_CONTRACT.json` committed at `4826226d4f3ac6d1f3af74191b0e6ebf53fb027f` on 19 Nov 2026, before this route's first Swiss source-GPS read.

## Scientific purpose

Oppel et al. (Journal of Avian Biology, DOI 10.1111/jav.03246) report **697 Swiss bird-seasons from 258 birds**, with 488/209 year-ID training/test rows and up to seven seasons per bird. The checksum-verified deposited `SUI_indseasondata.csv` instead contains **2,866 unique year IDs / 553 bird-ID strings before GPS filtering**. A paper count is not an authenticated training roster.

PR #293 confirmed the exact original 2024 ZIP's three NestTool training functions split on `year_id`, not `bird_id`. Its expected 67.463–146.540 birds represented in both roles is a **sharp range of expectations over unknown histograms**, not an actual split or measured accuracy bias. This gate attempts to recover the source's qualified bird-season multiplicities **without opening reproductive responses**.

## Frozen twelve-arm screening, not posthoc fitting

The paper specifies Swiss latitude strictly >45°N, longitude strictly >4°E, 11 March to 24 June and hour-scale sampling. The dated 2024 R source uses UTC ordinal DOY and `number_of_fixes > minlocs`; the upstream hourly downsampling implementation remains unknown. **Before data access**, we froze a 2 × 3 × 2 grid:

- Two seasons: fixed-2023 UTC DOY 70–175; or actual calendar March 11–June 24 (different in leap years).
- Three sampling schemes: all source events, one per UTC hour bin, or sorted rolling ≥3,600-second selection.
- Two GPS thresholds: >800 from dated R implementation, and ≥800 from paper wording.

Every arm is reported regardless of whether its two counts equal **697 seasons/258 birds**. The predeclared primary descriptive arm is fixed-DOY × unique UTC hour bin × >800, **not** a claim to reproduce the authors' original thinning. Count matching is not an identity or model-admission certificate.

## Exactly what is accessed

| Frozen source | Provider bytes | Provider MD5 | Parsed fields |
|---|---:|---|---|
| `SUI_indseasondata.csv` | 117,327 | `91394907a2d036e3dbacf5cd4f70475b` | Leading `bird_id,year,year_id` ONLY |
| `SUI_trackingdata.csv` | 266,416,454 | `f654300e9a77b8dc41221f44d468ea2c` | `bird_id,year_id,timestamp,long_wgs,lat_wgs` ONLY |

The mixed-response metadata CSV inevitably contains HR/nest/success bytes in transport for full-file MD5, but the prefix-only parser **never decodes the outcome suffix**. The GPS scanner uses coordinates and times transiently for filtering; it never exports any individual or hashed IDs, GPS positions, exact dates/timestamps, or track histories. No Movebank login, model RData or animal outcome values are accessed. Provider MD5, exact original header SHA256 and one-to-one year→bird identity are required. Failures are source HOLD.

## Methodological response (no biology prediction)

For each frozen arm, publish total eligible season IDs, distinct bird-ID strings, season multiplicity histogram (number of birds with 1,2,... eligible seasons), and the **expected** number of birds appearing in both roles under an explicitly hypothetical uniform year-ID train/test split of approximately 70/30. If a cohort has N season rows, n training rows and h_k birds with k seasons, its expected shared-bird count is sum(h_k*[1-falling(n,k)/falling(N,k)-falling(N-n,k)/falling(N,k)]).

This is conditioned on the *source* histogram; it is **not** the realized 2024 random split. An exact numerical match to 697/258 does not verify historical row identities, canonical animals, or forecast accuracy; the nest-success model uses a different smaller response-conditioned subset.

**Scientific terminals unchanged:** original ODSP BOP `empirical_state_prediction_mixed`; red-kite new-outcome and external-gain `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`; historical BOP Dryad `NOT_ADMITTED`.

## Reproducible run

```bash
python -m pytest tests/test_bop_red_kite_sui_gps_year_id_admission_v1.py
python scripts/bop_red_kite_sui_gps_year_id_admission_v1.py --out /tmp/sui-source-only.json
```

First official GitHub Actions source run is gated on Python 3.10/3.12/3.13 synthetic safety tests, with an aggregate-only first-result artifact even on source HOLD.

## Original first real-data result — *published Swiss totals matched by a frozen source screen*

The official [GitHub Actions first run #44456757144](https://github.com/zuizui0223/odsp/actions/runs/44456757144) completed successfully after all synthetic Python 3.10/3.12/3.13 tests. Source job ID `135336383906`, original immutable source artifact ID `14498950985`, ZIP SHA256 `5db9468c76f294ed2f6f339fb2bb5d1bb56109fc7a17be529161fefe7a63bdeb` (1,464 bytes), and aggregate-only original JSON SHA256 `c1fc25a81d2285d0751e4e8b9ef5c85dda0d4e9252a56a464373c3b4dff18a5a` (10,573 bytes). The pre-access contract SHA256 was `52ca9198aa3b6a7f5282186e437c99340f28b03c55ac01c7ef17dbe2d6f01993`. Both original Swiss source-file provider MD5s matched.

Original provider GPS: **2,395,531 physical records**, zero malformed, zero unknown or mismatched bird/year IDs in the archived metadata mapping; 390,753 linked GPS records outside the strict geographic bounds. After geographic and source-season filters: **1,138,761 GPS events from 967 year-ID strings** for the fixed 2023 DOY rule (actual calendar variant: 1,140,949 events / 967 year IDs). These are source-quality counts, not labels.

All **twelve** predeclared quality rules were reported:

| Swiss date rule | GPS time rule | >800: eligible seasons / bird-ID strings | ≥800: eligible seasons / bird-ID strings |
|---|---|---:|---:|
| Fixed UTC DOY 70–175 | Raw provider events | **697 / 258** | **697 / 258** |
| Fixed UTC DOY 70–175 | Unique UTC clock hours | **697 / 258** | **697 / 258** |
| Fixed UTC DOY 70–175 | Rolling ≥3,600 seconds | 620 / 246 | 621 / 246 |
| Calendar March 11–June 24 | Raw provider events | **697 / 258** | **697 / 258** |
| Calendar March 11–June 24 | Unique UTC clock hours | **697 / 258** | **697 / 258** |
| Calendar March 11–June 24 | Rolling ≥3,600 seconds | 622 / 246 | 623 / 246 |

**Eight of twelve** source-defined choices numerically reproduce *both* paper-reported 697 Swiss seasons and 258 birds; no rule was selected after looking at the outcomes. The primary was fixed UTC DOY × unique UTC hour × strictly >800, as preregistered. The rolling-hour screen is materially stricter and gives only 620–623 seasons/246 IDs, confirming why the unknown original downsampler must not be presumed to be a particular greedy method.

### Real source bird-season multiplicity (primary source screen)

| Eligible seasons per bird-ID string | Bird-ID strings |
|---:|---:|
| 1 | 66 |
| 2 | 51 |
| 3 | 62 |
| 4 | 56 |
| 5 | 20 |
| 6 | 2 |
| 7 | 1 |
| **Total** | **258 IDs; 697 season rows** |

**192 of 258 source bird strings have ≥2 eligible seasons.** Replacing PR #293's unknown-histogram envelope with this actual source histogram gives the conditional expected number of distinct source bird IDs on both sides of a **hypothetical, uniform 488-training / 209-testing year-ID split**:

**E[shared bird-ID strings | source histogram, uniform 488-of-697 year-ID partition] = 121.992374.**

This is a *mathematical expectation conditional on the original archived source group's actual multiplicity*, not the original authors' realized bird overlap, not a probability that exactly 122 birds were shared, not a biological-independence certificate, and not an estimate of predictive-accuracy inflation. It lies within the previously proven sharp range 67.462949–146.540230, which did not use the source histograms.

### The starting-sample discrepancy remains

The paper describes 697 eligible seasons plus **336** with insufficient data, for **1,033** nominal seasons considered in that stage. The source GPS has **967** year IDs with any in-season GPS and loses **270** at the fixed primary >800 screen, despite matching the published 697/258 eligible counts. The difference of **66** between published excluded seasonal episodes and the source's 270 quality-failing in-season year IDs is not resolved here: source records with no in-season locations, prior data selection, and the precise 2024 hourly preprocessing remain possible explanations. **Do not assert a literal historical 2024 source-row crosswalk merely from matching numerators.**

### Frozen result and safe reproduction

`BOP_RED_KITE_SUI_GPS_YEAR_ID_ADMISSION_V1_FIRST_RECEIPT.json` preserves the entire first original counts-only source JSON, documented first Actions ZIP/JSON hashes, source-group histogram and scientific claim limits. An **offline-only** verifier checks all twelve arm totals, every histogram's internal sums and each hypothetical expectation without downloading any GPS again. Post-first CI was switched from live source to only synthetic tests and immutable original-result verification, so subsequent commits do not trigger another 266 MB source request.

**Original ODSP BOP mixed result, nest-success restricted response subset, Swiss→Germany external verification and new red-kite biological predictor HOLD are unchanged.**