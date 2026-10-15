# Bukhansan: exact camera-conditional null for apparent temporal partitioning

**15 October 2026 | ODSP PR #264 | Post-publication exploratory reanalysis, NOT a preregistered biological test**

## Ecological question

Do Water Deer and Wild Boar from the same published Bukhansan camera-trap network show an extra species-related clock-time partition **within physical camera sites**, beyond the apparent differences expected when finite source records are divided into more cells?

**Actual external empirical source:** Jeong, Shin & Kim (2025), Journal of Agriculture & Life Science 59(5):111–118, DOI https://doi.org/10.14397/jals.2025.59.5.111. Its original author-uploaded full-text Tables 1–2 report 11 public camera IDs × 24 clock-hour rows for the two species. The existing source-derived 3-bin contract passes independent row and habitat margin checks and contains **184 Water Deer and 273 Wild Boar photographic records** across 9 forest and 2 wetland cameras. No original animal photos, protected GPS, camera-by-hour operational logs, species detection q, individual animal IDs or event timestamps were recovered.

Clock windows 01–06, 07–18, and 19–24 are **published clock-row bins**, not actual dated solar phases; their widths are 6/12/6 reported hour rows. The original paper separately classified its published broad day/night totals using daily sunrise/sunset. No original Uljin 2022 41 matched daylength pairs were analyzed.

## Exact null: all published physical-camera and combined time-bin margins fixed

For each camera s and clock bin z, the observed Water Deer and Wild Boar source counts are W(s,z), B(s,z). The conditional null retains (a) **each camera's total Water Deer records**, (b) **each camera's total Wild Boar records**, and (c) **each camera×bin combined-species records** T(s,z) = W(s,z)+B(s,z).

If species labels are **conditionally exchangeable across the camera's recorded clock-bin observations**, a feasible Water Deer vector w(s,1:3) has exact combinatorial probability:

    P(w | fixed margins) = product_z choose(T(s,z),w(s,z)) / choose(sum_z T(s,z), W(s))

All feasible local configurations are enumerated; distinct 2×3 tables are NOT given equal probability. Site-local score distributions are convolved by integer dynamic programming; no Monte Carlo, random seeds, asymptotics or pseudocounts.

The overlap of species-normalized observed count vectors is O(P,Q) = sum_cells min(Pcell,Qcell). The previous observed marginal overlap O_site is fixed by the site-wise species totals, and the full joint overlap O_joint depends on assigning species counts among the three bins. The additional clock-resolved mismatch is **D = O_site − O_joint** (larger D suggests more mismatch).

The exact integer score is S = sum_(site,z) min(273 × W(s,z), 184 × B(s,z)). Then O_joint = S / (184×273) = S/50,232; source-observed **S=30,916**. The source exact-null support has **9,922 distinct global integer scores**; all local and global integer weights sum exactly to their combinatorial denominators.

The one-sided **record-label reference** is P_null(D >= D_observed) = P_null(S <= 30,916). This is NOT a valid animal-level or independent-camera biological p-value unless the substantially stronger species-label exchangeability and independence assumptions held. The field cameras and animals have not been independently shown exchangeable, and the original hour-specific detector q and effort cannot be verified.

## Source-backed result: extra temporal mismatch is ordinary under this exact null

| Quantity | Value |
|---|---:|
| Published source site-only overlap | **0.652114190** |
| Published source joint site × clock overlap | **0.615464246** |
| **Observed extra clock mismatch D** | **0.036649944** |
| **Exact null expected extra clock mismatch** | **0.041139977** |
| D observed minus exact null mean | **−0.004490032** |
| Exact reference null median D | 0.039357382 |
| Exact reference null central 95% discrete-quantile interval | **0.011825131–0.079411530** |
| **Exact one-sided conditional photographed-record tail** | **0.569788726301** |

The observed extra mismatch is **smaller than** the exact conditional null mean. Over 56% of label-exchangeable allocations have extra mismatch **at least as large** as the observed source table. Therefore the prior 0.03665 extra spatially conditioned temporal variation is a legitimate **descriptive measurement under finer bins**, but it is **not evidence by itself of within-camera temporal partition beyond finite-count allocations**.

This does NOT demonstrate ecological equivalence or behavioral absence of partition: the conditional null is a stylized reference and no independent animal- or camera-clustered sampling model is identified.

### The visually most important camera G19 was selected after the data

The earlier v3 descriptive decomposition attributed **87.72% of measured extra clock overlap loss** to forest camera G19. Applying the exact single-camera conditional label null gives:

| G19 component | Value |
|---|---:|
| Observed contribution to extra overlap loss | **0.032150820** |
| Expected under exact local null | **0.016291547** |
| Exploratory unadjusted one-camera reference tail | **0.125372371** |

G19 has larger measured discrepancy than its local null expectation, but is far from a convincing source-level rejection; the camera was **selected because it appeared extreme**, multiple cameras could have been selected, and photographed-record exchangeability is unverified. Other cameras have null-expected discrepancies larger than the observed one, explaining why the full network appears completely ordinary under the exact null.

## Consequences for ecological interpretation

The prior genuine author-source result remains: **Water Deer detections are concentrated at fewer camera codes than Wild Boar** (7/11 vs 11/11 positive cameras, inverse-Herfindahl detected-record effective cameras 3.034 vs 7.439). The cross-species overlap of camera record shares is 0.6521, compared with pooled coarse clock-bin overlap 0.9144 and joint site×clock overlap 0.6155.

But it is not justified to call the joint mismatch *competitive temporal niche segregation* or to interpret its 90.47% spatial-first accounting as a causal mechanism. Spatial-first and clock-first decompositions yield different attribution shares. Finite species-specific camera count allocations alone explain the small clock-conditioning increment adequately under the explicit exact record-allocation reference.

A different earlier post-outcome analysis showed a source-count 01–06 versus 19–24 Mantel–Haenszel OR 1.616 with a naive independence p≈0.0466 that was sensitive to M2; that is a **directional two-clock statistic** with unverified photographic independence. The new full three-clock **nondirectional overlap-refinement** exact-null tail≈0.570 concerns a different estimand and stronger conditioning constraints. These findings are not contradictory; picking the smallest p-value would be indefensible.

**Current manuscript-worthy ecological finding:** in the actual published Bukhansan source camera network, recorded spatial localization differs between species; the apparent extra within-camera temporal distribution difference is **not unusual after exact finite-count conditional comparison**. More sensitive data and independent replicated sites are needed to establish species-specific temporal segregation.

The original Uljin 2022 **41 fixed matched daylength date pairs** and true independently verified camera ON hours remain source-HOLD under https://github.com/zuizui0223/odsp/issues/265. This new route is an exploratory **2019 Bukhansan secondary analysis**, not a substitute for the Uljin source, an inferred fitness effect, human disturbance avoidance or competition experiment.

## Reproducibility

- Original paper DOI and author-published tables: https://doi.org/10.14397/jals.2025.59.5.111.
- Post-publication exact null contract: BUKHANSAN_PUBLISHED_SITE_CONDITIONAL_CLOCK_NULL_V4_CONTRACT.json.
- Code: scripts/run_bukhansan_published_exact_site_clock_null_v4.py.
- Tests: tests/test_bukhansan_published_exact_site_clock_null_v4.py (6 tests).
- **Actual successful CI:** https://github.com/zuizui0223/odsp/actions/runs/38662204765, including exact small contingency tables, integer probability mass conservation, 11-site source margin preservation, expected null, global tail, G19 postselection guard and immutable biological-source-HOLD.
- Earlier v3 observed overlap and source margin audit: docs/bukhansan_recorded_joint_space_clock_overlap_ecology_v3_20261015.md.

**Evidence status:** exact mathematics for a **hypothetical photographed-record exchangeability null**, evaluated against real published camera-level counts. It is neither a valid animal-population p-value nor a demonstration of evolutionary, competitive, solar or human-driven ecological mechanism.
