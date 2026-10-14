# From 457 published wildlife photos to a *conditional* species × habitat × night table

**Date:** 2026-10-14 (Asia/Tokyo)  
**Route:** exploratory secondary mathematical reconstruction of published aggregate percentages, *not* original author event data and *not* original frozen Uljin 41 daylength pairs.  
**Source:** Jeong SM, Shin KC, Kim EK (2025), *Journal of Agriculture & Life Science* 59(5), 111–118, DOI https://doi.org/10.14397/jals.2025.59.5.111, official KCI https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003260212.

## Ecological question

Does the apparent Water-deer-versus-Wild-boar nocturnal-detection difference reflect differing species-associated nocturnal photographic profiles **within** forest and wetland habitats, or partly their differing representation among the photos obtained in each habitat?

The KCI public English abstract reports **2,529 camera-trap photographs, 457 analyzed photos** of Water Deer and Wild Boar, plus one night percentage and its complement for each of **four species×habitat groups**:

| Source stratum | Published day % | Published night % |
| --- | ---: | ---: |
| Water deer, forest | 29.73 | 70.27 |
| Wild boar, forest | 29.15 | 70.85 |
| Water deer, wetland | 16.36 | 83.64 |
| Wild boar, wetland | 22.97 | 77.03 |

These are reported *image percentages*, not camera-independent behavior observations. No source event timestamps, real camera station IDs, night exposure denominators or individual-animal counts were obtained.

## An unexpected algebraic result: exactly ONE integer table under declared source assumptions

**Conditional identification assumptions (NOT independently proven by the published abstract):**

1. All 457 analyzed focal images partition into exactly the four above species×habitat groups, without exclusions, duplicate accounting, other strata or weighting.
2. The published complementary percentages are calculated from each group's positive **integer** night/day photo counts.
3. The authors used **nearest 0.01 percentage-point rounding** (not truncation or a model-based fitted percentage) on the raw proportions, with no hidden weights or editing.

Under these assumptions, for each group with total `n ≤ 457`, integer `night=k` must satisfy the exact rounding inequality:

```text
abs(100 * k / n − P_reported) < 0.005 percentage points
0 < k < n, integer n,k
```

For all four groups, the numbers of independently admissible `(n,k)` candidates are respectively **12, 10, 14, 12**. Intersecting their Cartesian product with the globally published condition `sum(n) = 457` yields **EXACTLY ONE** table:

| **Inferred, conditional** counts | Daytime photo count | Nighttime photo count | Total |
| --- | ---: | ---: | ---: |
| Water deer, forest | 22 | 52 | 74 |
| Wild boar, forest | 58 | 141 | 199 |
| Water deer, wetland | 18 | 92 | 110 |
| Wild boar, wetland | 17 | 57 | 74 |
| **Total** | **115** | **342** | **457** |

The reconstructed fractions give 52/74×100 = 70.27027%, 141/199×100 = 70.85427%, 92/110×100 = 83.63636%, 57/74×100 = 77.02703%, exactly producing the four published night percentages when rounded to two decimals.

**What is proved:** uniqueness of the integer solution *under these explicit assumptions*. **What is NOT proved:** that these are the authors' raw original counts; that each image is an independent animal event; that any camera was equally operational; or that sampling across habitats represents wildlife abundance/selection. Without the exact 457-photo partition assumption, there are many admissible counts per percentage.

## Conditional reconstructed within-publication ecological description

The reconstructed total Water-deer images are **184** (forest 74, wetland 110); Boar images are **273** (forest 199, wetland 74). In these **photo records**, the wetland representation is very different: **59.78% of Water-deer photos** versus **27.11% of Boar photos**. This is composition of recorded images only, not population habitat preference (camera deployment may differ).

Aggregating inferred counts over habitats yields Water deer 144/184 = **78.26%** night and Boar 198/273 = **72.53%** night; the photo-pool contrast is **+5.733 percentage points**. This pooled result does **not** appear directly in the original paper's quoted per-habitat night percentages and follows only from the conditional integer solution.

### Separate within-habitat differentiation and photo-habitat composition

The symmetric Kitagawa arithmetic decomposition for observed photo night fraction is:

```text
pooled_water_minus_boar =
  Σ_h (mean_species_habitat_weights_h × difference_in_night_fractions_h)
+ Σ_h (difference_in_species_habitat_weights_h × mean_night_fraction_h)

5.733397 percentage points
   = 2.541103 points (WITHIN-habitat recorded night-fraction component)
   + 3.192294 points (PHOTO-habitat-composition component).
```

Therefore **55.68% of the numerical pooled PHOTO difference** is attributed, *under this symmetric algebraic choice*, to different forest/wetland representation among the photos; 44.32% to within-habitat source photo profiles. The contributions are **not causal**, and Kitagawa decomposition choices are not unique causal counterfactuals.

If every species' photo night fraction is instead standardized to a **hypothetical 50% forest / 50% wetland** mixture, the descriptive Water-minus-Boar difference is **+3.012668 percentage points**, rather than the pooled +5.733397 points.

### Inference sensitivity: even the optimistic photograph-independent approximation is inconclusive

For the inferred table, the wetland-versus-forest *photo-level nocturnal odds ratios* are Water deer **2.1624** and Boar **1.3792**, a ratio of conditional habitat odds ratios **1.5678**.

**Only if the 457 photos were independent Bernoulli observations** (no repeated individual, burst, camera/position/time correlation), the simple unclustered Wald diagnostic would be log-OR ratio 0.44969, SE 0.48147, z 0.934, two-sided **p ≈ 0.3503**, and 95% Wald OR interval **[0.6102, 4.0283]**. This demonstrates that even an overly simple independence idealization does not resolve an interaction. It is **NOT a validated biological p-value or confidence interval**, and cannot replace station-blocked inference. Real effects and uncertainties cannot be estimated from published percentages alone.

## A separate, directly observed robustness result from Uljin

The authentic externally MD5-verified Jeon & Lim (2026) Uljin Supplement 3 uses 4 taxa × **day / civil twilight / night** whole-period event counts. Across that published *observed-count* table, allow every crepuscular record to be reassigned as night or non-night in any proportion, even differently for each species. This gives **recorded night-fraction intervals**, still without station-hour exposure correction:

| Taxon | Minimum night fraction | Maximum, all civil twilight counted at night |
| --- | ---: | ---: |
| Goral | 36.815% | 42.814% |
| Roe deer | 33.663% | 42.698% |
| **Water deer** | **61.302%** | **67.568%** |
| **Wild boar** | **25.146%** | **30.556%** |

Hence Water deer have the **highest** observed pooled night-photo fraction and Wild boar the **lowest** across all four, **under every possible species-specific reallocation of civil-twilight events**. The Water-minus-Boar pooled night-fraction difference lies between **+30.747 and +42.421 percentage points**. Goral-versus-Roe-deer ordering cannot be guaranteed by this interval method.

This is robust to a *classification convention*, **not** to species-specific detector q, unequal station representation, unverified operation hours, different seasons or recording unit differences.

## Why this matters to comparing the independent Korean field studies

Han et al. (2024) reported **autumn** Water deer night 61.9% and **day 13.9%**, Boar night 77.6% and **day 0.7%**, in *four distinct dawn/day/dusk/night classes*. If the four categories exhaust the published species' autumn percentages, the remaining dusk+dawn fractions are **24.2%** Water deer and **21.7%** Boar. Merely changing twilight inclusion can then put Water deer night share in **[61.9%, 86.1%]** and Boar in **[77.6%, 99.3%]**. These *intersect*, so the apparent opposite ranking cannot be declared invariant to species-specific twilight reclassification using the abstracts alone. If the **same proportion** of each species' twilight records were reassigned to night, the Boar–Water ordering would persist, but that common allocation is an **assumption** and may be false because species use dawn/dusk differently.

Therefore: **Uljin's rank is internally twilight-classification robust, but a biological Korean cross-study rank reversal under fully harmonized day/night definitions is NOT yet demonstrated**.

The Jeong 2025 Bukhansan survey itself uses a binary day/night division. Its original grouping and twilight boundary still need validation; do not assume it matches the 2026 Uljin civil night definition.

## Recommended ecological conclusion and next empirical step

The strongest present supported empirical question is now **whether species-specific observed timing differences persist when camera placement, night definitions and season are held constant**. Three explanatory layers need to remain separate:

1. **Published pooled event differences**: real descriptive observations (Uljin source-verified whole-year marginal tables, Bukhansan publisher percentages).
2. **Compositional sampling explanation**: mathematically possible, and in Bukhansan the conditional inferred photo-table demonstrates how differently distributed habitat photos can account for much of the pooled contrast.
3. **Within-physical-camera biological mechanisms**: untested without actual event clocks, independent hourly camera operational time, camera-q calibration, temporal visitor pressure and station/habitat identities.

The original Uljin 2022 41 astronomical calendar pairs, PR264's H1 daylight-edge definition, source-HOLD and qualified existing routes remain **unchanged**. It would be premature to claim urbanization causes boar nocturnality or that the reconstructed photos demonstrate behavioral plasticity.

## Reproducibility and evidence provenance

- Bukhansan *public article* verified in CI: https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003260212.
- Fixed post-outcome source/assumption contract: `BUKHANSAN_PUBLISHED_INTEGER_RECONSTRUCTION_V0_CONTRACT.json`.
- Exact exhaustive integer algorithm + source-data validation: `scripts/run_bukhansan_2025_public_integer_reconstruction_v0.py`.
- Tests: `tests/test_bukhansan_2025_public_integer_reconstruction_v0.py`, genuine first-party HTML + constraints checked with [CI 38582095893](https://github.com/zuizui0223/odsp/actions/runs/38582095893).
- Uljin twilight assignment bounded directly from its author-published aggregate and independently verified Zenodo ZIP: `scripts/run_uljin_published_three_phase_identifiability_v0.py` and `tests/test_uljin_published_three_phase_identifiability_v0.py`, CI on the ecology branch.
- Original EcoBank source: https://doi.org/10.22756/ETC.20260000001022, and remaining provider user-declaration/original-source admission is tracked in https://github.com/zuizui0223/odsp/issues/265.

**Evidence tier**: conditional inverse-aggregation identity, descriptive standardized photo distribution, naïve photo-independent non-significance check, and source-backed civil-twilight night-rank bounds. Not empirical habitat-selection, causal behavior or original 41-pair seasonal reassembly.


## How sensitive is the unique table to an incomplete 457-photo partition?

The full feasible count enumeration now also checks whether the **sum of the four four-group totals** might be **smaller than 457** if some of the 457 images had not been attributed to these four report groups. This is a sensitivity counterexample ONLY, not evidence that any such image was actually excluded.

With the identical published rounded percentages and the same numerical integer constraints, **the first different four-group solution appears if seven photos are allowed to remain outside the four groups**, so their group totals sum to **450 rather than 457**:

| Hypothetical alternative **if 7 of 457 photos lie outside four groups** | Reconstructed total | Reconstructed night |
| --- | ---: | ---: |
| Water deer, forest | 74 | 52 |
| Wild boar, forest | 247 | 175 |
| Water deer, wetland | 55 | 46 |
| Wild boar, wetland | 74 | 57 |
| **Four-group total** | **450** | **289** |

The remaining hypothetical **7 photos** are **not observed or assigned** to any actual author category. This alternative only proves that the four-group exhaustiveness assumption is consequential. Under its 450-photo four-group subset, the pooled Water-minus-Boar nighttime photograph difference would be **+3.695 percentage points** instead of the first solution's +5.733 points.

Thus the accurate formulation is: **conditional UNIQUE integer inversion IF all 457 photographs partition the four source groups**, not “we discovered the original 457-photo counts.” The source paper's actual group totals, any weighting and any exclusions still need author-file confirmation for literal raw-data identity. The expanded [CI 38583206793](https://github.com/zuizui0223/odsp/actions/runs/38583206793) reproduces this seven-photo sensitivity and re-verifies the original KCI article text.
