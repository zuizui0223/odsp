# Red-kite unfiltered biological identity projection — source-only gate

**First-access contract:** `research/BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_CONTRACT.json` was committed to GitHub as `99f32569bf7b8ee17056f1b9a4c7c90dd82e1694` **before any full individual-season CSV read for this protocol**. The older six-file metadata inventory and first-physical-line header-only checks were completed in different, frozen routes. This gate is not a new prediction result.

## Biological question

Oppel et al., *Journal of Avian Biology* (2025; DOI 10.1111/jav.03246) report **163 raw German bird-seasons from 65 birds**, reduced to **99 GPS-eligible seasons from 63 birds** using location coverage/phenology/time-step filters. Swiss training data comprise **697 eligible seasons from 258 birds**. IDs in a raw season metadata file need not be identical to the admitted cohort. The goal here is to check actual source row identities and repeated years without reading the movement records or extracting any reproductive responses.

## Exactly what is accessed

Two already documented, checksum-pinned Zenodo v1 CSVs: `GER_indseasondata.csv` (6,456 bytes) and `SUI_indseasondata.csv` (117,327 bytes). The complete CSV byte streams **do contain real outcome values** and are necessarily received to verify provider MD5 and find physical line endings. This protocol **does not claim these source bytes were never accessed**. Instead, a streaming scanner decodes only the leading key columns: German `year_id,bird_id`; Swiss `bird_id,year,year_id`. It discards all remaining body-line bytes without decoding or recording age, sex, home-range, nest, success or other outcome fields. No raw/hardened/hash-per-animal ID values, sensitive row fragments, timestamp, coordinates, probabilities or GPS event rows are written to receipts or logs. No tracking CSV is downloaded.

Raw key strings temporarily exist in the single runner process to count distinct IDs, histories and literal cross-source collisions; only aggregate counts/histograms are publicly emitted. Provider size/MD5 are checked against the previously frozen official metadata receipt, and full header lines against original first-line SHA256/CRLF. Malformed key-prefix encodings, mismatched source bytes, duplicate year_id record lines, or transfer failures cause a **HOLD**, never promoted biological inference.

## Allowed aggregate outcomes

- Physical CSV record lines (not yet an eligible-bird model sample), distinct `bird_id` and distinct `year_id` strings, number of birds with repeated recorded seasons, season-count histogram and max season count.
- Duplicate season IDs and the number mapping to multiple bird IDs; any positive duplicate count forces source identity HOLD.
- Counts of **exactly identical literal ID strings** between German and Swiss files; these can reveal naming collisions but cannot authenticate cross-country biological identity.
- Full file-size/MD5 integrity status, processing-contract digest and permanent scientific HOLD.

No German study-population identifier is declared in the original published header, so grouping into the two German populations is **not possible from this metadata alone**. Likewise the 800 GPS points/season filter and chronological independence cannot be reconstructed from this route. This protocol can check a **necessary** identity bookkeeping condition but cannot admit the 99 eligible seasons or claim novel ecological predictive gain.

## Next gated biological step after a clean source-only result

1. Separately freeze a source-native 60-minute-thinned GPS coverage/season-eligibility pipeline for Germany, explicitly reproducing the paper's geographic/phenology and 800-fix thresholds without opening nesting labels. Its output must identify 99 eligible seasons and 63 birds **or explicitly report a reproducibility gap**; do not post hoc tune a threshold to force published counts.
2. Check genuine cross-year biological bird identifiers, source reuse and the missing two-population crosswalk; raw string equality alone cannot certify independence.
3. Only then freeze which outcome is estimated (binary nest initiation or conditional fledging success), input transformations and a Swiss-trained model, training-only baseline and disjoint German adaptation/calibration/test birds before any new scoring. Published German validation is already postpublication, not a new independent biological discovery.

**Claim ceiling:** no model, no success probability, no real new-bird rank calibration, and no revised BOP verdict. Historical BOP terminal remains `empirical_state_prediction_mixed`; red-kite stays `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`.

## Local offline testing

```bash
python -m pytest tests/test_bop_red_kite_raw_group_prefix_only_v1.py
```

Official source run (only in the dedicated CI source job following successful synthetic tests):

```bash
python scripts/bop_red_kite_raw_group_prefix_only_v1.py --out /tmp/red-kite-raw-group-aggregate.json
```

## First official source-only result (18 November 2026)

Source job [#44257226379](https://github.com/zuizui0223/odsp/actions/runs/44257226379) succeeded after the original committed preaccess contract `99f32569bf7b8ee17056f1b9a4c7c90dd82e1694` and Python 3.10/3.12/3.13 synthetic tests. The exact first aggregate-only artifact is ID `14406462430`; original ZIP SHA256 `bf5b9b1bdf29acbbdfcd3ab17709c11a4307df6b7146fba5b0d8705c22e6d9da`; JSON SHA256 `efc41dacf264777d06343a283fc620a6575d2879874e1530ed00f749840e3e1e` (2,161 bytes). The official first result is pinned in `BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_FIRST_RECEIPT.json` and rechecked offline by `scripts/verify_bop_red_kite_raw_group_first_v1.py`.

| Provider metadata file | Physical lines | Distinct `bird_id` | Distinct `year_id` | Birds with ≥2 records | Largest history |
|---|---:|---:|---:|---:|---:|
| Germany | **159** | **63** | 159 | 46 | 7 |
| Switzerland | **2,866** | **553** | 2,866 | 515 | 7 |

Both provider file bytes matched the **original published full-file MD5** values, and no duplicated `year_id` values were found. The exact string overlap across German/Swiss `bird_id` and `year_id` sets was zero for both; this is **not authenticated biological non-overlap**.

**Source-versus-paper warning:** German original source metadata has **159/63**, while the paper describes **163/65 before GPS eligibility** and **99/63 after GPS eligibility**. Swiss source metadata has **2,866/553**, while the paper reports **697/258 eligible**. This is an important **documented unresolved sample-frame discrepancy**, not an error to hide by post hoc filtering. It may reflect published file preparation or screening, but the cause has not been demonstrated here. **No 99-season, 63-bird GPS-eligible roster is admitted yet.**

At the publication aggregate stage, the project still has no source-audited animal-level gain, no independent 90% group-rank calibration and no claim of a new source biological discovery. The next valid action is a separately predeclared German GPS quality/season eligibility preflight, *not* opening `nest` or `success` values.
