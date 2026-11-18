# Red-kite German GPS eligibility: fixed-stage attrition diagnostic

**Pre-result source gate:** `research/BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_CONTRACT.json`, frozen in commit `fbb244938950fe5c3c0fdfc73c24429c0c44e087` before this additional source-level diagnostic. The prior real-GPS result is permanently recorded in `BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_FIRST_RECEIPT.json` (first raw-event primary: **99 season IDs / 49 bird strings**, not paper 99/63).

## Why the funnel matters

The German public `GER_indseasondata.csv` contains **159 unique source season IDs from 63 distinct bird IDs**, while the published paper describes an earlier 163/65 sample and a final 99/63 eligibility set. The already frozen 12-rule pre-outcome GPS gate finds **99/49** under the source-event/strict->800 primary rule, with no rule reproducing **both** paper counts. We must determine whether the loss of bird strings arises before GPS matching, outside German geobounds, outside breeding season, or only at the GPS coverage threshold, instead of simply forcing a later filter to output 63.

## Ordered cumulative source-only stages

1. **S0:** all 159 distinct `year_id` strings in original German metadata, mapped uniquely to exactly one `bird_id` (not GPS eligible).
2. **S1:** those German metadata season IDs with ≥1 parseable GPS event whose `bird_id` exactly matches the metadata mapping; invalid/missing or source-foreign rows excluded.
3. **S2:** subset with ≥1 of those events at strictly latitude >50N and longitude >9E.
4. **S3:** subset with ≥1 location at the above geobounds and fixed UTC day-of-year 74 through 191.
5. **S4:** subset with **strictly more than 800** original provider GPS event rows after S3 (no new hourly thinning), matching the original first-run primary variant. No output is revised even if S4 differs from 99/49; a difference triggers source integrity HOLD.

For each stage, export *only* the total number of source season ID strings, total bird ID strings and losses since the previous stage. No real IDs or hashed identifiers, nesting status, breeding success, GPS location, GPS timestamp or per-animal tracking summary is emitted. Full 53.47 MB GPS bytes and 6.5 KB metadata bytes must match their original official MD5s. The metadata mixed outcome suffix is never parsed by the previously frozen `KeyPrefixCollector`.

These cumulative counts can locate a **data-processing discrepancy** but not demonstrate that each row is an independent biological bird, authenticate the two German source populations, or establish a novel future-bird prediction gain.

## Run

```bash
python -m pytest tests/test_bop_red_kite_ger_gps_stage_attrition_v1.py
python scripts/bop_red_kite_ger_gps_stage_attrition_v1.py --out /tmp/german-attrition.json
```

The fixed-format CI first runs offline tests for Python 3.10/3.12/3.13, then performs a single full-source read and archives a **counts-only** output or fail-closed source HOLD. Historical BOP `empirical_state_prediction_mixed` is unchanged.

## First official independent source-stage audit

The first frozen stage-funnel calculation [Actions run 44260229713](https://github.com/zuizui0223/odsp/actions/runs/44260229713), after Python 3.10/3.12/3.13 synthetic tests, **succeeded**. Original artifact ID `14407028545`; ZIP SHA256 `3e5699905f1eb82a2eaf24c8c5e6c1b6acac261c1892fd7dc20cefc53df69841`; original JSON 2,203 bytes SHA256 `2acd0ea576398b0de7a9181b2943679adc9c7e802aa011556c8ed996d2920539`. The first result is locked by `BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_FIRST_RECEIPT.json` and its independent verifier.

| Stage | Distinct season IDs | Distinct bird ID strings | Lost seasons | Lost birds |
|---|---:|---:|---:|---:|
| S0 — source metadata | **159** | **63** | — | — |
| S1 — exactly matched GPS year/bird IDs | 159 | 63 | 0 | 0 |
| S2 — at least one GPS point within strict German geo bounds | 159 | 63 | 0 | 0 |
| S3 — at least one GPS point in frozen breeding season | 159 | 63 | 0 | 0 |
| **S4 — strictly >800 locations after S3** | **99** | **49** | **60** | **14** |

Data quality and exact source-link notes: original German GPS had 500,778 physical rows; one incomplete/malformed row, 2,524 rows with year IDs not in the frozen metadata, **zero** rows with a mapped year ID but different bird ID, and 498,253 valid, correctly joined GPS rows. Both original Zenodo file MD5s were verified. These results isolate the **fixed-GPS-coverage threshold** as the stage where 60 source seasons and 14 bird strings disappear. They do not establish the original publication's biological sample selection pathway.

The publication's 99 GPS-eligible seasons across 63 birds remain **not reproduced**, despite the numerical match in eligible seasons under one already frozen source processing rule. The 163/65 initial sample also differs from the published source CSV's 159/63. Without the exact pre-archive raw-data preparation and paper-specific sample roster, the substantive cause of this discrepancy is unresolved. No real prediction gain or future-bird conformal claim is allowed.
