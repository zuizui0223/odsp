# Red kite candidate: provider metadata only, *different biological state target*

**Status:** frozen SOURCE-ONLY inventory prior to provider API access; **no
animal-year files, GPS positions, breeding labels or physiological/altitude
response data are to be downloaded** under this contract.

## Why examine this source?

The first independent-bird BOP method paper has an unresolved empirical
question: whether a truly separate, auditable biological group-level
calibration/validation source could ever be admitted, rather than merely
making the synthetic rank method pass.

A public red-kite (*Milvus milvus*) data release associated with
Oppel et al. (2024/2025; doi:10.1111/jav.03246) contains two national
populations, originally evaluated for reproducing nesting/breeding
status from GPS movements:

- Switzerland: the authors reported 324 GPS-tracked birds; 258 with
  sufficient data contributing 697 individual-seasons to training.
- Germany: 65 tracked birds; 63 eligible birds and 99 individual-seasons
  in the paper's previously published external evaluation.

Data release [Zenodo record 13736049](https://zenodo.org/records/13736049),
DOI 10.5281/zenodo.13736049, described in
Oppel et al.'s public data availability statement.

This is a **plausible future ecological-state demonstration**, not an
independent held-out validation of the historical four-class BOP
*altitude* random forest. It instead would require a NEW,
prospectively frozen **binary nest-attempt or breeding-state**
estimator and reference, with per-animal grouping across repeated
breeding years. In fact, the source publication has already evaluated
the German response values, so any later ODSP test could claim at best
a separately sealed analyst-level model test, **not unprecedented
biological discovery**.

## Pre-access inventory contract

`research/BOP_RED_KITE_SOURCE_INVENTORY_V1_CONTRACT.json` was committed
before the first official Zenodo API request. Its only authorized read
is the **one JSON metadata document**:

`https://zenodo.org/api/records/13736049`

The six frozen expected filenames and their official Zenodo published
MD5 manifest strings are:

| Name | MD5 | Restricted role |
|---|---|---|
| `SUI_indseasondata.csv` | `91394907a2d036e3dbacf5cd4f70475b` | Contains nesting response values — do not open |
| `GER_indseasondata.csv` | `bdf5445971195ca8cc27760d242b1563` | Contains nesting response values — do not open |
| `SUI_trackingdata.csv` | `f654300e9a77b8dc41221f44d468ea2c` | GPS tracking data — do not open |
| `GER_trackingdata.csv` | `ec5dd057fc6d704a09f15bbbffe00129` | GPS tracking data — do not open |
| `NestTool-1.0.0.zip` | `b172b87191f00f221e9d0151c61d65a6` | Historical code — do not open |
| `NestTool_archived_full_analysis.r` | `f3878bd76bd851d0ea048950ee84e8f9` | Historical source analysis — do not open |

These MD5s are **provider metadata values** until actual file content
is separately downloaded. The present source-only route **does not
verify file bytes**. If any filename/checksum differs, it stops
with `SOURCE_METADATA_ACCESS_OR_VERSION_HOLD`, without adjusting the
precommitted expected list after seeing the source.

Only if the exact source record, DOI, six file manifest entries,
publication flag and checksum strings match does the source-inventory
status become `SOURCE_FILE_INVENTORY_VERIFIED_ONLY`. The biological
scientific status **always** stays

`HOLD_NEW_NEST_STATE_TARGET_AND_AUTHENTIC_GROUP_ROSTER_NOT_YET_FROZEN`.

No new bird sample is admitted, no proper score is computed and
**this inventory cannot be used as a negative or positive predictive
result**.

## First official API-only inventory result — confirmed

The first [official GitHub Actions run 40636304599](https://github.com/zuizui0223/odsp/actions/runs/40636304599)
verified the exact record ID, DOI, publication flag and **all six
provider-published file names, MD5 manifest strings and sizes**.
No outcome-bearing individual-season CSV, GPS CSV or code archive was
downloaded. The Zenodo license metadata specifies **CC BY 4.0**.

Original source metadata JSON SHA256:
`15938986f1966543b22722f38ff0d4e7c95134bbc6c157d691ef129eef2f0b46`.
The first 2,403-byte result JSON SHA256:
`9f7de00fa42ccbb5ac68924fdf121e271882629a1c7730b598b24f82d1b19ebe`.
GitHub Actions artifact **12792739938**, ZIP SHA256:
`109fe897235724db921f0c1cdcbbec7c2f504dc501e0e4dc2126a92dc62bd966`.
The permanent first receipt:
`BOP_RED_KITE_SOURCE_INVENTORY_V1_FIRST_RECEIPT.json`.

| File role | Verified published manifest size |
|---|---:|
| German individual-season status **and response values** (unopened) | 6,456 bytes |
| Swiss individual-season status **and response values** (unopened) | 117,327 bytes |
| German GPS events (unopened) | 53,471,439 bytes |
| Swiss GPS events (unopened) | 266,416,454 bytes |
| Archived NestTool package (unopened) | 6,578,763 bytes |
| Prior analysis code (unopened) | 26,930 bytes |
| **All six manifest entries** | **326,617,369 bytes** |

The verified source-inventory category is
`SOURCE_FILE_INVENTORY_VERIFIED_ONLY`. The mandatory, separate
**biological** terminal remains
`HOLD_NEW_NEST_STATE_TARGET_AND_AUTHENTIC_GROUP_ROSTER_NOT_YET_FROZEN`.
**MD5 manifest matching is not equivalent to MD5-checking downloaded
data-file bytes**, because this analysis deliberately never opened
those files.

The first official result can be replayed with
`scripts/verify_bop_red_kite_source_inventory_v1.py`: its checks
bind the saved result to first-run ZIP and JSON hashes, source record,
the exact six advertised MD5 strings/sizes, original source-selection
commit and the same no-outcome/no-external-inference classification.

## Separate scientific prerequisites before any future outcomes

1. **New prediction target and training model**: whether the
   outcome is home-range existence, nest initiation or breeding
   success is a *different estimand* from BOP altitude. Establish
   exact data-field mappings, a prespecified comparable probability
   baseline and a reproducible learner.
2. **Animal-level independence**: 697 Swiss and 99 German
   individual-*seasons* are repeated observations of 258 and 63
   animals, not 796 independent calibration gains. A prospective
   design needs entity ID crosswalks over time and source, plus
   disjoint model-training, calibration and final test birds.
3. **Source and site structure**: two German regions are not one
   exchangeable ecological population by default. Calibrate and
   test in a defensible nested target group/population, or report
   the population-level assumption honestly without claiming
   universal group exchangeability.
4. **No untouched-original-study claim**: the German group
   outcomes and predictive results were already analyzed in the
   original published paper. The new ODSP analyst may seal response
   values for a separately frozen workflow, but cannot describe the
   dataset as an unprecedented, previously unstudied test.
5. **Model evidence versus interval coverage**: a 90% group-rank
   lower limit's marginal coverage can be valid despite negative
   expected biological predictive gain. A positive probability gain
   requires an empirically positive bound and external assumptions,
   not merely sufficient group count.

**Original BOP scope unchanged:** 30 birds, 27/30 positive historical
RF gains, terminal `empirical_state_prediction_mixed`; same-study
v2026 group-count gate closed; Schaub 2026 Dryad original RF remains
`NOT_ADMITTED`; MH_WATERLAND/H_GRONINGEN new individual 90% group
rank remains HOLD. None is reclassified by this source search.

## Reproduction

```bash
python -m pytest tests/test_bop_red_kite_source_inventory_v1.py
python scripts/bop_red_kite_source_inventory_v1.py --out /tmp/ODSP_RED_KITE_SOURCE_METADATA_ONLY.json
```

The second command reads only the exact Zenodo **record metadata API**,
and preserves a HOLD even if rate-limited or offline. No file name
may be translated into a GPS or outcome download in this route.
