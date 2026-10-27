# Independent BOP-like raptor tracking source: Dryad Schaub et al. 2026 metadata screening

**Role:** external source discovery only, after closing the original BOP_RODENT v3-v2026 reference gate. No source selection for a confirmatory biological analysis, no outcome inspection, and no alteration of the frozen BOP terminal or the separate synthetic methods results.

## Public candidate

- Dataset: Schaub et al. (2026), *Evaluating the sensitivity of raptors to wind turbine collisions: an integrative approach based on GPS tracking* (Dryad), published **17 August 2026**.
- DOI: https://doi.org/10.5061/dryad.n8pk0p398
- Public landing page: https://datadryad.org/dataset/doi:10.5061/dryad.n8pk0p398
- The landing-page README states **280 original GPS-tagged individuals, six species, 15 field-study areas** in France, Belgium, Luxembourg, Netherlands, Germany and Sweden, 2009–2023.
- Species totals from its published README: *Circus pygargus* 101, *C. cyaneus* 54, *C. aeruginosus* 31, *Buteo buteo* 31, *Milvus milvus* 61 and *Circaetus gallicus* 2. **217** is the sum for the four BOP primary admitted taxa in this *whole published dataset*. It is not the eligible or independent external-validation sample size.
- **Data_1a.csv:** 3,302,242 GPS positions, 271 tagged individuals total, subsampled to a minimum 15-minute interval; raw `height.above.msl`, UTC `timestamp`, rounded 0.1° latitude/longitude, individual.global.identifier, individual.taxon.canonical.name, site `bb_name_2`, and quality/cadence fields. Full file about 888 MB (not opened).
- **Data_2a.csv:** 7,013,897 processed **in-flight** GPS positions, 162 individuals total, 2–3 second tracking intervals; height above MSL is **corrected** and above-ground level also supplied, but flight-only selection changes the ecological target. Full file about 2.16 GB (not opened).
- Supplementary source files: README.md (~8 KB), Study_areas_bounding_boxes.csv (~564 bytes), Complete_succesful_breeding_seasons.csv (~6 KB). They are metadata candidates, not validated animal-identity rosters.
- Public README lists **no external-temperature predictor** for Data_1a or Data_2a. The historical BOP random forest used external temperature and full-resolution latitude/longitude, so no claim that its **same frozen feature contract** can be directly scored here.

## Outcome-blind screening questions before admission

1. Verify legal reuse, canonical file version/checksums and a truly accessible metadata source. Small Dryad file downloads attempted in this turn returned HTTP 403 and were not read; their contents and identity coverage are **unverified**, not silently imputed.
2. Check exact individual IDs and study-area/source identifiers against the historical BOP sample to exclude tagged-animal reuse, relocated tag identity and research-program overlap. The same authors and Belgian sites make overlap plausible, but unverified.
3. Freeze biological independence unit: one individual, with study area/source clustered at higher level. No 280-animal iid inference. Study area must not be conflated with population, and the 15 areas are not necessarily mutually independent.
4. Choose the biological target *before* GPS opening. Data_1a raw AMSL altitude is more comparable to BOP's four raw AMSL bins, but 0.1° location rounding, 15-minute subsampling, missing temperature and protocol-specific processing mean the original RF is **not** a drop-in. Data_2a has corrected MSL and in-flight-only selection and must not be pooled indiscriminately with Data_1a.
5. If a *new* reduced common-feature learner is chosen, freeze its training-source contract, altitude semantics, scoring comparator, model-generator bytes, deterministic source-to-forecast execution, calibration/validation group roster and exclusion rules **before opening Dryad GPS outcomes**. Never relabel the historic BOP mixed score as its prospective result.

## Evidence and decision

**Status: EXTERNAL_METADATA_CANDIDATE_NOT_ADMITTED.** The landing-page metadata support a plausible larger multi-species source, but independence, predictor compatibility, source availability, real per-species support, altitude semantics and ability to freeze a directly comparable model remain unresolved. No external-Dryad statistical result or held-out 90% guarantee is asserted.

The separately closed BOP 2026 version-reference route remains **NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT**, with **10** new IDs spread across species (largest six *C. aeruginosus*) and unchanged original `empirical_state_prediction_mixed` status.
