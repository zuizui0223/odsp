# Apparent habitat differentiation depends on one camera: nested ecological scale of Water Deer–Wild Boar observations

**15 October 2026 | ODSP PR #264 | post-publication source-verified ecology reanalysis (v6) | not a predeclared source study**

## Biological question

When two sympatric ungulates differ in the distribution of camera-trap detections, is that difference best described by **broad habitat class** (Forest vs Wetland), **micro-site within habitat** (physical camera code), or **diel observation window within site**? And is the apparent ecological scale repeatable when one source camera is omitted?

This is particularly salient because a prior source-backed result found that a single wetland camera, **M2**, accounts arithmetically for **98.09%** of the Water-deer–Wild-boar difference in the overall fraction of detections recorded at the two wetland cameras. A separate earlier exact *photograph-label* temporal null found no excess site-conditional time mismatch (reference tail **0.569788726301**); these are **observational** questions, not direct competition tests.

## Primary, genuinely published input

Jeong, Shin & Kim (2025), *Journal of Agriculture & Life Science* 59(5):111–118, DOI https://doi.org/10.14397/jals.2025.59.5.111. Source Tables 1–2 give 11 source camera codes × 24 clock-hour count rows, separately for Water Deer and Wild Boar, and Tables 3–4 give species × habitat day/night totals. Source-derived `BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json` preserves all **11** source camera codes, **9 Forest** and **2 Wetland**, retains 3 previously defined clock blocks (01–06, 07–18, 19–24), and **independently checks all author-published 24-hour species counts and four habitat totals**. Exactly **184** Water Deer and **273** Wild Boar author-recorded photographic events are accounted for.

No original dated images or detailed event stream, independently authenticated camera ON/OFF time, species-specific camera detection q, animal identities or precise GPS locations were acquired. Multiple detections may be correlated; 'camera' is an original source public code, **not an independent population study unit by fiat**. The source is Bukhansan in 2019, not NIE EcoBank Uljin original 2022 41 matched astronomical dates.

## Three nested scales of the SAME recorded-count distribution

For each species, normalize its camera × clock block counts to its own total `N_water=184`, `N_boar=273`. Define total variation `TV = 0.5 sum_cells abs(p_water(cell)-p_boar(cell)) = 1 - sum_cells min(p_water(cell),p_boar(cell))`. A larger TV means that **recorded count fractions** overlap less, not necessarily different movement behavior.

The nested supports are: **2 habitats** → **11 public camera IDs (each nested in habitat)** → **11×3 camera × clock blocks**.

| Scale and record-distribution TV component | TV | Share of final joint TV |
| --- | ---: | ---: |
| Forest vs Wetland, initial difference `TV_habitat` | **0.326763816** | **84.98%** |
| Additional between-camera differences WITHIN habitat, `TV_camera − TV_habitat` | **0.021121994** | **5.49%** |
| Additional three-clock-window differences WITHIN cameras, `TV_joint − TV_camera` | **0.036649944** | **9.53%** |
| **Total joint camera × 3-window recorded distribution mismatch** | **0.384535754** | **100%** |

The exact telescoping identity is `TV_joint = TV_habitat + (TV_camera − TV_habitat) + (TV_joint − TV_camera)`. Original direct record-overlap identities from prior v3 are also verified: `TV_camera = 1−0.652114190`, `TV_joint = 1−0.615464246`.

Within the originally observed full 11-camera sample, **93.93% of the source record-distribution spatial mismatch at the camera scale** is already visible when collapsing stations to the two forest/wetland categories: `0.326763816 / 0.347885810 = 0.939285`.

**Not biological causation, variance explained or a unique niche-contribution percentage.** These percentages depend on the **chosen nested order and number/width of source categories** (2 habitats, 11 stations, 3 unequal 6/12/6 clock groups). There is no sampling-variance partition here, and even a strong habitat-class RECORD mismatch could arise through unequal physical camera effort, lens q, local positioning, repeated photographs, site selection or real animal availability.

## Micro-site diagnostic: why only forest camera G19 adds spatial mismatch at full sample

The habitat-to-camera refinement can be computed directly by habitat as

```text
extra_within_habitat(h)
  = min(W_h/184, B_h/273)
    − Σ_{site in h} min(W_site/184, B_site/273).
```

This is nonnegative by finite-distribution marginalization. Its actual source components are:

| Habitat | Source counts W/B | Contribution to new TV after splitting habitat into cameras | Within-habitat site overlap normalized separately to W_h and B_h |
| --- | ---: | ---: | ---: |
| Forest (9 cameras) | 74 / 199 | **0.021121994** | 0.623455 |
| Wetland (M1, M2) | 110 / 74 | **0** | 0.825799 |

Within Forest, **G19 is the only source camera whose species-normalized network record share reverses the overall Forest direction**: `45/184 − 61/273 = +0.021121994`. The other eight Forest cameras have source species-normalized Water shares no greater than their Boar shares. **That single site produces the entire original habitat→camera extra TV.**

The zero added TV in Wetland **does not mean the two wetland sites are biologically interchangeable**. Their separately normalized within-wetland camera record distributions have overlap **only 0.825799**, while the source-wide Water fraction is greater than the Boar fraction at BOTH sites. The pointwise minimum (and margin normalization) makes the two Wetland site contributions add up to the same pooled wetland overlap. Do NOT mistake this metric-specific exact cancellation for absence of micro-site variation.

The earlier v5 analysis found the large original Forest/Wetland source-record fraction contrast was concentrated at **M2**, whereas the residual full-network **within-habitat refinement** here comes from **G19**. Those describe **different observational scales**; they are not competing causal diagnoses.

## Full 11-camera leave-one-out: which ecological scale is visible changes dramatically

Each of the 11 original source camera codes is deleted once. **Both species' totals are recalculated for the retained network**, and ALL three levels of TV are recomputed without keeping any old 184/273 denominator.

| Camera sample | TV Habitat | Extra within-habitat camera TV | Extra within-camera clock TV | Habitat share of CAMERA-scale TV |
| --- | ---: | ---: | ---: | ---: |
| **Original 11 cameras** | **0.326764** | **0.021122** | **0.036650** | **93.93%** |
| **M2 removed** | **0.084045** | **0.253882** | **0.017663** | **24.87%** |
| M1 removed | 0.356636 | 0.025117 | 0.034687 | 93.42% |
| **G19 removed** | 0.442310 | **0.000000** | 0.004004 | 100.00% |

**Key ecological interpretation:** The original broad Habitat category appears to account for essentially all *observed camera distribution mismatch*. But removing one wetland camera, M2, reduces that apparent habitat share to **24.87%**, while extra Forest/Wetland-internal site mismatch grows from **0.021122 to 0.253882**. This is not a new wildlife behavior; **source composition changed, and all species-normalized denominators changed**. The species' spatial camera-record fractions change meaningfully with the sampling roster.

Removing G19 instead makes the habitat→camera TV increment effectively **zero**: within the remaining network, all source camera differences align in direction with their habitat's pooled species record-share ordering. This is a property of the TV minimum, not an absence of forest microhabitat heterogeneity.

The program reports all eleven omitted-camera contrasts and checks the algebraic nested identities for each. Neither extreme is a valid independent site-leave-one-out **population confidence interval** or randomized habitat effect. The post-data choice to highlight M2 and G19 is explained transparently.

## Integrating the ecological result with the exact temporal null

Prior ODSP v4 showed that after keeping original camera species totals and each camera × clock-bin pooled totals fixed, the observed extra clock TV **0.036650** was **smaller** than the formal exact hypergeometric record-label null expectation **0.041140** (one-sided reference tail **0.569789**). This reinforces that finer temporal bins **alone** do not establish local competitive partitioning. This source-level formal label-null is **not an independent-animal p-value**.

Combining the studies, the strongest reportable ecological result is **scale-sensitive spatial detection heterogeneity, heavily influenced by one wetland camera**, without a confirmed repeated *within-camera* temporal segregation mechanism. More cameras at multiple independent wetland habitats, verified hours and detection, and animal-independent dated events are needed to determine whether the apparent spatial signature is environmental preference rather than sampling/placement.

This is a **post-publication reanalysis** of actual published photo counts and does NOT establish animal abundance, competition, habitat choice, density, thermal refuge, urban avoidance, evolutionary change or season-specific astronomical phase.

## Next decisive field test

To evaluate a biological hypothesis such as *“Does habitat or microhabitat predict local water-deer versus boar detection after equalization of exposure and q?”*, predefine station effort and independent species records, survey multiple wetland microhabitats rather than 1–2 cameras, and explicitly include site effects. If the interest remains astronomical phenology, capture original per-photo date/time and camera operation, then test within-site clock-versus-solar windows with seasonal replication. The original frozen ODSP Uljin 41 daylength date-pair design is a DIFFERENT source and still **HOLD** until authorized original NIE EcoBank v1.1 event and camera-hour operation bytes are authenticated.

## Reproducibility and source boundaries

- DOI: https://doi.org/10.14397/jals.2025.59.5.111, original published Tables 1–4.
- Original publication-derived exact-margin-checked source file: `BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json`.
- New post-outcome scope: `BUKHANSAN_NESTED_HABITAT_SITE_CLOCK_V6_CONTRACT.json`.
- Source-audited standard-library implementation: `scripts/run_bukhansan_published_nested_habitat_site_clock_v6.py`.
- Tests: `tests/test_bukhansan_published_nested_habitat_site_clock_v6.py` (6 source/identity/influential-site/negative-control tests).
- **Actual successful [dedicated CI 38674113573](https://github.com/zuizui0223/odsp/actions/runs/38674113573)**: all six tests and complete 11-camera leave-one-out output reproduced from author-published margins.
- Complementary sources: [v5 M2 localization](https://github.com/zuizui0223/odsp/blob/ecology/uljin-matched-daylength-temporal-refuge-v0/docs/bukhansan_wetland_M2_source_localized_ecology_20261015.md), [v4 exact finite-record camera time null](https://github.com/zuizui0223/odsp/blob/ecology/uljin-matched-daylength-temporal-refuge-v0/docs/bukhansan_exact_camera_conditional_time_null_ecology_20261015.md).
- Original 2022 EcoBank Uljin source held: https://github.com/zuizui0223/odsp/issues/265.

**Maximum justified claim:** true original published camera-photo count *distribution* differs on the habitat scale in the original sample but its allocation across habitat versus within-habitat station classes is **highly contingent on one wetland camera's inclusion**; additional time-bin variation is not supported beyond a separate formal finite-photo null. None of these constitute causal biological partitioning.
