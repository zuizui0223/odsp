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
