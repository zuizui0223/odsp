# Untouched external freeze semantic lock v2

## Why v2 exists

The first untouched-external contract verified that a concrete freeze artifact
existed before declared external-outcome access and that its SHA256 matched the
runtime declaration. That proves artifact identity, but hash identity alone does
not prove that the frozen artifact describes the analysis actually run.

Version 2 closes that gap. The canonical `transfer-refits-external` CLI now
requires a machine-readable freeze manifest whose scientific and inferential
contents exactly match the runtime endpoint.

## What must be frozen

The manifest must contain:

- an upstream model-set identifier;
- an external dataset identifier;
- a SHA256 of the sorted unique external row-ID roster;
- the exact upstream refit IDs;
- the reference refit ID;
- score semantics;
- every information-level name and information set;
- the directional alternative;
- familywise lower confidence level;
- bootstrap draw count and seed;
- minimum refit count;
- minimum validation blocks per group;
- gain tolerance.

The manifest's internal `frozen_at_utc` must equal the freeze timestamp declared
by the external-validation contract, and that timestamp must predate the declared
first external-outcome access time.

## External row roster lock

The row roster is outcome-free provenance. ODSP sorts the unique external
`row_id` values, joins them with newline separators plus a trailing newline, and
computes SHA256. That runtime digest must exactly equal
`external_row_ids_sha256` in the pre-outcome manifest.

This prevents silently switching the external cohort, sites or held-out rows
after outcomes are available. Outcomes themselves are deliberately not included
in a pre-outcome hash because they are the sealed validation target.

## Refit and analysis lock

The runtime refit IDs must equal the frozen refit IDs after canonical sorting.
The reference refit must match and must be present in that set. Score semantics,
information filtration and all certification settings are compared as normalized
structured values, not prose.

A manifest with a perfectly valid updated SHA still fails if any of those fields
no longer match the runtime analysis.

## Version boundary

The low-level v1 runner remains for compatibility and provenance reconstruction.
The canonical CLI command

```bash
odsp transfer-refits-external --contract endpoint.json --out receipt.json
```

uses the v2 semantic lock. Its receipt has
`odsp_untouched_external_refit_positive_validation_endpoint_v2` as the receipt
type and records the verified semantic lock.

## Epistemic boundary

ODSP can machine-verify file hashes, row-roster identity, timestamps and exact
agreement between frozen and runtime analysis settings. It still cannot prove the
historical human claim that nobody viewed an outcome before the declared access
time, nor independently prove development-data disjointness. Those remain
explicit provenance declarations in the receipt.
