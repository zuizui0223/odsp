# Sixty-two-study vertical biodiversity profile transfer — frozen V2 empirical closeout and independent V3 verification

**2026-11-23 JST. Status:** ORIGINAL SOURCE VERIFIED; preregistered score measured; **heterogeneous/mixed outcome**, not generalizing across all original studies. Neither a claim of species-specific 3D SDM success nor proof of zero ecological stratification. All methods and source-integrity gates are in unmerged new prospective branch, leaving ODSP N2 original manuscript, batter JAE, esdm E5, and draft PR #306/#307 unchanged.

## Question and design

**Does knowing the broad vertebrate group (Bats, Birds, Small mammals, Amphibians) predict the vertical shape of an author's standardized biodiversity proxy at a study held out in full better than a pooled vertebrate height slope?** This is broader than bat-only recording strata and genuinely holds out original published *studies*, not random height/source rows or same-study sites. The original 2023 Biological Reviews meta-analysis already discusses broad-taxon height gradients; new aspect is the **out-of-study predictive test of a deliberately simple taxon-conditioned versus pooled model**, not a novel recognition of height differentiation.

Original published research: Basham et al., *Vertical stratification patterns of tropical forest vertebrates: a meta-analysis*, DOI [10.1111/brv.12896](https://doi.org/10.1111/brv.12896). Public author GitHub [schefferslab/Vert-Strata-Meta](https://github.com/schefferslab/Vert-Strata-Meta), exact corrected/corrigendum commit **`a68a2fca81407800855ea482f94104b425911232`**, file `data/stripped_data/analysis/data_joined.csv`: Git blob SHA1 **`7b9c5b7e2b5722c7f4891853dc4fbc2e83db6b4c`**, original SHA256 **`028f5ad6371151a1cd5d89d2e2711711b4de383e24dd914a55e28b74aaa9cdc1`**, 920040 bytes. These source bytes were verified in both V2 and independent V3.

**Source-blind geometry/admission** `docs/vertebrate_vertical_study_source_v1_preopen.md` and `docs/vertebrate_vertical_study_source_v1_1_geometry_amendment.md`. V1 first-run scientific `source_architecture_gate_hold` [run #45083547587](https://github.com/zuizui0223/odsp/actions/runs/45083547587) was due solely to 1,171 blank *optional textual* `strata_category` values. All 1,422 rows contain valid [0,1] **numeric** canopy-normalized `mean_strata_height_p`; requiring textual labels was unnecessarily strict. The **pre-outcome** V1.1 parser amendment kept all original scientific height geometry and added duplicate-height diagnostics; source gate PASS in [run #45083799164](https://github.com/zuizui0223/odsp/actions/runs/45083799164), extended 7 synthetic tests finally PASS [#45083859540](https://github.com/zuizui0223/odsp/actions/runs/45083859540). No biological abundance/richness values opened by the source-only gates. Audited **62 original studies**, **86 original site identifiers**, **127 site×metric groups with >=2 distinct heights** (79 >=3); **14 source site×metric units repeat height, with 49 redundant rows**.

Before opening new V2 source biodiversity numerical outcomes, frozen source/cohort, numeric target handling, softmax slope grid and whole-study CV scoring in [V2 pre-outcome freeze](vertebrate_vertical_study_v2_preoutcome_scoring_freeze.md). `corrected_biodiversity_metric_value` is an **author-standardized abundance/richness proxy**, not an independently identified probability of organism presence or raw individual counts. Duplicate height records were **averaged** within site×metric×height (rounding to 8 decimals) prior to normalizing the author proxy **within site** across observed heights to unit mass; no unsampled height was falsely treated as an absence. All 127 profiles passed finite/nonnegative/positive response gates, **zero groups excluded by response**. Abundance 69 profiles; richness 58 profiles.

**B0** models a common slope `p(z_j|site sampled heights) proportional to exp(beta_0*height_j)`; **B1** uses the same training-only site-normalized height support but a broad taxon-specific slope shrunk to B0 with fixed 5-study strength, and exact B0 fallback for fewer than 4 training studies in a class. Fixed deterministic beta grid [-6,6] step 0.25. Fit uses equal original-study weights (within study, sites equal). Leave one original `study_id` out entirely for evaluation, separately by richness and abundance; B1/B0 compared on identical heldout heights and normalized author proxy. No site/year random row leakage, no source-driven subgroup or post-result penalty search. Proper scoring is **profile-weighted log score** in nats per within-site normalized author proxy, not GPS likelihood, individual animals, or directly measured true height use.

## First original-data outcome — neither endpoint generalizing

[First original V2 score CI #45084122700](https://github.com/zuizui0223/odsp/actions/runs/45084122700), artifact **14778054983**, `vertebrate-vertical-62study-heldout-v2`, includes original source audit, complete study folds and group-level summaries. Eight source-free known-truth tests passed **before** first full original biodiversity numerical opening.

| Endpoint/cohort | Original studies held out | Positive study folds | B1−B0 (equal-study nats / normalized profile) | Descriptive original-study 95% bootstrap |
|---|---:|---:|---:|---:|
| Abundance, all taxa | **54** | **32/54** | **+0.0190802412** | [−0.00385007,+0.04310444] |
| Richness, all taxa | **42** | **25/42** | **+0.0020023806** | [−0.00219696,+0.00594164] |
| **Bats**, abundance | **21** | **12/21** | **+0.0359188736** | [−0.01623993,+0.08915329] |
| **Bats**, richness | **12** | **7/12** | **+0.0016664430** | [−0.00452912,+0.00700636] |
| Birds, abundance | 14 | 9/14 | +0.0005488049 | [−0.02854340,+0.02326256] |
| Birds, richness | 18 | 12/18 | +0.0040826172 | [−0.00272514,+0.01067379] |
| Small mammals, abundance | 16 | 11/16 | +0.0167720882 | [−0.00751797,+0.03972844] |
| Small mammals, richness | 8 | 6/8 | −0.0011730552 | [−0.01353620,+0.00862570] |

Amphibians: abundance has 3 heldout studies and richness 4; in all relevant folds, train-only count is below the frozen 4-study taxon fit gate, hence **B1 exactly falls back to B0** and every gain is **0 by construction**, not an observed null ecological effect.

The frozen classification is **mixed** in all estimable individually fitted major taxon/endpoint cohorts, and **mixed** overall in both original endpoints. Point estimates slightly favor B1 but all descriptive study intervals include zero; positive overall does NOT establish a stable new-study vertical profile rule. A 0-containing percentile interval is not a formal equivalence test either. Taxa and methods differ and the fixed one-slope model may be too restrictive; do **not** select flexible/nonlinear/post-hoc interaction models on these opened outcomes to rescue a positive claim.

The original data are ecological meta-analysis **broad taxon averages / richness or abundance proxies**, not source species-level occurrence records, and the original independent study IDs may differ markedly in location, method, source population and q. Even an observed positive would not demonstrate an independently validated species-level 3D SDM `lambda(species,x,y,z,t)`. This result instead indicates the substantive **transferability bottleneck**: historical observations of taxon-specific vertical organization do not ensure that broad-taxon identity alone predicts height-profile shape when a new original study is unseen.

## Independent implementation — consistent with first receipt

A **separate original CSV reader and NumPy vectorized** profile/softmax fitting implementation, `scripts/verify_vertebrate_vertical_study_v3_independent.py`, **does not import** the first V2 model, source parser or score helpers. Independently re-downloads/checks original Git source, reconstructs all 127 height profiles with the 49 repeated rows mean-collapsed, implements study-equal beta fitting and all original study leave-one-out splits, and checks pooled and focal bat endpoint estimates.

[Original independent source-replay CI #45084285451](https://github.com/zuizui0223/odsp/actions/runs/45084285451), artifact **14778432662**, success. Independent vs registered first-run effects:
- all-taxa abundance: absolute discrepancy **4.8572×10⁻¹⁷**;
- all-taxa richness: **2.2985×10⁻¹⁷**;
- bats abundance: **2.0817×10⁻¹⁷**;
- bats richness: **2.5587×10⁻¹⁷**.
- study counts 54/42, source profile counts 69/58 and positive fold counts 32/25 matched, bats positive 12/21 and 7/12 matched.

This verifies original source intake, principal model arithmetic and group-level CV summaries, **not** a second independent field experiment, not every original fold-level score individually, not detector calibration nor ecological mechanism.

## Next scientific gate and explicit non-claims

What is supported: **broader-than-bat, 62-study heldout audit with mixed generalizability**, using one precisely controlled source-standardized vertical richness/abundance target and fixed model capacity. The positive slope improvements in some studies/taxa are genuine within-protocol scores but are insufficient to claim universal rule. The source already demonstrates biodiversity gradients; this newly evaluates one transport rule, not the general value of all conceivable 3D models.

What is not supported: observed or causal trophic partition, true species×height distribution; claim that taxonomic height preferences don't exist; a globally transferable 3D SDM; biophysical detection-corrected `q`; spatially explicit source maps; known individual movement/behavior; or identifiability of actual airborne animal height from broad source `strata`.

The next genuinely new study would require a **separate data source with source-native species×physical site×time×vertical position and calibrated observation process**, fixed fully before its raw outcomes. Do **not** excavate the same 62-study author table after seeing mixed results to search for a favorable nonlinear kernel, subset of taxa/continents or different beta range. This independent source programme is closed as **successful software and source verification with scientifically mixed original study transfer**.

All existing frozen SDMR/ODSP N2, batter JAE, esdm E5 and earlier other Draft PRs untouched.
