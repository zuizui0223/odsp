# Red kite: 2024 archived code versus paper and immutable source cohort counts

**Status: postpublication code/provenance reconciliation, not a new biological result.** This audit reads only immutable, counts-only ODSP receipts. It never opens GPS, breeder outcomes, individual identifier strings or per-bird probabilities.

## Executive finding

**Source-code line correction (2026-11-18):** A subsequent checksum-verified read of the original Zenodo archived R script places the unfiltered `length(unique(GERseasondata$bird_id))` at **line 501, not line 486**. The original `data_prep.R` inside `NestTool-1.0.0.zip` was confirmed *byte-identical* to the pinned 28 Aug 2024 GitHub source. This correction supersedes the approximate line label in the original audit matrix, which remains retained as historical evidence. The whole package runtime, 60-minute preprocessing and 163/65 source frame are still unverified. See [`BOP_RED_KITE_2024_PACKAGE_CODE_V1_FIRST_RECEIPT.json`](../BOP_RED_KITE_2024_PACKAGE_CODE_V1_FIRST_RECEIPT.json) and [code-only audit](bop_red_kite_2024_package_code_only_v1.md).


The published article by Oppel et al. (*Journal of Avian Biology*, first published 17 October 2024, DOI [10.1111/jav.03246](https://doi.org/10.1111/jav.03246)) reports 163 original individual-seasons from 65 German birds and 99 GPS-eligible seasons from 63 birds. Yet the exact official [Zenodo v1 archive](https://zenodo.org/records/13736049) (24 Sep 2024, data MD5 checked by ODSP) contains **159 distinct `year_id` / 63 `bird_id` strings**. The previously frozen code-aligned source eligibility yields **99 seasons / 49 bird-ID strings** after geographical, seasonal and strictly >800-source-GPS-fix conditions. A separate fixed-stage audit showed the loss of **60 seasons / 14 bird strings occurs entirely at the GPS coverage threshold**; there was no loss of distinct source IDs from requiring any GPS, German coordinates or breeding-season presence.

| Count stage | Paper-reported | Frozen Zenodo v1 source/ODSP result | Difference |
|---|---|---|---|
| Original (before 800-fix eligibility) | 163 seasons, 65 birds | **159 seasons, 63 ID strings** | Paper +4 seasons, +2 birds |
| Eligible after GPS quality filters | 99 seasons, 63 birds | **99 seasons, 49 ID strings** | Same season count, paper +14 birds |

**The match at 99 seasons does not identify the 63 birds**, and 99 seasons are not 99 biologically independent validation groups. The source-filtered result supports at most 49 independent animal-ID strings *before* authenticated canonical identity or population checks. The paper's accuracy results were already published; this is not a new NestTool prediction validation.

## New original-code evidence explaining where 63 might have come from

The authors' archived [complete R analysis script](https://zenodo.org/records/13736049/files/NestTool_archived_full_analysis.r?download=1) is labelled finalised 29 Aug 2024 (Zenodo MD5 `f3878bd76bd851d0ea048950ee84e8f9`). Lines 295–315 load the archived **two GER files** directly, then call `data_prep()` with latitude=50, longitude=9, `minlocs=800` and 2023-defined breeding-period day-of-year boundaries. It contains no visible separate hourly-resampling function call in that German top-level block.

Crucially, line **501** is the **unfiltered** `length(unique(GERseasondata$bird_id))`. Its result for the verified archived season CSV would be **63**, exactly the same number reported as the *eligible* German birds in the article. Immediately following, lines 487–494 do filter `GERseasondata` by `year_id` membership in `GER_data_input$summary$year_id` for the supplemental German age/sex table. Thus an unfiltered count and a filtered sample-size operation coexist in the deposited code. **This is a concrete candidate for the provenance of '63'; it does not establish that the authors actually copied this unfiltered number into the paper or that the paper contains an error**. Differences between the archived source and the originally analyzed material remain possible.

An independently dated [28 Aug 2024 GitHub snapshot](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/R/data_prep.R) at commit `8fdf3884b5f6079afdffdc5c563c9050766670a4`, file blob `3fa42eddbfb852d5dbc29364281bffef8410563e`, verifies that the 2024 `data_prep` implementation first restricts geography (lines 94–102), then day-of-year (line 108), and admits a `year_id` only when `number_of_fixes > minlocs` (lines 161–163). The paper describes **at least 800**, while this dated code uses a strict >800 threshold. ODSP's already-frozen comparison of >800 and >=800 had **no effect on the 99/49 count**, so boundary wording does not explain the 14-bird discrepancy.

**Version limit:** This GitHub source is a dated near-publication snapshot; it is *now byte-verified for `R/data_prep.R` against* the archived `NestTool-1.0.0.zip` package. The archived top-level script also does not reconstruct its own prior 60-minute thinning: either source tracking data were already pre-thinned or an upstream process is not represented in that script. Nothing here proves which.

## Independent pieces of frozen ODSP evidence

- `BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_FIRST_RECEIPT.json`: source `GER_indseasondata.csv` 159 season lines / 63 distinct bird strings; original MD5 verified; no reproductive fields decoded.
- `BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_FIRST_RECEIPT.json`: original `GER_trackingdata.csv` 500,778 physical GPS lines, full provider MD5 matched, 12 fixed season/thinning/threshold rules; primary source-event route yields 99/49; no posthoc rule selection.
- `BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_FIRST_RECEIPT.json`: source key join and successive spatial/season conditions all retain 159/63; the strict >800 gate leaves 99/49. No raw animal IDs or exact positions exported.
- `research/BOP_RED_KITE_2024_PAPER_SOURCE_COUNT_AUDIT_V1.json`: machine-readable published/code/source evidence matrix and exact unverified claims.

## Decision

1. **Code provenance confirmed:** historical author script directly reads the two official GER CSVs; contemporary GitHub `data_prep` uses strict >800 group count; the archived script contains an unfiltered German `bird_id` count and a separately filtered supplement calculation.
2. **Empirical source-count inconsistency confirmed:** 99/49 under the predeclared, source-audited rule differs from paper's 99/63; original 159/63 source differs from the article's 163/65 input description.
3. **Author explanation unresolved:** 63 may have been copied from an unfiltered raw count, but that is a hypothesis. Verifying the exact Zenodo v1 package code, upstream 60-minute preprocessing and the original 163/65 sample roster could resolve the discrepancy.
4. **Stop inference:** no fixed source-authenticated 63-bird group roster, probability gains, conformal lower bounds or new ecology result. Keep `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`; original BOP `empirical_state_prediction_mixed` and Dryad `NOT_ADMITTED` unchanged.

## Reproduce (offline, no provider access)

```bash
python -m pytest tests/test_bop_red_kite_2024_paper_source_count_audit_v1.py
python scripts/audit_bop_red_kite_paper_source_count_path_v1.py --out /tmp/bop-red-kite-count-provenance-v1.json
```

