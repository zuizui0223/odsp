# NestTool 2024 archived package source-code parity: prospectively frozen code-only check

## Fixed provenance boundary

Before downloading the archived package ZIP, the exact source-code-only contract was committed as `research/BOP_RED_KITE_2024_PACKAGE_CODE_V1_CONTRACT.json` at **`be5623ac3680e89d2023d576003e6a28982a789d`**. The two authorized provider files, both published by [Oppel et al. on Zenodo record 13736049](https://zenodo.org/records/13736049), are:

- `NestTool-1.0.0.zip` — exactly **6,578,763 bytes**, provider MD5 `b172b87191f00f221e9d0151c61d65a6`.
- `NestTool_archived_full_analysis.r` — exactly **26,930 bytes**, provider MD5 `f3878bd76bd851d0ea048950ee84e8f9`.

The historical reference is the **28 August 2024** [Vogelwarte/NestTool R/data_prep.R](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/R/data_prep.R) at pinned commit `8fdf3884b5f6079afdffdc5c563c9050766670a4`, Git blob SHA1 `3fa42eddbfb852d5dbc29364281bffef8410563e`. This is a dated source reference, not an assertion of historical runtime equivalence.

## What is actually checked

1. Read the entire two **code-only** provider files into volatile memory and verify published exact byte length and MD5, plus a pinned historical Git blob's exact SHA1. **No `.csv`, tracking, biological label, model or other data file is downloaded.**
2. Inspect ZIP directory entries without extracting any binary or data files. Decompress only source files inside `/R/` with `.R`/`.r` extension, within predeclared uncompressed-size limits. Require exactly one normalized `R/data_prep.R` member. Reject traversal paths, unexpected duplicate data-prep sources and source-code decode failures.
3. Compare the 2024 archived `R/data_prep.R` bytes with the 28 August 2024 GitHub version. Report separately **exact byte identity** and **equality after CRLF→LF normalization**. Keep both source SHA256 and Git blob SHA1 so line-ending differences are not mistaken for identical bytes.
4. Search only fixed static code patterns for the GPS `year_id`-grouping, `>800`/`>=800` semantics, `floor_date`, thinning/resampling/3600-second hints, and the archived script's unfiltered versus post-filtered German bird-count operations. Output **only pattern labels and bounded line numbers**, never entire code or tracked bird records.

## Result interpretation

- `PACKAGE_CODE_EXACT_GIT_MATCH`: same bytes for this one source file only. It does **not** certify original 2024 execution environment, archived German data preprocessing, tag identity, or a replicable 163/65 starting cohort.
- `PACKAGE_CODE_EOL_ONLY_DIFFERENCE`: only CRLF/LF differs in that one source file. This does not establish identity of *every* R package function.
- `PACKAGE_CODE_DIFFERENCE`: a substantive difference between the archived code file and dated GitHub reference may affect the exact historical eligibility calculation; compare static structural evidence before calling it relevant.
- `SOURCE_PACKAGE_CODE_HOLD`: unverified provider code/integrity, ZIP layout or restricted access. This is not a successful code parity result.

The previously frozen `GER_indseasondata.csv` has **159 year IDs / 63 bird-ID strings**. Independent source-level seasonal-GPS filtering yielded **99 seasons / 49 bird-ID strings**, with 60 seasons and 14 bird strings lost at the fixed >800 threshold. The original article states **163 seasons / 65 birds** before filtering and **99 seasons / 63 birds** after. This code audit cannot by itself make these populations equivalent. The documented archived unfiltered `length(unique(GERseasondata$bird_id))` line could explain the published 63 but **is not proven to be its source**.

**Scientific terminal stays:** original BOP `empirical_state_prediction_mixed`, Dryad `NOT_ADMITTED`, red-kite biological `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`.

## Offline tests

```bash
python -m pytest tests/test_bop_red_kite_2024_package_code_only_v1.py
```

Official single-source code audit runs in GitHub Actions after Python 3.10/3.12/3.13 synthetic tests. All source errors are archived as a named source HOLD.

## First official original ZIP test: exact source-file identity

First official [GitHub Actions run 44288291609](https://github.com/zuizui0223/odsp/actions/runs/44288291609) **succeeded**, following all three Python 3.10/3.12/3.13 offline synthetic tests. Original source job ID `134746762799`; first source artifact `14420740820`, ZIP SHA256 `b9aa6ae7ef7b687adbc368405b630963ecfccfda07b4f16a144efd65208e2fe9`, first 2,665-byte JSON SHA256 `bb5a0a9251c4396b71caa239046b48de7996b03807ebad9f9677f473604775f9`. These are preserved by `BOP_RED_KITE_2024_PACKAGE_CODE_V1_FIRST_RECEIPT.json` and `scripts/verify_bop_red_kite_2024_package_code_first_v1.py`.

- Source `NestTool-1.0.0.zip`: provider MD5 matched; original ZIP SHA256 `ce9737f120aaf039d8252525a9a96d869c3975030f5bf3960c8d86615455bdc9`; **13 R source files**, 146,094 uncompressed R source bytes. No model RData/RDS or other binary entries extracted.
- **Critical: archived ZIP's `NestTool-1.0.0/R/data_prep.R` has exactly the same bytes as the dated 28 Aug 2024 GitHub `R/data_prep.R`**, Git blob SHA1 `3fa42eddbfb852d5dbc29364281bffef8410563e`, source SHA256 `d398cddb6bc6b2ef7453618ac20a3e57e654777db35114a06a35683911e532cd`. This checks the eligibility-implementing source *file*, **not** identity of all package files or execution of the original paper's runtime.
- Archived exact `data_prep.R` contains `number_of_fixes > minlocs` at **line 163** and day-of-year filter at **line 108**. The original top-level script's archived-file MD5 matched and has the unfiltered `length(unique(GERseasondata$bird_id))` expression on **line 501**.
- **Correction of PR #289:** earlier postpublication source-audit materials assigned the above unfiltered expression to line **486**. The actual original Zenodo byte-verified script locates it at **501**, a 15-line discrepancy. The older audit remains as an archived historical statement; use this original-file correction as the authoritative line locator. Statements about earlier extracted line numbers for nearby `GER` script blocks must be rechecked independently before precise citation.
- Static search for explicitly named hourly thinning operations (`floor_date`, `round_date`, `3600`, `60 min`, `60min`, `subsampl`) returned no matching R-source snippets in the bounded scan; generic `thin` matches include English words such as *within* and are **not evidence of a 60-minute preprocessing function**. Thus the upstream 5–45 minute-to-hourly standardization reported in the paper is **not reconstructed**.

**What changes:** the prior uncertainty about historical package `data_prep.R` compatibility is resolved to an exact source-byte match. **What does not:** original 163/65 cohort provenance, `99 seasons / 63` eligible birds, individual-level exchangeability, upstream GPS hourly sampling, or genuine red-kite predictive gain. The source-only 99/49 remains the supported filtered count.
