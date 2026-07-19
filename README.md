# ODSP — Occurrence-Defined Survey Patches

ODSP constructs operational survey patches in geographical space relative to known occurrence patches.

The central question is not which raster cell has the highest suitability. It is whether an environmentally supported candidate patch is:

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
held-out or future detections -> patch-level recovery evaluation
```

Connectivity classes:

- `occurrence_patch_extension`
- `near_disconnected_occurrence_patch`
- `remote_candidate_patch`

"Disconnected" is an operational graph label under predeclared distance rules. It does not imply genetic, demographic, habitat, or dispersal isolation.

## Relationship to ACSP

ODSP was motivated by a later island application of ACSP. The validated ACSP study asks how finite survey selections should be constructed and compared with same-pool counterfactuals. ODSP asks a different question: what spatial object should be surveyed when an undiscovered population may lie near, but outside, a known occurrence patch?

ACSP remains one possible source of candidate-support layers, but ODSP is support-model agnostic.

## Relationship to EOG

EOG describes observed point-cloud geometry in environmental feature space. ODSP constructs survey patches in geographical space and evaluates them using withheld or future detection clusters. ODSP does not use environmental gaps as proof of fragmentation or barriers.

## Campanula microdonta case

The initial motivating case uses records available through 2025 to construct patches and 2026 field detections for external illustration. This case revealed the limits of global Top-k point ranking across islands and motivated occurrence-relative patch representation.

Because the patch method was developed after inspecting the first field result, this case is method development and preliminary external illustration, not untouched confirmatory evidence.

## Confirmatory target

The primary future endpoint is the additional recovery of held-out occurrence clusters missed by occurrence-extension searches but recovered by near-disconnected candidate patches.

Required baselines:

- occurrence buffers / extension-only search;
- nearest-known outward search;
- single-threshold geographical clustering;
- DBSCAN or equivalent simple clustering;
- support-only candidate patches;
- random candidate patches from the same eligible pool.

The method should be evaluated across multiple frozen taxon-region pairs and at least one independent prospective field season.

## Status

Early research implementation migrated from `zuizui0223/acsp` PR #39. Barrier/corridor claims from the early development branch are not part of the ODSP headline method.
