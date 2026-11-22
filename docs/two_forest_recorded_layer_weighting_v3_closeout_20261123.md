# Two independently published forest bat acoustic datasets: reference-weighting dependence of recorded vertical information

**Date:** 2026-11-23 JST. **Status:** source-authenticated, post-publication/post-original-outcome **descriptive** comparison. **Not** latent high-dimensional SDM, calibrated detector q, site-heldout predictive replication, or preregistered biological hypothesis test.

## Summary

A 2-D recording/microphone-stratum projection can hide differences among **recorded acoustic labels**, especially when source counts are extremely dominated by one class. But the magnitude of observed-layer information depends strongly on whether the target is a *random recorded bat acoustic sequence* or a *random acoustically active label*. These are distinct reference measures/target populations, and neither is a direct sample of true bat organisms' flight-height niches.

Both original sources were freshly fetched and source hashes/reconciliation checked in one successful CI: **[GitHub Actions run #45079028499](https://github.com/zuizui0223/odsp/actions/runs/45079028499)**, artifact **14776406636** (`two-forest-weighting-source-verified-v3`), exact method tests **6/6 passed**, original source retrieval and receipt archiving succeeded. An earlier workflow run #45078795343 failed **before opening the source** because NumPy was absent in the workflow environment; existing package dependencies were installed in the repaired workflow without changing the scientific calculations.

The declaration of source-dependent estimands preceded this run and is in `docs/two_forest_weighting_dependency_v3_postoutcome.md`. The two source ecological count tables had already been examined in previous stages; this is **not independent confirmatory opening**.

## Source, count, identity checks

- Switzerland, Froidevaux et al. (2014), DOI [10.1002/ece3.1296](https://doi.org/10.1002/ece3.1296), original official NCBI PMC OAI-PMH JATS XML of PMCID `PMC4278821`. Official response SHA256 `6da2280f01723b426795ba174fbf3b0050f9fb1cfcbd0e7538b05744750b8ffb` in independent prior [OAI admission run #45078501629](https://github.com/zuizui0223/odsp/actions/runs/45078501629), artifact **14776441408**. Original Table 1 strict: 16 published labels (15 with ground or canopy detections, one forest-gap-only), **52,547 gap**, **41,850 ground**, **35,630 canopy**; total all three 130,027, of which ground+canopy = **77,480**. The article says 32 plots across eight spatial cells/71 nights, but *Table 1 itself is pooled* without site/day rows, therefore no site/night validation of this table is possible. The previous Europe PMC fulltext XML endpoint returned HTTP500 and its v1 run #45078238459 remains an honest source STOP; the separately documented official PMC source v2 succeeded.
- French Guiana, Gomes et al. (2020), DOI [10.5281/zenodo.4019867](https://doi.org/10.5281/zenodo.4019867), original `Bats.csv` MD5 `2bc125dd0021d23c0efa0cb80828c632`, SHA256 `4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9`; original `Number` count response, **7,854 source-design rows** and 16,123 counted acoustic passes, 21 original Bat labels. Original author rule total `Number>5` admits **17 labels** with **16,115 counted acoustic passes**. Source `COLOR` is two nearby ~180m-apart towers, not independent forest sites. The v4 previously scored conditional `I(Bat;recorded layer|HOUR)=0.1761303797` nats and v6 both local-tower transfers positive; those original results are **not changed**.

## Exactly comparable *unconditional, observation-conditioned* metrics

`p_w(s,z)=w_s p_recorded(z|s)`; `I_w(S;Z)=Σ_s w_s KL[p_recorded(z|s)|| Σ_r w_r p_recorded(z|r)]`; layer entropy `H_w(Z)`. All finite count zeros preserve their zero contributions and **no smoothing** is added to the primary I. A label with 0 recorded passes in both considered layers is **inactive** and excluded from the label-equal reference measure, not interpreted as an organism absent from the habitat.

- **Mass-weighted:** `w_s=source recorded count_s / N`, the information carried about the recording layer by the label of a random detected source acoustic sequence.
- **Equal-label:** `w_s=1/K_active`, information after giving each *acoustically active* label equal weight, retaining its own source-recorded layer split. This is an alternative hypothetical comparison population and **not a true species-level population correction**.

| Source + chosen target | Active acoustic labels | Original recorded two-layer counts | I(label;recorded layer), nats | H(layer), nats | I/H(layer) |
|---|---:|---:|---:|---:|---:|
| Swiss full source, **mass** | 15 | 77,480 | **0.00521627134** | 0.6899213691 | **0.7561%** |
| Swiss full source, **equal label** | 15 | 77,480 | **0.14601330070** | 0.6720373516 | **21.7270%** |
| Swiss equal label **at least 20 original counts** | 12 | 77,459 | **0.05407116631** | 0.6555169244 | **8.2486%** |
| Swiss **remove original-author noted hyperdominant P. pipistrellus**, mass | 14 | 5,251 | **0.04704778267** | 0.6432410858 | **7.3142%** |
| Swiss same dominance exclusion, **equal label** | 14 | 5,251 | **0.15565624954** | 0.6698863151 | **23.2362%** |
| Gomes original-author qualified, **mass** | 17 | 16,115 | **0.16659266547** | 0.5582250104 | **29.8433%** |
| Gomes original-author qualified, **equal label** | 17 | 16,115 | **0.30669264512** | 0.6553206732 | **46.8004%** |
| Gomes **equal label, >=20 original counts** | 17 | 16,115 | **0.30669264512** | 0.6553206732 | **46.8004%** |

The source-reported *P. pipistrellus* accounts for **72,229 of 77,480 Swiss ground+canopy recordings = 93.23%**. The observed count-weighted effective number of acoustic labels is `exp(H(S))=1.4469193` in Swiss source vs `6.8181138` for Gomes (both **acoustic recording** label frequencies, not biological species diversity). Dominance can suppress detected mass-weighted MI because `I(S;Z) <= H(S)`, but it does not alone imply the actual MI value or identify detector process. The equal-label estimates are sensitive to scarce labels: Swiss `I_equal` falls from 0.1460 to 0.0541 nats on the **same prereclared >=20 recorded count** guard, which changes target label roster; this is crucial and must remain visible.

This is the first **two original source** demonstration within this project that *the reference measure* materially changes the descriptive answer to how much recorded stratum information is discarded. This is **not new in general information theory**: reweighting changes joint distributions by definition. The empirical observation should be framed as evidence for a study-design decision, not as an invented ecological law.

### Core inference ceiling

- Swiss unconditional `I(label;recorded layer)` and Gomes *earlier* hour-conditional I are incomparable; this v3 explicitly recomputed **unconditional Gomes** I for the first like-for-like metric definition.
- Same metric definition **does not** make hardware, acoustic labels, ecology, field effort, false-positive calling, source season, species frequencies or sensor q comparable. Both sources are *observed detector classes*, not bat GPS/AGL z or detection-corrected `I(true species;flight height|x,y)`.
- Aggregate Swiss Table 1 lacks species×plot×night original records. No independent forest holdout is possible from this table; two sampled regions **do not** prove a universal transferable strategy.
- If microphone detection favors different spectral guilds or differs by stratum, it may create positive observed I absent any true species-specific flight height partition. q is **unmeasured in both sources**.
- One acoustic sequence is not one bat individual. Rare observed-group proportions have sampling uncertainty; a descriptive >=20 guard is not a confidence bound. No causation, competition, functional-guild mechanism or cross-biome effect-size test is claimed.
- The Yoh et al. Amazon source with independent forest locations remains **blocked at authenticated public Dryad API 401**; no source counts opened, no source substitution.

## Concrete next-source criterion

To advance from **recorded microhabitat** to ecological 3D species SDM, admit a new original site×species×vertical-stratum×time response table containing identifiable *independent stations*, effort/recording durations and source-specific q anchors (or linked repeated histories with justified independence), plus source-proven coordinate/height datum, and freeze an independent-site heldout predictive comparison. Otherwise target explicitly the observed sensor-stratum response and stop at descriptive generality.

**Research state:** two independent source-level descriptive comparisons reproduced; site-level transport and detection-corrected true niche **not yet established**. Draft PR #306 stays unmerged, ODSP N2 release, batter JAE and esdm E5 unchanged.
