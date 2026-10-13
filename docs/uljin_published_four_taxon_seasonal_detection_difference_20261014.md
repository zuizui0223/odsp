# Ecology first: published four-ungulate summer detection divergence
**Analysis date:** 2026-10-14 (Asia/Tokyo)  
**PR:** #264, **route:** post-publication exploratory, original 41-pair animal inputs remain **HOLD**.

## Scientific question and evidence tier

Do the four sympatric ungulates exhibit equivalent broad summer-vs-winter **fitted station-season detection** responses in published occupancy examples, and which species contrast remains separated even under fully unknown cross-species coefficient error correlation?

**External empirical source:** Jeon J-H & Lim A (2026), *Biodiversity Data Journal* 14:e191556, Table 3 (https://doi.org/10.3897/BDJ.14.e191556 ; readable https://pmc.ncbi.nlm.nih.gov/articles/PMC13379711/). We have **not** fitted any coefficient to the real source event ZIP ourselves.

Table 3 supplies species-wise best-model detection submodel \`p ~ log_effort_z + season\`, whose \`is_summer\` coefficient is relative to **winter** (summer June-August vs winter December-February). It is a **conditional logit detection probability** coefficient; NOT observed hourly detections, optical q, occupancy \`ψ\`, individual activity, physical activity-time phase, or abundance. The goral's selected occupancy model was M2, and the three other taxa were M1. This is not the immutable ODSP 2022 41-pair early-growing-season (May 1-June 10) vs midsummer (July 1-August 31) design.

| Taxon (published) | Best model | Summer logit-p β | Published SE | Published 95% CI |
|---|---|---:|---:|---:|
| Goral | M2 | +0.886 | 0.636 | [-0.361, 2.134] |
| Water deer | M1 | +1.234 | 0.378 | [0.493, 1.974] |
| Roe deer | M1 | +0.030 | 0.369 | [-0.693, 0.754] |
| Wild boar | M1 | −0.888 | 0.247 | [-1.372, −0.404] |

## Valid uncertainty target and exploratory calculation

Let β_i be one published species-specific fitted summer-minus-winter coefficient and s_i its published standard error. For a comparison d_ij=β_i−β_j, the covariance **cannot** safely be assumed zero, because taxa were sampled at shared stations. Cauchy–Schwarz bounds all mathematically permitted correlations:

\[
\operatorname{SE}(d_{ij})^2=s_i^2+s_j^2-2\operatorname{Cov}(\hat\beta_i,\hat\beta_j)\leq (s_i+s_j)^2.
\]

Thus \(s_i+s_j\) is the upper bound for the difference SE, without needing or inventing the cross-species covariance. Under the explicit **approximate joint normal with valid published SE** assumption only, calculate two-sided conservative p-values using \(z_{\min}=|d|/(s_i+s_j)\). Control exploration over **all six unordered contrasts** using Bonferroni: p_FWER ≤ min(1, 6 p_bound), and an approximate simultaneous 95% family-wise interval uses \(z_{1-.05/(2*6)}=2.638257273\).

| Contrast (first minus second) | Difference in published β | Upper bound of SE | Conservative p after 6-pair Bonferroni | Approximate simultaneous 95% interval |
|---|---:|---:|---:|---:|
| Goral − Water deer | −0.348 | 1.014 | 1.0000 | [−3.023, 2.327] |
| Goral − Roe deer | +0.856 | 1.005 | 1.0000 | [−1.795, 3.507] |
| Goral − Wild boar | +1.774 | 0.883 | 0.2672 | [−0.556, 4.104] |
| Water deer − Roe deer | +1.204 | 0.747 | 0.6421 | [−0.767, 3.175] |
| **Water deer − Wild boar** | **+2.122** | **0.625** | **0.004115** | **[+0.473, +3.771]** |
| Roe deer − Wild boar | +0.918 | 0.616 | 0.8169 | [−0.707, 2.543] |

The **sole surviving difference** under these stated assumptions is Water deer vs Wild boar. Exp(2.122)≈**8.348** is a ratio of **model-based seasonal detection odds ratios**, *not* an 8.348-fold abundance, detection count, occupation or activity change. The wide family-wise interval exp([.473,3.771])≈[1.60,43.42] highlights remaining imprecision.

This is a new **secondary mathematical comparison** of published coefficients, not an independent ecological observation or demonstration of a causal mechanism. The six-way multiplicity correction covers post hoc selection among these six pairwise comparisons given the reported asymptotic models, but does **not** incorporate uncertainty from model selection, survey detection heterogeneity, occupancy identifiability, common-site sampling beyond the correlation bound, fitted marginal means, or possible specification errors. Compare only the similar M1 Water deer and Wild boar terms for the surviving result; Goral M2 has particularly unstable occupancy coefficients as warned in the source paper.

## Ecological questions that remain testable, not yet results

1. **Seasonal use of the observation process:** Why is summer-vs-winter conditional \`p\` higher for Water deer but lower for Wild boar? Could species-specific movements, ecology, detectability, vegetation occlusion, or local abundance generate this? These explanations are not distinguished by Table 3.
2. **Within-day redistribution at matched daylength:** In the immutable 41 early-growing-vs-midsummer 2022 matched pairs, does independently effort-adjusted Water deer vs Wild boar event allocation shift between daylight core, daylight edge and night at identical physical stations? Test only after authentic source event dates AND complete station×hour operation logs are admitted.
3. **Biological vs camera confounding:** Would a temporal-shift interpretation survive reference-based physical camera detector q and distance-mix transport checks, and cross-station heterogeneity? Retain zero-event site-date/species cells; selection of sites is exclusively pre-event operation availability.

No evidence here for direct sun/thermal entrainment, interspecific competition, thermoregulation, actual time-shift, or photoperiod-driven mechanisms. Repeated site-season values are not independent biological replicates unless modeled accordingly.

## Reproducibility

- Frozen **after seeing published data**: \`ULJIN_PUBLISHED_TABLE3_SEASONAL_SPECIES_CONTRAST_V0.json\`.
- Exact standard-library reanalysis: \`python scripts/run_uljin_published_table3_species_contrasts_v0.py\`.
- Dedicated regression tests: \`python -m pytest -q tests/test_uljin_published_table3_species_contrasts_v0.py\`.
- Passing CI: https://github.com/zuizui0223/odsp/actions/runs/38424926466.
- Original source issue: #265. The original NIE EcoBank ZIP, independent hourly operation and detector q are still **unverified**, so **do not promote this result to original 41-pair empirical H1/H2/H3**.
