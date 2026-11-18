# German red-kite archive GPS sampling cadence: fixed source-only interval audit

## Question and frozen data-access boundary

Does the **original, checksum-pinned** `GER_trackingdata.csv` in the official [Oppel et al. Zenodo v1 archive](https://zenodo.org/records/13736049) already have roughly one record per 60 minutes, or does it retain shorter within-season GPS intervals? This addresses whether the paper's description of 5–45-minute logger schedules standardised to 60 minutes is visible in the **deposited source itself**. It cannot identify how the authors resampled before depositing the source.

Before this new GPS timestamp pass, the contract `research/BOP_RED_KITE_GER_GPS_CADENCE_V1_CONTRACT.json` was committed at **`903a85501371e6d8294cf0cb29125046da0eeb07`**. The exact known official original GPS MD5 `ec5dd057fc6d704a09f15bbbffe00129` (53,471,439 bytes) and German metadata MD5 `bdf5445971195ca8cc27760d242b1563` (6,456 bytes) are reused. The upstream BOP source 159/63→99/49 count/source receipts, first official five-stage audit and verified 2024 R-code byte parity are left unchanged.

## Frozen method

1. Read only `bird_id`, `year_id`, `timestamp`, latitude and longitude from the original seven-column `GER_trackingdata.csv`; use the existing response-suffix-blind German metadata key projection. **No `HR`, `nest`, `success`, age or sex values are opened.**
2. Include only timestamped GPS events linked to the authentic *source ID string pair* (`year_id`,`bird_id`) with longitude strictly >9E, latitude strictly >50N and UTC ordinal day-of-year 74–191. These match the previously frozen original-source primary eligibility branch.
3. Form two **predeclared** sets: (A) all 159 source seasons with ≥1 such event, and (B) the primary **strictly >800** event set, previously 99 source season IDs/49 bird strings. Never post hoc choose another cohort based on the interval results.
4. Within each season only, sort the UTC timestamps and count differences of consecutive recorded fixes. Zero-time duplicates are counted separately; every strictly positive interval is assigned to one of **9 fixed bins**: 0–5, 5–15, 15–30, 30–45, 45–55, 55–65, 65–75, 75–120 and ≥120 minutes. Report gap counts, proportion of gaps <55min/<60min, number of source season IDs with any <55min gap, and pooled nearest-rank 10th/50th/90th quantile in minutes.
5. All original source checksum and linked-cohort count checks must pass. Source failures produce a durable `HOLD_GER_SOURCE_GPS_CADENCE`, not an hourly sampling conclusion.

## Evidence and limits

A positive count of intervals **under 55 minutes** in the archived 99-season cohort is direct evidence that its timestamp stream was **not already strictly standardized to one observation per 60 minutes**. It does not prove that the paper used these exact unthinned event sequences to train NestTool; the original training/validation input may differ from the archived file. Even zero short gaps would be compatible with several unknown upstream interval-selection algorithms.

Individual IDs, hashed IDs, actual dates, timestamps, GPS positions, biological outcomes and per-animal histories are not printed or archived. All reported histograms are whole-cohort aggregates. Passing an interval audit does not repair the paper's **99 seasons/63 birds** versus source **99 seasons/49 bird-ID strings** denominator discrepancy, validate the 163/65 original population, or create new model log-score gains.

**Biological terminal:** `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`; original BOP `empirical_state_prediction_mixed` and Dryad `NOT_ADMITTED` remain unchanged.

## Offline source-safety tests

```bash
python -m pytest tests/test_bop_red_kite_ger_gps_cadence_v1.py
```

After Python 3.10/3.12/3.13 synthetic success, a dedicated GitHub Actions job reads the exact provider CSVs and emits only the fixed interval aggregate or source HOLD.

## First real provider-result: source CSV is *not* strictly hourly

The [first official GitHub Actions run #44290699238](https://github.com/zuizui0223/odsp/actions/runs/44290699238) succeeded after all Python 3.10/3.12/3.13 synthetic safety tests. Original provider MD5s matched, and the output consisted solely of source-wide timing histograms. Original source job `134755815277`; artifact ID `14421093958`; ZIP SHA256 `558af84440cb0fb792814c5d4eeb6394fc768cce5732fa7da63060c2556913fb` (1,265 bytes); JSON SHA256 `77b375496f01a010487c13b8277a89373a60f41e72b24913634aea0db6381167` (2,922 bytes). Both are pinned by the **original-first-result receipt** `BOP_RED_KITE_GER_GPS_CADENCE_V1_FIRST_RECEIPT.json`.

| Fixed source cohort | Linked seasons | Distinct bird-ID strings | Source GPS events | Strictly positive within-season consecutive gaps | Gaps <55 min | Gaps <60 min | Gaps 55–65 min | Seasons with any gap <55 min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All source-linked GPS seasons | 159 | 63 | 236,989 | 236,830 | **46.3619%** | 61.3985% | 37.0629% | 109 |
| Frozen primary GPS-eligible cohort (>800 event rows) | 99 | 49 | 210,420 | 210,321 | **48.7398%** | 64.9550% | 39.2557% | 67 |

The eligible-cohort median gap is **59.03 min** (nearest-rank q10=30.00 min; q90=95.00 min). The full source-linked cohort median is 59.60 min (q10=30.00, q90=179.85). These are *pooled consecutive gap distributions* and not per-bird independent effect estimates.

| Gap bin (minutes) | All 159 seasons | Eligible 99 seasons |
|---|---:|---:|
| 0–5 | 85 | 74 |
| 5–15 | 201 | 186 |
| 15–30 | 925 | 867 |
| 30–45 | 103,681 | **96,527** |
| 45–55 | 4,907 | 4,856 |
| 55–65 | 87,776 | **82,563** |
| 65–75 | 1,842 | 1,470 |
| 75–120 | 6,281 | 4,764 |
| ≥120 | 31,132 | 19,014 |

**Interpretation:** the exact archived German GPS source **unambiguously contains a large number of consecutive within-season location intervals shorter than one hour**. Therefore the public `GER_trackingdata.csv` is *not itself* a fully one-observation-per-hour-standardized stream. It is consistent with a mixed logger cadence or source preselection; the mechanism cannot be inferred from these timing counts alone.

Under already-frozen alternative eligibility rules, the raw-event threshold gave 99 seasons/49 bird strings, one-per-UTC-hour gave 90/46 and rolling ≥3,600 s gave 83/44. Therefore **a source-event threshold that happens to reproduce 99 seasons does not independently validate the article's described 60-minute processing or its eligible 63-bird group count**.

**Important guardrail:** absence or presence of short intervals in a published source cannot establish whether the authors trained models on that exact same unthinned stream, when thinning occurred or which historical algorithm was used. We have not accessed the original nest/HR/success labels or performed any animal-level score gain. The paper's 163/65 starting population, reported 99/63 eligible population, exact German site/population crosswalk and authentic independent-animal roster remain unreconciled. Scientific terminal remains HOLD.
