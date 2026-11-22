# Multispecies vertical information: observed-source transfer and detection boundary (2026-11-22)

**Evidence levels:** (A) source-free **mathematical nonidentifiability** demonstrated in `vertical_species_observation_identifiability_v1_result.md`; (B) *real but detector-conditioned* acoustic activity information in Gomes et al. 2020 original Zenodo `Bats.csv`; (C) *not identified*: latent `I(true species; actual flight height|geographic place)`, detection-corrected high-dimensional SDM, species-level niche overlap corrected by 3D.

This scientific record is on the **unmerged prospective ODSP branch**. It does not alter ODSP N2 submission, esdm E5, batter JAE or the existing resource×height null experiments.

## Independent source selection and source-only support
- Yoh et al. (2022), PLOS ONE, Dryad DOI `10.5061/dryad.0vt4b8h2d` is a promising 2-stratum/12-species/164-point field source, but source-only API ZIP intake returned **HTTP401 before any original numeric bat-pass outcomes**. GitHub Actions **success** with scientific `source_access_or_structure_stop`: run [#45029223793](https://github.com/zuizui0223/odsp/actions/runs/45029223793), artifact 14757181439. No artificial positivity/negativity is attached to it. Alternate original file access would need explicit separate admission.
- Independent Gomes et al. (2020) French Guiana matched high/low acoustics, original v1 `Bats.csv` at Zenodo DOI **10.5281/zenodo.4019867**, published MD5 `2bc125dd0021d23c0efa0cb80828c632`, verified SHA256 `4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9`. Source-only run [#45029391725](https://github.com/zuizui0223/odsp/actions/runs/45029391725) and category-only run [#45029516185](https://github.com/zuizui0223/odsp/actions/runs/45029516185) established 7854 rows, 19 fields, 21 original Bat labels, 9 DAY, 13 HOUR, POS=above/below, **X unique per record (not a physical site ID)**. Released CSV lacks verified independent site IDs, although authors sampled four locations.

## Critical row-grain correction (must carry into any publication)

Initial v3 [run #45029823495](https://github.com/zuizui0223/odsp/actions/runs/45029823495) scored binary POS with **one row = one event** and got source-row `I(Bat;POS|HOUR)=0`, Γ_min 1. This was a **wrong biological response denominator**, consistent with the original source's balanced data-design grid; the tiny positive +0.0001617 nats/row with interval including zero is NOT evidence for or against bat vertical activity differentiation. Original numeric `Number` was not opened by that workflow, and v3 is preserved as an instructive failed estimand, not quietly overwritten.

We independently authenticated the author's published `Hourly_Models.R` (MD5 `376bfc130acad070aa7045f6c816cd09`) in [run #45029941740](https://github.com/zuizui0223/odsp/actions/runs/45029941740). Their original R explicitly `summarise(Total=sum(Number))` and `stan_glmer(Number ~ ... + HOUR*POS + (HOUR*POS|Bat) ..., family=neg_binomial_2)`. The implemented author-rule excludes Bat groups with total `Number<=5` even though an adjacent comment mentions 20; we followed **executed source code**, not its inconsistent comment.

The revised **v4 protocol was committed BEFORE numeric original Number opening**: `docs/gomes_zenodo_number_weighted_v4_preopen.md`. Actual v4 original-data run [#45030204114](https://github.com/zuizui0223/odsp/actions/runs/45030204114) succeeded after source-free tests, with aggregate artifact **14757765028**, `gomes-zenodo-author-corrected-number-v4`. Source-free test fixture contained no real counts and corrected a minor no-signal smoothing expectation before the original data-opening step; no model, bin, threshold or split was altered afterward.

## First real bat acoustic activity endpoint: observed 2-stratum prediction

Original source has **16,123 acoustic counts** across 7,854 structured records, including **6,670 rows with true zero response**, 1,184 positive-response rows. The original author's minimum `Total>5` rule excludes 4 rare labels and 8 counts, leaving **17 labels / 16,115 acoustic counts** (not 16,115 independent bat individuals).

Response is recorded detector `POS` for acoustic source counts `Number`, conditional on `Bat` acoustic class and HOUR; the final claim does **not** treat two detector heights as actual bat flight altitude or infer true occupancy.

| Fixed endpoint | Authenticated real result |
|---|---:|
| `I(Bat;POS|HOUR,recorded counts)` | **0.17613037973692044 nats** |
| B0 `p(POS|HOUR)`, leave-one-DAY-out equal-day log score | **−0.5064528777825684** nats/count |
| B1 `p(POS|Bat,HOUR)`, same score and heldout count denominator | **−0.3928470554801496** |
| **B1−B0, mean across 9 DAYs** | **+0.11360582230241885** nats/count |
| Whole-day gains positive | **8/9** |
| 9-day bootstrap 95% *descriptive*, 10,000 draws | **[−0.019734728394323713, +0.2527382276786989]** |
| Frozen transfer category | **`mixed_days`** |

Individual day gains in fixed fold order (nats/count):
`[+0.5338499112, +0.2024189776, +0.0132274676, +0.2646583238, +0.0871737233, +0.0692558398, +0.0366585321, +0.1011143322, −0.2859047068]`.

The positive equal-day point estimate shows that source acoustic-class identity **can add predictive information for recorded vertical detector class across unseen nights** beyond time-of-night alone. But the descriptive uncertainty includes zero, one whole day has a large negative gain, and groups/individuals and four author study sites cannot be independently held out from this released CSV. So **generality is not established**. This reproduces a *predictive side of previously published observed vertical stratification*; it is not a novel demonstration that vertical niche partition exists or a new causal mechanism. Acoustic calls are not individual organisms; species labels include sonotypes; detection and time-varying effort remain unresolved.

## Detector q sensitivity does NOT identify true use

Original observed-count plug-in `Γ_min` (Jeffreys 0.5, ratio of extreme per-class above/below acoustic odds) was **78.13449942247023**, both on the original-author retained group set and all 21 source codes. `Γ_min` is the minimum global ratio max(q)/min(q) at which a *free species×stratum observation process* can, for **expected count tables**, reconcile all labels with a common latent vertical odds; its strict positive-mean algebra is proven in `docs/vertical_species_observation_identifiability_v1.md`. For finite sampled counts this 78 value is **only a highly assumption-dependent plug-in diagnostic**, potentially dominated by extreme class odds, not an empirical detector efficiency measurement and not a proof that 3D niches differ. No independently observed q bounds or bat height calibration exist for this source.

Ecological inference remains bounded: `I(Bat acoustic label;recorded detector stratum|HOUR)`, not `I(true bat species;true flight Z|XY)`. A long list of same-study acoustic recordings cannot bypass species-dependent microphone range/volume, the lack of q calibration, unlinked detection histories, row-index X not being a site key, and missing independent geographic validation.

## Resulting next-source specification

A future real *3D latent SDM* admission needs **co-located species-resolved repeated vertical sampling with known effort and source-independent q calibration, or appropriately linked independent detection histories**; independent sites/years for holdout; a verified physical height reference; known observation kernel; and the same event support and proper scoring rule for baseline vs augmented model. If q cannot be identified, retain the observed-only estimand and do not rebrand it as a new 3D ecological law. The model may remain prospectively testable but **current portfolio does not certify true 3D spatial ecological niche distributions**.

Code paths: `odsp/vertical_species_identification.py` and `odsp/weighted_detected_vertical_transfer.py`; observed source adapter `scripts/gomes_zenodo_number_weighted_v4.py`. Both exact synthetic witness and original-real-data results are independently source-traceable, with no original observation matrix committed.
