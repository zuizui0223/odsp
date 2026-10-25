# What prevents the independent GPS test from establishing seasonal generality?

**2026-10-19 | ODSP PR #267 | Post-outcome identifiability audit, NOT a new speed-effect test.**

## Evidence and reproducibility

The audit re-downloads the original seven-duck-species source (van Toor & Waldenstrom 2025, DOI https://doi.org/10.5281/zenodo.16940654), verifies MD5 `1972d0ef08b83c2b88a169ba07bb48b3`, and first reproduces the **entire original GPS v0 numerical result byte-for-byte**, SHA256 `557c21c6446556f16c24ccf496b0b2c7ea8e22c259830a9e9a764faec10e5e8b`. No original effect, matching rule, threshold or source cohort is replaced.

[Verified workflow 39187640044](https://github.com/zuizui0223/odsp/actions/runs/39187640044) passed all five diagnostic tests, including exhaustive comparison of maximum matching to brute force on all 512 possible 3-by-3 bipartite graphs, before processing the real source. It verified 294,683 original rows and 181 marked individuals (study name plus individual ID), reproduced the original 36-bird preliminary cohort and nine-bird final outcome cohort, and archived aggregate-only JSON in artifact `duck-gps-identifiability-audit-20261019` (artifact ID 12158244345).

Audit JSON SHA256: `34dca961aca6952d5ab2e3d706380e323ba9c8031aa591194072e2df8c475afa`.

## 1. Why 36 preliminary birds became nine analyzable birds

The following reasons partition the **original 36-bird preliminary cohort**. For an animal with multiple individual-by-cell-by-solstice groups, the audit reports the farthest stage reached by any originally preliminary-qualified group. These are sample-opportunity failures, not negative ecological outcomes.

| Farthest stage / unresolved requirement | Distinct birds |
|---|---:|
| Too few dates with at least three DAY and three NIGHT readings in both branches | **17** |
| Enough day/night dates, but fewer than five one-to-one pairs within the original five-minute photoperiod caliper | **7** |
| Astronomy supports at least five pairs, but per-zone falling/rising fix-count balance 0.5–2 does not | **3** |
| Enough valid pairs exist but the original greedy pairing prevents the five-pair threshold | **0** |
| Included in unchanged v0 | **9** |

All nine final birds belong to the preliminary cohort: no final animal was silently added from outside that original 36-bird set.

Among mallards, eight of the 13 preliminary birds fail the day/night sampling condition, four fail photoperiod overlap, and one fails fix-count balance. The absence of a final mallard contrast therefore does **not** mean mallards show no seasonal response.

The included birds originate from two named source studies: **four** from `Dabbling duck migration Bangladesh 2019-2022`, and **five** from `Dabbling duck migration Portugal 2018--2022`. These are source recruitment/study names, not a demonstration of independent ecological regions or the exact places the birds occupied during comparisons. No animal locations or individual IDs are disclosed.

## 2. Does a better date-pairing algorithm recover enough replication?

The previous protocol uses deterministic nearest-daylength greedy matching. Greedy matching need not maximize the number of pairs: the audit verifies this with known-truth examples, then computes an outcome-blind maximum-cardinality matching on the **same candidate edges**, preserving the five-minute caliper, day/night sample minimum, balance ratio, one-to-one date use and five-pair group requirement.

Across all local groups, including those below the five-pair group threshold, the original procedure finds **232** pairs. Maximum-cardinality matching permits **246** pairs, an additional **14** across five local groups. These totals are not the 186 date pairs in the nine accepted v0 individual-groups.

Despite the extra pairing capacity, the number of potentially eligible individuals remains **nine**, with the **same per-species counts**. Thus pairing efficiency is worth documenting but does not solve the present lack of multi-species replication. No alternative-pair speed effects were calculated, and no original matched date was changed.

## 3. The chosen speed endpoint is predominantly zero

The original v0 outcome compares medians of log(1 + GPS ground speed) within each individual-region-date and solar DAY/NIGHT block. On the **unchanged accepted v0 dates**, the audit finds:

| Source taxon | DAY/NIGHT date blocks with median zero | All such blocks | Zero-median fraction |
|---|---:|---:|---:|
| Northern pintail (`Anas acuta`) | 212 | 228 | **93.0%** |
| Northern shoveler (`Anas clypeata`) | 39 | 40 | 97.5% |
| Eurasian teal (`Anas crecca`) | 32 | 32 | 100% |
| Garganey (`Anas querquedula`) | 52 | 52 | 100% |
| Gadwall (`Anas strepera`) | 374 | 392 | 95.4% |
| **All accepted v0 samples** | **709** | **744** | **95.3%** |

There are **7,850** sensor readings in these selected blocks, of which **6,442 (82.1%)** report zero speed. Neither a reported sensor zero nor a positive sensor reading is by itself a validated behavioral state. The median can remain zero even when several nonzero readings occur. Consequently the previous zero contrasts in teal and garganey are arithmetic consequences of zero block medians; they do not establish absence of seasonal changes in occasional movement, flight frequency, distance traveled or activity budgets.

The small positive pintail result remains numerically unchanged. It describes differences between typically near-zero instantaneous-speed medians in five tagged birds; it must not be translated into a percentage change in time spent active.

### Timestamp-quality caveat

The source contains **256** repeated study-individual timestamp rows. Only **two** such extra rows occur within the accepted v0 day/night blocks, both in the teal sample. The present audit reports these occurrences; it does not automatically deduplicate or claim that their removal leaves all eligibility conditions unchanged. A future analysis must define how repeated and potentially discordant measurements are handled before treating row counts as distinct sampling opportunities. This does not affect the count of repeated timestamps in the pintail accepted blocks, which is zero.

## 4. Revised scientific decision

The present external data do **not** support an inference that animals generally preserve their time use at equal daylength, nor a general seasonal shift. Two limitations are now separated quantitatively:

1. **Observation support**: dates on opposite seasonal branches do not necessarily supply comparable daytime and nighttime measurements. The effective individual sample stays at nine even under optimal matching of the original admissible dates.
2. **Measurement target**: a median of mostly zero instantaneous GPS speeds is poorly suited to detecting changes in the occurrence of brief or infrequent movement events. It may still be a valid descriptor of typical sampled speed; that is a narrower question than diel activity allocation.

The observational Serengeti photo/NDVI results remain unchanged. The independent GPS exercise remains a separate sensor pilot rather than validation of the mammal camera effect.

## 5. Next falsifiable ecological design

For new data, distinguish two pre-specified observational questions at matched photoperiod and within individual/location:

- Does the **probability of a movement event at a scheduled observation** change between seasonal branches or solar phases?
- Conditional on such an event, does its **speed or displacement** change?

A movement-state definition must come from independent tag calibration or linked accelerometry, not a speed threshold chosen to maximize a seasonal effect in this dataset. Scheduled-fix or accelerometer opportunities, missing-fix/battery histories, duplicate handling, local solar-date conventions, and relocation/deployment intervals must be available. These allow the observation process to be represented rather than inferred from successful fixes alone. Brief high-speed events and feeding/walking behavior also require different sensor-resolution validation; none should be inferred merely from a nonzero GPS reading.

Select additional study populations by **both-branch within-individual sampling support and independent observation protocols before reviewing effect signs**, not by total point count or number of listed species. Determine the required number of individuals from a pre-specified biologically meaningful effect and desired precision using an independent pilot or design simulation; do not treat the earlier n=5 descriptive floor as a powered population design.

This is a protocol direction for new, independently validated measurements. No two-part model was fitted and no revised positive ecological result was manufactured from the current source.

## Files and status

- `scripts/audit_duck_gps_identifiability_20261019.py`
- `tests/test_duck_gps_identifiability_audit_20261019.py`
- `.github/workflows/duck-gps-identifiability-audit-20261019.yml`
- [Verified run](https://github.com/zuizui0223/odsp/actions/runs/39187640044), aggregate-only artifact as above.

PR #267 remains Draft. Original Serengeti, Rhode Island, Uljin, vegetation and GPS numerical outputs remain immutable. This follow-up changes the interpretation of what the GPS measurement can test, not the archived numerical findings.
