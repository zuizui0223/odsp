# BOP: Swiss NestTool internal validation splits seasons, not animals

**Role:** frozen source-code inspection plus sharp, *conditional mathematical expectation*; NOT an observed reanalysis of birds or new model accuracy. This is a methodological ODSP result, not an RSDS ecological result.

## Scientific question

Do the 2024 NestTool training functions select **bird-year** groups or independent **biological birds** when constructing internal training and test sets? If distinct years from the same individual can appear in both roles, what can be concluded about the expected number of repeated animals **from published summary counts alone**, without opening bird identifiers or outcomes?

Oppel et al. ([*Journal of Avian Biology*, DOI 10.1111/jav.03246](https://doi.org/10.1111/jav.03246)) report 697 Swiss red-kite breeding seasons from 258 birds, with 1–7 seasons per bird; 488 seasons trained and 209 season rows internally validated. They state use of a 70% random training fraction. This is **not** the Germany cross-population external-validation data (99 seasons reported; original paper claims 63 German birds, but the fixed Zenodo source has only 49 bird-ID strings eligible under the audited primary GPS rule). The success outcome has a smaller, conditional training subset and **must not be assigned 697-season overlap numbers**.

## Before-code source freeze

Frozen contract `research/BOP_NESTTOOL_2024_YEARID_SPLIT_ANIMAL_OVERLAP_V1_CONTRACT.json` was committed on 18 Nov 2026 at `3b50495405731eec92f925654740cb13906b316a` **before first access to the ZIP copies of the three trainer files in this route**. The source is the exact official Zenodo code archive `NestTool-1.0.0.zip` (6,578,763 bytes, provider MD5 `b172b87191f00f221e9d0151c61d65a6`, previously independently verified SHA256 `ce9737f120aaf039d8252525a9a96d869c3975030f5bf3960c8d86615455bdc9`). Its three `/R/train_*.R` files are compared to the dated [28 August 2024 Vogelwarte/NestTool commit](https://github.com/Vogelwarte/NestTool/tree/8fdf3884b5f6079afdffdc5c563c9050766670a4) using exact Git blob SHA1 and byte equality.

The code-only access does **not** download the original Swiss/German tracking CSVs, sex/age/outcome tables, RData models or split member IDs; only published R source files are decompressed. There is no training, prediction, validation accuracy or real-identity linkage in this route.

### Exact historical source checks

| Dated 2024 R trainer | Split variable | Historical location |
|---|---|---|
| [`train_home_range_detection.R`](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/R/train_home_range_detection.R) | `unique(trackingsummary$year_id)` | lines 69–75 |
| [`train_nest_detection.R`](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/R/train_nest_detection.R) | `unique(trackingsummary$year_id)` | lines 69–75 |
| [`train_nest_success.R`](https://github.com/Vogelwarte/NestTool/blob/8fdf3884b5f6079afdffdc5c563c9050766670a4/R/train_nest_success.R) | `unique(nestingsummary$year_id)` | lines 95–101 |

In each code, the 70% training subset is selected by sampling `year_id` values, and other `year_id`s become the test set. The archived ZIP member parity must also be checked before making a categorical statement about which code the 2024 archived package contains. **A season-independent split is not necessarily an animal-independent split.**

## Sharp finite-population expectation for an unknown repetition histogram

Let a bird appear in exactly (k) distinct seasonal rows. For a uniform choice of 488 training rows without replacement from 697 rows, the remaining 209 are test rows. Then

\[
p_{\mathrm{both}}(k) = 1 - \prod_{j=0}^{k-1}\frac{488-j}{697-j} - \prod_{j=0}^{k-1}\frac{209-j}{697-j}.
\]

The expected number of distinct birds represented on both sides is \(\sum_{k=1}^{7}h_k p_{\mathrm{both}}(k)\), where **unknown** bird-season counts must satisfy \(\sum_k h_k=258\) and \(\sum_k k h_k=697\). The function is strictly discretely concave over k=1..7 under these source parameters. Thus the *minimum* expected overlap is attained by concentrating repeat seasons as much as possible, and the *maximum* by spreading them as evenly as possible.

| Extreme | Feasible distribution of 258 birds / 697 seasons | Expected birds appearing in both roles |
|---|---|---:|
| **Minimum** | 184 birds observed once; 1 bird twice; 73 birds seven times | **67.462949** |
| **Maximum** | 77 birds twice; 181 birds three times | **146.540230** |

The bounds are **sharp for the given aggregate constraints and uniform random season split**: both configurations satisfy exactly 258 birds, 697 seasons and ≤7 seasons/bird. The bounds do not require a sample of actual bird IDs, GPS events, model predictions or biological responses. They do **not** imply that the realized historical split actually mixed at least 67 individuals; an observed split can differ from the expectation. Also, they are **not** confidence intervals and say nothing about the magnitude, or even direction, of any model-accuracy bias.

## Implication for ODSP methodology

NestTool's published Swiss internal-validation accuracies (home range 99.5%, nesting 95.2%, nest success 80.5%) were reported **per bird-season**. The first two use a 697-season dataset and the published 488/209 season split; the conditional breeding-success subset has a different denominator. If there was cross-year bird overlap, these Swiss figures do **not** by themselves establish accuracy on *previously unseen birds*. The cross-country Swiss→Germany external-validation accuracy is a distinct test and **is not invalidated by this year-level split alone**; the separate German published 99 seasons/63 birds versus archived-source 99/49 discrepancy still prevents confirming the eligible independent-group roster.

ODSP should continue requiring exact *biological bird* disjointness and within-population training/calibration/test grouping before any future-group coverage claim. An actual Swiss bird-level holdout analysis would require a new, prospectively frozen eligibility roster and model replay. It has **not** been performed here.

## Reproduction

```bash
python -m pytest tests/test_bop_nesttool_2024_yearid_animal_overlap_v1.py
python scripts/bop_nesttool_2024_yearid_animal_overlap_v1.py --out /tmp/nesttool-yearid-split-audit.json
```

Source-code ZIP verification runs once after Python 3.10/3.12/3.13 offline tests in a dedicated Actions job. CI outputs only historical byte digests, split-pattern line numbers and the conditional expected-overlap bounds; it never exports actual animal IDs or data.

## Official first source-code and mathematical-result verification

The first dedicated code-only source job in [GitHub Actions run #44307730106](https://github.com/zuizui0223/odsp/actions/runs/44307730106) succeeded, after Python 3.10/3.12/3.13 known-truth tests passed. The source job ID was `134819982555`; the source artifact ID was `14429691808` (`bop-nesttool-yearid-animal-overlap-first`), with exact ZIP SHA256 `48c7a408f08f7a9a5aa7d85ff6347617cb738c0e16db0641ee6c45d3c7d07fee` (1,577 bytes) and original JSON SHA256 `f2617e20b3a16b089a365ed8257e3011d56b013933294d0c480b5ef919b38f60` (4,657 bytes). The input-contract SHA256 was `fe7332979ba7320968c19a60752ac1592fd5b760c2c03ee3708e3ce6321bcbde`.

**All three archived trainer files matched the pinned 28 August 2024 GitHub R sources byte-for-byte.** The original Git blob SHA1 values and split lines were independently checked:

| Archived 2024 trainer | Git blob SHA1 | Unique season IDs | Randomly select season IDs | Train/test filters |
|---|---|---:|---:|---|
| `R/train_home_range_detection.R` | `47c7b5f6dbcfb53c2df8a014a65fe59cf8a258dd` | 69 | 70 | 73/75 |
| `R/train_nest_detection.R` | `c028e728e0fdf646c3bf6f46e10b3ae6b8f55bcd` | 69 | 70 | 73/75 |
| `R/train_nest_success.R` | `c657973023308201cc11c2fa0c8830fd6655ec5b` | 95 | 96 | 99/101 |

Thus it is **not merely a contemporary-code inference**: the exact official 2024 archived training functions sample **`year_id`**, not **`bird_id`**, for their internal training/test set. This establishes a potentially shared biological animal across the two season-held-out roles. It does **not** prove that the authors' saved 2024 random draw actually contained any particular number of repeated birds.

The original code-only first result independently computes **67.462949–146.540230 expected shared bird IDs** over all feasible 1–7-year repetition histograms for 258 birds / 697 seasons and uniformly sampled 488/209 season rows. The original source's counts and byte fingerprints are preserved in `BOP_NESTTOOL_2024_YEARID_ANIMAL_OVERLAP_V1_FIRST_RECEIPT.json`, and `scripts/verify_bop_nesttool_2024_yearid_overlap_first_v1.py` detects changes to code identity, sharp bounds or biological claim limits. In particular, the original model's nest-success training subset and all published Germany outcomes were **not** opened or re-estimated.

**Access control after the successful first source:** the dedicated Actions workflow has been switched to **offline-only** checks. This preserves the originally successful ZIP-source evidence without repeated downloads. No model RData/RDS, source GPS, breeding labels or individual names were accessed here.
