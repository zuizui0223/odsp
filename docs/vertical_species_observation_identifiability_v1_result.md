# Result closeout: observation-aware species × height nonidentification v1

**Date:** 2026-11-22 JST. **Result type:** exact synthetic known-truth counterexample, not field-data inference. Do not merge into frozen N2 manuscript or use as evidence that any real bat community partitions height.

## Execution

- Prospective branch `prospective/vertical-species-identifiability-20261122`; default branch `main` unchanged.
- Frozen theory and witness: [vertical_species_observation_identifiability_v1.md](vertical_species_observation_identifiability_v1.md).
- Reusable implementation: `odsp/vertical_species_identification.py`, calls pre-existing `odsp.transferability.base_added_mutual_information` and `odsp.projection_loss.schoener_overlap` rather than creating competing metrics.
- Six synthetic assertions: `tests/test_vertical_species_identification.py`; **6/6 PASS**.
- [Successful GitHub Actions original run #45028662248](https://github.com/zuizui0223/odsp/actions/runs/45028662248); artifact `odsp-vertical-species-identifiability-source-free`, ID **14756708083**. The result JSON is `results/vertical_species_identifiability_sourcefree_v1.json` inside the archived CI artifact. The full synthetic tensors are in source code and artifact; there are no animal identifiers or observation uploads.

## Verified exact findings

Both latent worlds have horizontal species totals `[100,100]`. Each world has the same independent method-specific Poisson expected table M1 `[[9,1],[1,9]]`, M2 `[[4.5,.5],[.5,4.5]]`. Their detected aggregate count likelihoods coincide exactly under the **unlinked, independent method-process** assumptions, even though both species use different actual strata in World A but the same ones in World B.

| Calculation | World A | World B |
|---|---:|---:|
| True latent `I(Species;Height|Site)`, nats | **0.3680642071684971** | **0.0** |
| Naïve M1-detected `I` (identical in both worlds), nats | 0.3680642071684971 | 0.3680642071684971 |
| Horizontal Schoener overlap, after marginalizing height | 1.0 | 1.0 |
| True vertical-aware Schoener overlap | 0.2 | 1.0 |
| Projection overlap inflation | 0.8 | 0.0 |

With the true method-specific detector probabilities `q` supplied by an external calibration, `observed_mean/q` recovers each original latent world exactly (test passed). Without them or other identifying assumptions/linked histories, observed species×height data cannot choose between the worlds.

**Important:** This witness does **not** prove impossibility for every integrated likelihood. Source-linked multiple-visit co-detection, known detection response, randomized calibration or genuinely shared constrained detector models can provide additional identifying information, subject to source-specific assumptions. It proves only the broad claim “unlinked observations of each dimension across arbitrary methods suffice” is invalid.

## Empirical source decision

The original ODSP temporal Serengeti endpoint does report detected `I(Species;Time|Site)=0.22427598739601606` nats and positive held-out site scores in all three folds, but is explicitly camera-detected and cannot be relabeled as latent detection-corrected daily activity. ODSP `Tadarida` height-thickness endpoint was independently non-generalizing. `batter` supports repeated individual vertical profiles but its four taxa do not jointly sample a common multi-species vertical community.

Closest independent field two-height evidence (not sufficient for latent community MI) is Cistrone's 20 forest plots × ground/canopy × two nominal nights, 17 acoustic groups and 1,301 recorded passes. However, detector height/volume/range, recorder-hours and exact calendar dates are not calibrated, and some acoustic group identities are not independent species. `batter/prospective/resource_behavior_sdm/CISTRONE_RECORDED_STRATUM_RESOURCE_RESULT_20261121.md` explicitly calls the current endpoint recorded-pass allocation, **not true species×height**. Krauel's 2018 one-site three-microphone source records one taxon, so cannot identify a same-site `I(Species;Height|X)` even with known detection.

The `esdm` E5 programme remains **0/17 standard-qualified sources** for independent activity/detection separation. That is not proof no future multi-sensor source is suitable; it is a specific present source-admission failure.

**Current decision:** The theoretical case for a higher-dimensional state distribution is valid, but the *multi-species ecological height-niche information* is **not empirically identified with the current candidate source portfolio**. The honest current output is a detection-conditioned diagnostic and a new-source inclusion rule, **not** a validated multi-species higher-dimensional SDM.

## Scientific continuation boundary

For a prospective empirical multi-species vertical source, require same-site/same-time species-resolved counts or classifications, vertical detector effort and range/volume, independent detection calibration or valid linked repeated survey assumptions, explicit geographic and vertical reference measures, independent locations/years for held-out log scoring and a fixed design prior to the outcome opening. If only multi-height acoustic detections are available with unknown q, label the estimand `I(Species;detected stratum|Site,observed)` and test predictive transfer **for detected events only**, not ecological niche partition or species occupancy.

Do not reopen the frozen Cistrone resource comparison or the frozen N2 results to hunt a positive field effect. This prospective method gate is complete.
