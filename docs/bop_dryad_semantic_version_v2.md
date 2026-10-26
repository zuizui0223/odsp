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

## Provenance correction: v1 SHA mismatch was copied, not observed source drift

A follow-up audit recovered the **actual first GitHub Actions JSON**
(artifact 12630760184, ZIP SHA256
`ddc23a16ea20e51e1c630cdc45b2466af0e421e0745aa282b7bb5331283922cd`,
original JSON SHA256
`10181566debf005c51d5a28f6d058a9134fddca33580621d1d9a2ce40b32669e`).
The raw first Dryad `/versions` response SHA256 recorded there is a valid
64-digit digest,
`433835a643d6685935835df2ac3fbb9070d331ff609ffd7f4a623b5083da5c9f`.

By contrast, the subsequently checked-in *semantic copy* omitted nine
characters, yielding a 55-digit invalid digest. The original later v1
replay failed when compared against that corrupted value. Once the
authoritative Actions JSON was restored in a separate, preserved file,
the live metadata preflight at GitHub Actions run **40278424271**
returned `EXACT_FIRST_SOURCE_REPLAY`: the official two API source
response summaries matched the first actual source evidence.

**Correction:** the earlier claim that changed official `/versions`
response bytes were observed is **not supported by the corrected
comparison**. The historical failed replay and frozen v2 design
contract remain unchanged as provenance; the explanation of that
failure is superseded by this correction. The v2 semantic-version
method remains valid and useful for future response drift, but it
must not claim that actual source drift was demonstrated here.

The corrected authoritative raw JSON is now separately archived at
`research/BOP_DRYAD_V1_ORIGINAL_ACTIONS_ARTIFACT_JSON.json`; the
historical copy and receipt are retained without editing, and
`BOP_DRYAD_V1_SOURCE_PROVENANCE_CORRECTION_V2_RECEIPT.json`
documents the nine-character omission.

At the same CI run, the semantic-version route returned
`SEMANTIC_METADATA_VERSION_VERIFIED_ONLY`, provider version ID
**458400**, semantic fingerprint SHA256
`e94f521659adb2cac99047b052bd34ebc150a11ad4f336244a9c0ffce878e5c6`.
No GPS file content, animal identities or scores were opened.
Neither confirmation makes the historical BOP RF directly
feature-compatible with Dryad.


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
