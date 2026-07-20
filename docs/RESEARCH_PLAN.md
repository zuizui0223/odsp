# ODSP research plan

## Research question

When undiscovered populations may occur near but outside known occurrence patches, does explicit near-disconnected patch construction recover held-out or future occurrence clusters that occurrence-extension searches miss?

## Estimand

The primary estimand is incremental cluster recovery:

```text
recall(extension + near-disconnected) - recall(extension only)
```

This is evaluated at predeclared spatial radii and under the same eligible region and candidate-support layer.

## Development case

The first *Campanula microdonta* island analysis is a problem-revealing and method-development case. Historical records through 2025 form the occurrence reference; 2026 field detections provide preliminary external illustration.

The method was defined after the first ACSP field result was inspected. Consequently, this dataset cannot serve as untouched confirmation of ODSP.

## Confirmatory design

1. Freeze support construction, feature set, thresholds, graph distances, patch persistence rule, and recovery radii.
2. Sample independent taxon-region pairs not used in method development.
3. Cluster occurrences geographically before splitting.
4. Hold out complete occurrence clusters.
5. Build support and candidate patches using training data only.
6. Compare extension-only with extension plus near-disconnected patches.
7. Retain failures and empty candidate sets in the intention-to-evaluate denominator.
8. Reserve at least one future field season for prospective confirmation.

## Frozen independent cohort

`validation/frozen_taxon_region_manifest.csv` contains 48 predeclared taxon-region pairs copied from the two independent ACSP confirmation cohorts:

- 24 mixed plant/animal pairs frozen on 2026-07-05;
- 24 non-overlapping plant pairs frozen on 2026-07-06.

These pairs are reused as an independent sampling frame, not as evidence that ODSP already works. ODSP requires a new graph-patch endpoint and therefore must reconstruct fold inputs under its own frozen protocol.

`odsp.acsp_adapter` converts complete ACSP fold exports into ODSP benchmark inputs. It explicitly blocks legacy exports that lack training and held-out coordinates. Coverage IDs, candidate IDs, or post hoc coordinate reconstruction are not accepted as substitutes.

## Current data blocker

The historical ACSP exports were optimized for Top-k recovery and may contain held-out coverage IDs without explicit training/held-out coordinate tables. Therefore the next executable data task is to rerun or extend the ACSP fold exporter so every fold writes:

- `training_occurrences.csv` with stable source IDs and coordinates;
- `held_out_occurrences.csv` with complete cluster membership and coordinates;
- `candidate_support.csv` generated from training occurrences only;
- a manifest containing source commit, GBIF query date, species key, region bounds, random seed, fold assignment, and support configuration.

Until those files exist, affected units remain `blocked_incomplete_legacy_export` rather than being silently omitted.

## Required baselines

- fixed-radius buffers around known occurrences;
- nearest-known outward search;
- DBSCAN or an equivalent simple geographical clustering method;
- single support threshold;
- persistence across thresholds;
- support-only patch ordering;
- same-pool random patch selection.

## Secondary endpoints

- total held-out cluster recall;
- distance to nearest candidate-patch member;
- label stability across frozen sensitivity settings;
- proportion of recovery uniquely attributable to near-disconnected patches;
- number and spatial extent of operational survey objects.

## Prohibited claims

ODSP must not claim that graph disconnection proves:

- genetic isolation;
- demographic independence;
- habitat fragmentation;
- a dispersal barrier;
- absence in the intervening area;
- occupancy probability.

## Publication target

A mature paper should frame ODSP as a new geographical survey-object representation rather than a new SDM. The strongest target is *Methods in Ecology and Evolution* after multi-taxon and prospective confirmation. *Ecological Informatics* is appropriate for a computational-method paper with narrower empirical validation.

## Boundary with related repositories

- ACSP: finite survey-set selection and same-pool counterfactual evaluation.
- EOG: descriptive geometry of observed states in environmental feature space.
- ODSP: construction and validation of occurrence-relative survey patches in geographical space.
