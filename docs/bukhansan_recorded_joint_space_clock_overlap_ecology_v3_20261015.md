# Bukhansan: does co-detection in space lead to divergence in detection time?

**2026-10-15 | Source-verified post-publication ecological reanalysis | ODSP PR #264**

## Biological question

When Water deer (*Hydropotes inermis*) and Wild boar (*Sus scrofa*) are photographed in the same Bukhansan camera network, is their *observed* space×time distribution discrepancy mostly tied to which camera records each species, or do distinct clock-zone distributions emerge **within** these same cameras? A second question asks whether cameras with more balanced two-species record abundance show more different local time profiles, as might be predicted by an untested temporal-segregation alternative.

These questions are exploratory. The author study does not measure interspecific competitive interactions or actual co-presence in the same hours.

## Empirical source, protected identifiers, analysis grain

Jeong, Shin & Kim (2025), *Journal of Agriculture & Life Science* 59(5):111–118, DOI https://doi.org/10.14397/jals.2025.59.5.111, original full-text [author PDF](https://www.researchgate.net/publication/397496454_Daily_Activity_Patterns_of_Wild_Boars_and_Water_Deer_in_Forest_and_Wetland_Habitats_of_Bukhansan_National_Park_Implications_for_Human-Wildlife_Conflict_Mitigation). Printed Tables 1–2 (p.114–115; source PDF pages 4–5) contain separate **11 published camera station codes × 24 reported clock-hour row frequencies** for both target species; Tables 3–4 contain published night/day group totals. These source tables were visually checked and previously reduced to three *post-publication* clock-row windows while preserving all 11 public camera codes and verifying the original 24 published per-species time margins, four habitat totals and 457 original events.

**Input preserved in ODSP:** `BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json`, derived public species×camera counts for 01:00–06:00 (6 printed labels), 07:00–18:00 (12 printed labels), and 19:00–24:00 (6 printed labels). No original photo frames, GPS positions, date-labelled records or full verbatim hourly table are re-released. The source's original **day/night** division used daily sunrise/sunset, but the new **three clock-label groups do NOT represent solar phases**. In particular `07to18` has twice the duration of `01to06` or `19to24`. Thus the analysis compares **proportions of registered events**, NOT per-hour latent activity rates. The different widths do not violate the *probability mass* overlap identity, but prevent reading the 3-bin distribution as a fine-scale chronotype or species activity density.

The 11 camera codes are 9 forest and 2 wetland. From published source totals, `N_W=184` and `N_B=273`. The same photo can contain multiple animals; deduplication and camera independence do not establish independent species encounters. No independently calibrated camera on/off or optical q is present. Actual competition, human use, temperature and seasonal shift remain unmeasured.

## Reanalysis target: source-detected joint probability, not inferred movement

Normalize each species' **whole published camera×clock table** by its own total:
`p_species(site,window)=n_species(site,window)/sum_site,window n_species`.

For the two species' distributions, define the finite-bin empirical overlap
`O(p,q)=Σ_cells min(p(cell),q(cell))=1−TV(p,q)`.
This is Schoener-style **record-distribution overlap**. It is NOT the kernel-based temporal `Δ4` from Jeon & Lim 2026 or from the Jeong et al. original paper. They have different supports and estimands.

| Source-based distribution being compared | Water–Boar overlap O | Observed total-variation mismatch 1−O |
| --- | ---: | ---: |
| **Camera only** (11 published source codes) | **0.652114** | **0.347886** |
| **Clock only** (the 3 grouped published source-row windows) | **0.914397** | **0.085603** |
| **Camera × clock** (all 33 published joint source cells) | **0.615464** | **0.384536** |

**Ecological observation:** These species have very similar **pooled three-bin clock-record distributions** but substantially less similar **spatial camera-record distributions**; their joint recorded space×clock distribution has still lower overlap. This is evidence for observed network-level spatial heterogeneity as an important component of *where and when detections are registered*, not a demonstrated species' niche separation, competition, segregation or habitat effect.

### Exact decomposition; check order dependence and noncausality

By marginalization, `O_joint ≤ min(O_camera, O_clock)`. The original 11-camera count record supports both exact arithmetic paths:

- **Camera then clock:** joint TV `0.384536 = 0.347886 (camera TV) + 0.036650 (additional TV after resolving clock within camera)`. Thus **90.47%** of the observed joint *record-distribution discrepancy* is already visible when only station labels are retained, and **9.53%** more appears when distinguishing the three clock blocks. These percentages are not causal/ecological contribution shares.
- **Clock then camera:** joint TV `0.384536 = 0.085603 (clock TV) + 0.298933 (additional TV after resolving camera within clock)`. The very different first-stage shares show explicitly that these are *order-sensitive decompositions of total variation*, not unique “mechanism attribution.”
- **Order-symmetric numerical bookkeeping:** average the site contribution across the two paths and likewise clock contribution; the resulting additive values are **0.323409 site (84.10% of joint recorded mismatch)** and **0.061126 clock (15.90%)**. Even this symmetric allocation is **not causal**: it is computed from empirical detected records in **11 site classes versus only 3 time classes**, whose granularity differs substantially; site-specific detector q and observation effort are unobserved. This is a descriptive answer to *record-distribution accounting*, not evidence that 84% of behavioral competition is spatial.

### Where is the small extra clock differentiation located?

The extra `O_camera−O_joint=0.036650` can be decomposed by original published camera code *without inventing a location*. Only two camera codes supply a positive contribution at the three-bin resolution:

| Public camera | Habitat | Additional recorded overlap loss from distinguishing clock blocks | Fraction of extra loss |
| --- | --- | ---: | ---: |
| **G19** | Forest | **0.032151** | **87.72%** |
| M1 | Wetland | 0.004499 | 12.28% |
| Other 9 camera codes (including M2) | Mixed | 0 at this specific normalized-overlap resolution | 0 |

**Important contrast with ODSP's earlier source-count Mantel–Haenszel result:** M2 supplied about 64% of an *early-vs-late species×camera conditional count score*, but **G19** is the main camera contributing to *joint normalized site×3-clock-window overlap refinement*. These are distinct mathematical/ecological observational estimands; this is not a contradiction and demonstrates that choosing one metric can change the apparent 'critical' site. G19 has 45 published Water-deer and 61 Wild-boar records, so unlike sites with a single Water-deer record, it has reasonably populated **observed photo cells**, albeit not independent animals. G19's **within-camera, three-window conditional record overlap** is **0.8095**, compared with M2 **0.8279**, M1 **0.8978**, G4 **0.8992** and G22 **0.9048**.

The zero extra overlap loss for M2 does **not** mean its species have the same activity distribution; it results from marginal species camera-record fractions and the pointwise minimum, in which the lower species' relative cell mass remains the limiting mass in all three windows. A different metric or time resolution can produce a different dominant station.

## Direct test of the ecological co-detection / clock-partition prediction

Define *observed species-balance* at each co-detected camera as `2 min(N_Wsite,N_Bsite)/(N_Wsite+N_Bsite)`, not wildlife presence or ecological encounter. Define a separate *local clock-record overlap* within that site by normalizing each species to its **own** total at the site and summing the minimum of the three reported clock-bin proportions.

For the seven source cameras with both species recorded, an exploratory Spearman rank correlation of species-record balance versus local 3-bin clock overlap is **+0.464**. With an outcome-known minimum of **five recorded events per species** at a camera (excluding sparse G12 and G21; retaining 5 sites), the rank correlation becomes **−0.500**. No p-value or population confidence interval was used: source cameras may not be independent and threshold choice is retrospective.

**Scientific result:** The available public site records do **NOT provide a stable, reproducible direction** for the suggestion that stronger local co-recording leads to temporal segregation. A competition-mediated interpretation would require simultaneous interspecific use data and controlled measurement, not merely high or low overlap of records pooled across 83 days.

## Why this helps the next field study

The previous ODSP focus was clock vs astronomical transformation. The source-verified ecological question is more consequential: **Does apparent time-partitioning persist at sites where both target species are available and cameras genuinely operated in comparable clock/solar windows, rather than being driven by camera station representation?**

For a future genuine study, (i) retain the original station roster and all species zeros, (ii) independently verify station/date/hours operational exposure before selecting the sample, (iii) align clock/solar labels and temperature/human covariates by **actual event date**, (iv) account for repeated animals and optical detection q, and (v) model a physical-site conditional species×clock/solar interaction. In ODSP's frozen Uljin 2022 design, also retain the predeclared 41 daylength date pairs; neither this Bukhansan 2019 record study nor these aggregate 3-bin analyses evaluate them.

## Reproducibility

- Post-outcome scope `BUKHANSAN_PUBLIC_JOINT_SPACE_CLOCK_OVERLAP_V3_CONTRACT.json`.
- Source-checked original-camera derived 3-window data `BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json`.
- Pure standard-library implementation `scripts/run_bukhansan_published_joint_space_clock_overlap_v3.py`.
- Regression tests `tests/test_bukhansan_published_joint_space_clock_overlap_v3.py` check all 11 source camera marginals, joint versus marginal overlap, both exact refinement orders, order-balanced sums, site contributions, source sparsity rank flips and immutable source-HOLD.
- [Dedicated GitHub Actions 38637956483](https://github.com/zuizui0223/odsp/actions/runs/38637956483) validates the source-anchored calculations.
- Full source read as PDF pages 4–5, author publication linked above; never substitute previous publications' entirely different temporal KDE quantities for these discrete record distributions.
- Original NIE EcoBank v1.1 2022 date/hour source remains unavailable in issue https://github.com/zuizui0223/odsp/issues/265. PR #264 remains **Draft**, no frozen source or earlier scientific claim reclassified.

**Evidence tier:** post-publication **genuine observed pooled station×coarse-clock source distribution** and two exact noncausal algebraic decompositions; no individual-animal or interspecific-competition inference.
