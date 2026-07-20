# ODSP — Occurrence-Defined Survey Patches

ODSP constructs operational survey patches in geographical space relative to known occurrence patches.

The central question is not which raster cell has the highest suitability. It is whether a supported candidate patch is:

1. a continuous extension of a known occurrence patch;
2. a nearby but disconnected candidate patch; or
3. a remote candidate patch.

ODSP is designed for bounded, fragmented, or island survey systems where sparse occurrences, small accessible areas, coarse environmental grids, and strong geographic boundaries can make ordinary cell ranking difficult to interpret.

## Scientific scope

ODSP does **not** estimate occupancy probability, prove population isolation, infer barriers, or replace SDMs. It accepts any defensible candidate-support layer and changes the downstream survey object from ranked points to geographical patches.

```text
known occurrences -> occurrence radius graph -> occurrence patches
candidate support -> thresholded radius graphs -> persistent candidate patches
candidate patches x occurrence patches -> edge-to-edge connectivity classes
held-out or future detections -> member-level patch recovery
```

Connectivity classes:

- `occurrence_patch_extension`
- `near_disconnected_occurrence_patch`
- `remote_candidate_patch`

“Disconnected” is an operational graph label under predeclared distance rules. It does not imply genetic, demographic, habitat, or dispersal isolation.

## Implemented workflow

The package now provides:

- threshold-persistent candidate-patch construction;
- occurrence radius-graph patch construction;
- occurrence-relative edge-to-edge classification;
- observed-medoid clustering of field detections;
- nearest-member multi-radius recovery;
- extension-only versus extension-plus-near-disconnected incremental recall;
- connectivity-label sensitivity and class-frequency summaries;
- pair-first confirmatory benchmark summaries;
- frozen taxon-region manifests and ACSP export adapters;
- an auditable batch runner for the complete frozen cohort.

## Relationship to ACSP

ODSP was motivated by a later island application of ACSP. The validated ACSP study asks how finite survey selections should be constructed and compared with same-pool counterfactuals. ODSP asks a different question: what spatial object should be surveyed when an undiscovered population may lie near, but outside, a known occurrence patch?

ACSP remains one possible source of candidate-support layers, but ODSP is support-model agnostic.

## Relationship to EOG

EOG describes observed point-cloud geometry in environmental feature space. ODSP constructs survey patches in geographical space and evaluates them using withheld or future detection clusters. ODSP does not use environmental gaps as proof of fragmentation or barriers.

## Campanula microdonta development case

The repository includes the corrected 2026 positive field GPS inventory and `case_studies/campanula_microdonta/run_case.py`. The runner accepts frozen historical-occurrence and candidate-support CSVs, constructs ODSP patches without reading field outcomes, and then writes detection clusters, class-specific recovery, incremental recall, sensitivity labels, and an audit manifest.

Because ODSP was defined after the first ACSP field result was inspected, this is a method-development and preliminary external case, not untouched confirmatory evidence.

```bash
python case_studies/campanula_microdonta/run_case.py \
  --candidates frozen_candidate_support.csv \
  --occurrences historical_occurrences_through_2025.csv
```

## Confirmatory benchmark

`validation/frozen_taxon_region_manifest.csv` freezes 48 independent taxon-region pairs inherited from two ACSP confirmation cohorts: 24 mixed plant/animal pairs and 24 non-overlapping plant pairs.

The `odsp.acsp_adapter` module accepts only complete fold exports containing explicit training occurrences, held-out occurrences, and training-only candidate support. Legacy ACSP exports that retain coverage IDs without the corresponding coordinates are marked `blocked_incomplete_legacy_export`; coordinates are not guessed or reconstructed post hoc.

Complete exports can be evaluated in one batch:

```bash
python validation/run_frozen_benchmark.py \
  --layout mixed_20260705=/path/to/mixed_exports \
  --layout plants_20260706=/path/to/plant_exports \
  --output validation/results
```

The runner writes `adapter_audit.csv` for every adapted or blocked fold, plus unit metrics, unit status, pair-first cohort summaries, and `run_manifest.json` when evaluable inputs exist. `intention_to_evaluate_complete` is false whenever any frozen unit is missing or blocked.

The primary endpoint is:

```text
recall(extension + near-disconnected) - recall(extension only)
```

Required baselines include occurrence buffers, nearest-known outward search, single-threshold clustering, DBSCAN or an equivalent simple clustering rule, support-only patches, and same-pool random patches.

## Status

Research implementation migrated from `zuizui0223/acsp` PR #39. The method, benchmark contract, frozen independent cohort, export adapter, and batch execution/audit path are implemented. The remaining data-producing dependency is to extend or rerun the ACSP fold exporter so every frozen fold writes explicit training, held-out, and candidate-support coordinate tables. Corridor/barrier inference and survey-budget ranking are not part of the ODSP headline method.
