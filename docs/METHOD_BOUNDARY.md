# ODSP–ACSP method boundary

## Different estimands

**ACSP** selects a finite set of survey locations under evidence, diversity, access, and budget constraints. Its output is an ordered or optimized survey set.

**ODSP** constructs geographical survey patches relative to known occurrence patches and tests whether near-disconnected patches recover held-out detections missed by occurrence-patch extensions. Its output is a patch geometry, an occurrence-relative class, and an incremental-recovery estimate.

## What ODSP may consume

ODSP may consume any candidate-support field that was frozen before held-out evaluation. The support may come from a kernel, environmental analogue, expert map, SDM, ACSP component, or another independent method. The producer is recorded as provenance but is not part of the ODSP algorithm.

## What ODSP must not inherit

ODSP must not inherit ACSP candidate ranking, Top-k selection, evidence weights, geographic complementarity objective, route optimization, or same-pool finite-set estimand as part of its headline method.

## Headline comparison

The primary ODSP contrast is:

```text
recovery by occurrence-patch extensions plus near-disconnected patches
minus
recovery by occurrence-patch extensions alone
```

This asks whether explicit patch topology adds recoverable survey area beyond outward expansion around known populations. It does not ask whether one Top-k selector beats another.

## Native benchmark contract

Each benchmark unit contains:

- `unit.json` with taxon, region, fold, support method, and freeze declaration;
- `training_occurrences.csv`;
- `candidate_support.csv` with a normalized `candidate_support` column;
- `held_out_occurrences.csv`.

No ACSP-specific columns, IDs, folder names, or exporter are required.
