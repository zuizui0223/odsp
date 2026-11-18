# Red kite Germany: frozen GPS-season eligibility sensitivity (pre-outcome)

**Pre-GPS access contract first committed:** `6520f133694a78991f0fcc28c323b3d98a3f31d3`, in `research/BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_CONTRACT.json`. This is a strictly source-only quality-gate following the exact 159 raw German season rows and 63 bird IDs in merged [PR #286](https://github.com/zuizui0223/odsp/pull/286).

## Why eligibility needs a separate source gate

The original Oppel et al. 2025 paper (https://doi.org/10.1111/jav.03246) describes **163 seasons from 65 German red kites**, and then **99 seasons from 63 individuals** after GPS downsampling, German season and >=800 fixes/season criteria. The archived `GER_indseasondata.csv` is independently verified at **159 physical season rows and 63 ID strings** (full provider MD5). That raw set neither reproduces the paper's original 163/65 nor identifies the final eligible 99/63.

The publicly available **current** Vogelwarte/NestTool repository (snapshot blob `6374114f56374022b36e122bf058b02d53fdcd20` for `R/data_prep.R`) filters latitude >50, longitude >9, ordinal days-of-year constructed from 2023, and uses **strictly >800** fixes. The paper says *at least* 800. The current GitHub validation script (blob `0bbd3b94c447a7308d5b079a494c58164859e6cc`) is not verified to be identical to the frozen Zenodo v1 code from August 2024, and the original 60-minute thinning implementation is not yet reproducibly identified. We therefore predeclare a **sensitivity screen**, not an exact reproduction.

## Twelve rules fixed before opening the source GPS file

- Geographic scope: strictly longitude >9 degrees E and latitude >50 degrees N; only events whose `year_id` and `bird_id` strings are present in the pinned original German metadata key source are considered.
- Season definition (2): fixed 2023 UTC ordinal days 74 through 191, or actual calendar UTC dates March 15 through July 10 inclusive. In leap years these are different.
- Sampling definition (3): count all observed archive events, retain one per UTC clock-hour bin, or retain sorted events at least 3,600 seconds apart.
- Minimum season fixes (2): strictly >800 (later GitHub code) or inclusive >=800 (paper wording).

The predeclared primary descriptive route is **fixed-2023 ordinal × all provider events × strictly >800**, because it matches the selection operation visible inside current `data_prep` *if* the provided source tracking events have already been hourly pre-thinned. All twelve counts must be returned without selecting whichever matches 99/63. None can be promoted to an exact original NestTool replication without verifying original upstream transformations.

## What the CI runner may do

The official source job may download the frozen Zenodo `GER_trackingdata.csv` (**53,471,439 bytes**, MD5 `ec5dd057fc6d704a09f15bbbffe00129`) and the already verified 6,456-byte German individual-season metadata for key-only inclusion checks. It necessarily parses real GPS timestamps and positions **inside the restricted runner**, but prints and archives only whole-source hashes, totals and the 12 row-count/unique-bird-count results. **No precise coordinates, event times, raw or hashed animal IDs, individual-year rosters, nesting labels, species models or forecast probabilities are published or scored.**

Original German metadata has known outcome columns (`HR`,`nest`,`success`). They are not decoded by the previously frozen prefix-only reader; the GPS tracking CSV itself has no outcome fields in its original header. A source file or checksum drift, malformed GPS schema, inconsistent year-to-bird mapping, or blocked provider access is a source **HOLD**.

**Biological claim ceiling:** a matching count would be a descriptive precondition only, never proof of the same 99 individual-seasons or 63 specific birds, biological exchangeability, independently new Germany validation or future-animal model gain. The original ODSP BOP endpoint remains `empirical_state_prediction_mixed`, the red-kite endpoint remains `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`.

## Offline tests and source job

```bash
python -m pytest tests/test_bop_red_kite_german_gps_eligibility_v1.py
python scripts/bop_red_kite_german_gps_eligibility_v1.py --out /tmp/german-gps-eligibility-v1.json
```

Only the GitHub Actions official source job, after synthetic safety tests on Python 3.10/3.12/3.13, is authorized for initial GPS access. All failures save a diagnostic-only artifact.
