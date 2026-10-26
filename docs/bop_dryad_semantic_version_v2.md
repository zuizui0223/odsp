# BOP Dryad semantic version v2: metadata response drift correction

## Preserved history: v1 raw API response SHA failure

The first Dryad source-only analysis confirmed that the original BOP_RF
cannot be directly executed on the documented Data_1a covariates:
external temperature is absent and coordinates are rounded to 0.1°.
It also retrieved Dryad's public dataset/versions JSON, explicitly
verified a CC0-1.0 license, and found HTTP 403 for all three small
non-GPS direct download links.

That source result was frozen in
BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_TERMINAL_RECEIPT.json.

**A later direct replay FAILED on v1's raw /versions response SHA256**,
even though the feature and source-admission conclusions were identical.
Raw API JSON may contain unstable bookkeeping or generated fields; it
must not be interpreted by itself as a change of biological source.
The v1 response SHA mismatch and failed workflow remain historical
evidence. Neither v1 result nor v1 receipt is silently edited.

## Distinct v2 semantic source identity

The new v2 contract was committed before first v2 external response:

research/BOP_DRYAD_SEMANTIC_VERSION_V2_CONTRACT.json

The qualification question is narrower: *Can the published data
version be pinned by stable, ecologically meaningful provider metadata
despite unstable incidental API response bytes?*

Only three HTTPS GETs to official Dryad JSON APIs are permitted:
the DOI dataset record, its list of publicly visible versions and
the **file inventory metadata** for the current published version ID.
No direct file downloads, no README sidecar, no Data_1a or Data_2a
GPS bytes and no individual identifiers are accessed.

The candidate DOI and full public version roster must agree, including:

- dataset DOI **doi:10.5061/dryad.n8pk0p398**;
- explicit provider license **CC0-1.0**;
- current publication date **2026-08-17**;
- exactly consistent dataset versionNumber,
  _links.stash:version and the latest visible published version
  self href, resolved by the provider's numeric ID;
- exact five published file names and **positive provider file sizes**,
  from file-inventory metadata only.

The stable fingerprint includes the whole published version roster,
version IDs, publication dates, current license and the five filename/
size pairs. It excludes dynamic counters, lastModificationDate,
signed links, publication dashboard download counts and arbitrary
entire-response SHA values.

A changed version link, publication date, license or source file
inventory is a **source/version HOLD**, not silently accepted as a
cosmetic metadata change. A provider API failure also remains an
explicit HOLD. The qualifying result
SEMANTIC_METADATA_VERSION_VERIFIED_ONLY means *metadata identity*
was verified, **not** independent biological group eligibility.

## Known truth and tests

The v2 test fixtures hold version ID/date/license and five file sizes
fixed, while deliberately changing raw download counts, modification
dates and pagination presentation. The expected semantic fingerprint
must remain identical; changing README file size, version ordering,
license, DOI or current version link must cause a fail-closed error.

Executable files:

- scripts/bop_dryad_semantic_version_v2.py
- tests/test_bop_dryad_semantic_version_v2.py

The route runs in the existing
BOP source-only GitHub Actions workflow, not a new competing
ecological research lane.

## Historical primary and future empirical gate

The earlier BOP 30-individual prospective endpoint remains
`empirical_state_prediction_mixed`.
The v2026 same-study ID-count gate remains
`NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT`.

Dryad still lacks the original BOP_RF's documented external-temperature
predictor and only supplies 0.1°-rounded locations, so even fully
verified version identity would **not** constitute a direct external
RF validation. Exact individual/study overlap and group exchangeability
remain unverified. Any different common-feature learner needs a fresh
prospective design and independent biological calibration/validation
groups before opening GPS outcomes.
