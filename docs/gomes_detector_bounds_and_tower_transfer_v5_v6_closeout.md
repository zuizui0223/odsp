# Gomes original two-tower transfer and detector partial bounds: v5–v6 closeout (2026-11-22)

## Status — real source result, observational level only

Previous original data: authenticated Gomes et al. 2020 Zenodo v1 `Bats.csv`, DOI `10.5281/zenodo.4019867`, SHA256 `4a3b84e7175c29110bb6220f5cdf5889152897501b371fad3e2d9a74523773c9`, 7854 original design rows, 21 acoustic labels and **16,123 counted acoustic passes** in `Number`. The v4 day-heldout detected-stratum endpoint remained `mixed_days`: 8/9 positive, equal-day mean Δ+0.113606 nats/count, descriptive 95% day-bootstrap interval [−0.01973,+0.25274].

### Material original-source semantics correction

The prior claim that Gomes did not expose physical study-site identifiers was **incorrect**. The original paper [Gomes et al. 2020, PeerJ e10591](https://doi.org/10.7717/peerj.10591), methods and Table 2, verifies **two COPAS canopy towers 180 m apart**. It labels random intercepts `Tower=green` and `Tower=red`; source `COLOR` is `green/red`, and original published R model (MD5 `376bfc130acad070aa7045f6c816cd09`) includes `(1|COLOR)`. Thus COLOR represents two physical local towers, not a nuisance label with no location interpretation. Source `X` remains only a unique row index. This **overrides** any earlier statement in the v4 closeout/PR that no local-site holdout was possible; frozen v4 scores are not altered.

This is **not four independent forest sites**: the 4 recording *positions* are the two towers × above/below microphone layers. The original paper explicitly uses two tower infrastructure locations. Neither tower provides independent regional/geographic replication.

## V5 post-outcome detector q bound

Frozen documented **post-outcome** sensitivity protocol: `docs/gomes_detector_identified_set_v5_post_outcome_contract.md`. Mathematically exact conditional interval formula and conservative KL/Pinsker lower bound were implemented in `odsp/detector_partial_identification_v5.py`, with seven **source-free known-truth checks PASS**. Original authenticated result [Actions #45030929968](https://github.com/zuizui0223/odsp/actions/runs/45030929968), artifact **14757950947**, `gomes-detector-identified-set-v5`.

With the same 17 original-author eligible classes, 0.5 Jeffreys smoothing, and assumed class×height detection probability range `[1/Γ,1]`, each hypothetical bound means the following pair count *must* retain a distinct latent above fraction **if** plug-in counts may be treated as expected observed intensities:

| Assumed Γ, not measured | Distinct-profile label pairs among 136 | Analytical conservative I lower bound, nats |
|---:|---:|---:|
| 1 | 136 | 0.1151981272 |
| 2 | 103 | 0.0138987061 |
| 5 | 53 | 0.0010154515 |
| 10 | 31 | 0.0001464075 |
| 20 | 16 | 0.0000186218 |
| 50 | 8 | 0.0000003038 |
| 100 | 0 | 0 |

The point-value minimum Γ to make all detected class-height profiles compatible with a common latent profile is **78.13449942** under this simple expected-count observation model. Whole-day (nine DAYs, 5,000 resamples) bootstrap descriptive 2.5/median/97.5% Γ = **60.8008/203.5657/907.1948**, reflecting instability and rare/zero classes; *not* a confidence bound for real sensor calibration or the true latent species-height information. q was NOT measured in Gomes. Detection distance ranges from unrelated literature do **not** establish an upper bound Γ in this site/recording geometry. Strong generalizations from the conditional lower-bound curve are prohibited.

## V6 newly verified local tower holdout

New original-source semantic evidence above was independently checked **after** v4 observed count results, so v6 is an **explicitly post-original-response follow-up**. Tower-specific model/split was declared and committed **before looking at tower-specific source scores** in `docs/gomes_tower_transfer_v6_postoutcome_prescore_freeze.md`, using the same source and no new taxa, predictor, response or region.

Fixed proper-scoring comparison: B0 `P(recorded microphone position|HOUR)`; B1 `P(recorded position|HOUR,Bat acoustic label)`; Jeffreys alpha 0.5; B1 training-only Bat threshold >5 total count (author original). All original label counts in heldout physical tower are evaluated on **the same count cells**; no label-based target screening, no reusing target tower in the training model. Unknown/rare class×hour falls back to B0. Whole **tower** held out; each direction is one physical tower. Equal-tower score across two targets.

Source-free known-truth tests, including opposite-tower sign reversal and primary/secondary STOP independence, **6/6 PASS**. Original [Actions #45031349685](https://github.com/zuizui0223/odsp/actions/runs/45031349685) **SUCCESS**, artifact **14757379658**, `gomes-tower-transfer-v6`. First v6 run #45031239161 failed because one of 18 tower×DAY target cells was missing/zero and the code raised before storing the eligible primary scores. Correction *honored the originally frozen secondary STOP*, left the independent primary estimator unchanged, added a specific regression test and reran successfully. Neither negative nor positive tower scores were available in the first failed run.

| Original tower held out | Heldout acoustic counts | B0 log score | B1 log score | B1−B0 |
|---|---:|---:|---:|---:|
| **Green** (train Red) | 13,117 | −1.6766025460 | −1.3551956282 | **+0.3214069178** |
| **Red** (train Green) | 3,006 | −1.4064120022 | −1.1537558405 | **+0.2526561617** |
| **Equal-tower mean** | 16,123 source total, NOT independent animals | −1.5415072741 | −1.2544757344 | **+0.2870315397** |

The separate predeclared **tower+DAY** (18 tower×nine DAY combinations) endpoint is **STRUCTURAL STOP**: source contains positive acoustic counts in 17/18 target tower×DAY cells, and one missing/zero target. No partial-day subset scoring, no filled zeros, and no 17-fold rescue were allowed. The primary whole-tower result has positive counts and remains evaluable as predeclared.

### Exactly what this supports

**Supported**: the published bat acoustic-class label adds heldout predictive information about whether the *recorded acoustic passes* appear in the above- or below-canopy microphone at **both local towers** in the same forest, after conditioning on original source HOUR under this fixed, simple estimator. It transfers across two local stations ~180 m apart (one tower trained/one tested), and source class identity was important in 2/2 heldout directions.

**Not supported**: true co-occurring bat species' *biological* use of geographic 3D space, measured animal flight altitude, GPS z/AGL, detector-corrected latent `I(S;Z|X)`, site-independent reproduction across forests/biomes, a calibrated sensor-q ratio below Γ, risk/predation mechanism, or general SDM suitability prediction. The 2 towers are near each other, share the same weather and experiment, and the microphone observation process is species-/stratum-/tower-dependent and uncalibrated. Class labels include unresolved multispecies acoustic complexes; calls ≠ independent animals. A two-direction sign pattern has no defensible population-level p-value or broad universality. A large positive point estimate from two towers cannot override these constraints.

## Next independent evidence needed

A second *independent* forest/site network with co-located and repeated above/below acoustic surveys and source-specific detector calibration (or linked repeated histories) is needed to measure geographically transferable biological vertical partition. Alternatively, retain the narrower aim: prediction of the **recorded detector layer** and test transfer at >=3 independently held out forest sites with proper effort and class uncertainty. Do not refit previous outcomes or post-hoc choose an apparently favorable class subset.

All old ODSP N2/SDMR, batter JAE and esdm E5 results stay intact, main is untouched and PR remains Draft.

## Independent arithmetic replay (separate source parser and probability engine)

The original two-tower v6 results were **independently recomputed**, without importing the production v6 source adapter or ODSP scorer. The separate verification script `scripts/verify_gomes_tower_v6_independent.py` downloads and hash-verifies the same original author's CSV, uses `csv.DictReader` and its own raw `Number` integer parsing, constructs training-only hour/class cell counts and computes target log probabilities directly. It checks eight original numbers (per tower N, B0, B1, Δ) against the archived first successful v6 receipt to absolute tolerance 1e−10.

[GitHub Actions run #45031566764](https://github.com/zuizui0223/odsp/actions/runs/45031566764), artifact **14757434846** `gomes-v6-independent-source-replay`, completed successfully: **8/8 exact checks passed; max absolute discrepancy = 0.0**. The original v6 synthetic 6 tests and this independent replay validate scoring implementation, *not* organism-height or calibrated q.

## Published-data source priority for a future independent site test

- **Yoh et al. (2022) Amazon BDFFP**, Dryad DOI `10.5061/dryad.0vt4b8h2d`: two forest areas, four transects, 164 sampling locations, simultaneous canopy/understory recorders and source-declared species/sonotypes. Best declared future design for independent **forest-site** holdout but original 2024 Dryad ZIP access returned HTTP401 in an outcome-blind CI. Do not claim this source is admitted, assume unseen zeros, or silently substitute the older source version.
- **Froidevaux et al. (2014) Switzerland**, DOI `10.1002/ece3.1296`: 32 forest plots in eight 1-km² sampling cells, 16 bat species, paired ground/canopy/felt-gap observations and repeated nights; authors report 145,433 call sequences. This is a **published design** only at present, not a verified available species×site×height raw-event table. Need exact source-release and row-grain admission before an independent fit.
- **Gomes 2020** verified two-tower source: 2 physical stations only, both local positive heldout results. Retain as source-local observed detector-class prototype, not global generalization or true flight-z niche.
- Independent paired acoustic or device sensitivity calibration from other hardware/habitats is **not** a transferable source-specific bound `q_{s,tower,stratum}` without frequency/beam/vegetation/recorder conditioning. The article's generic 8–30 m detection ranges alone do not calibrate the needed q.
