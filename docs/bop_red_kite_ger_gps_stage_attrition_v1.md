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
