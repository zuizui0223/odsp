# BOP_RODENT v3 vs September 2026: outcome-blind animal roster gate

## Why this is necessary

The prospectively closed ODSP BOP_RODENT endpoint trained and validated
on the checksum-pinned Zenodo v3 release (DOI 10.5281/zenodo.10055071)
containing 35 publicly documented tracked birds (2020–2022).
Thirty passed the frozen individual scoring gate and the terminal
classification was **empirical_state_prediction_mixed**, with
27/30 positive individual log-score gains.

Zenodo also publishes an updated September 4, 2026 release
(DOI 10.5281/zenodo.17310324). Its **public page** states that
the animal-reference roster grows from 35 to 45 individuals and adds
GPS years 2024 and 2025. Crucially the same release changes old
2020–2022 source MD5 checksums, corrects one animal ID and removes
an out-of-scope animal. **45 minus 35 is not evidence of ten new
independent available validation animals.** Shared source-study
identity 1278021460 also forbids calling this an independent
study or an independent geographic population replication.

## Metadata-only source frame frozen before any reference download

The pre-outcome contract is:
research/BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_CONTRACT.json.

Two and only two permitted files:

- Original v3 reference CSV
  https://zenodo.org/records/10055071/files/BOP_RODENT-reference-data.csv?download=1
  source MD5 **81e85243e38823db4bde56e315b596f8**.
- September 2026 reference CSV
  https://zenodo.org/records/17310324/files/BOP_RODENT-reference-data.csv?download=1
  source MD5 **fc4623f4dd5f32ef228b3dae386b2c1a**.

**GPS/event data, altitude, speed, per-event times and held-out outcomes
must not be downloaded, opened, or used to choose animals in this gate.**
Only official reference-data CSV bytes can be accessed. Every source is
checked against the declared MD5 and a 250kB size ceiling; no replacement,
mirror or post-result source search is authorized.

The source-only script is:
scripts/bop_v3_v2026_reference_roster_preflight_v1.py.

Its count semantics are conservative:

1. Parse the provider-declared animal-id and animal-taxon columns.
   Multiple tag deployments are not multiple independent animals.
   Any blank animal/taxon or conflicting taxa fail closed.
2. Check the version's 35 and 45 advertised distinct animal counts.
3. Normalize **only the declared** H200701 → H197221 corrected animal
   ID, when the original and current references actually exhibit the
   correction, rather than claiming the corrected ID is new.
4. Preserve the provider's known removed H200730 animal as old
   attrition, not as a candidate.
5. Intersect old and new animals by adjusted animal ID, requiring
   unchanged taxon labels. An unexpectedly missing old identity,
   corrected alias ambiguity or changed species is an identity hold.
6. Report only aggregate new-ID candidate counts *per species*,
   source and roster SHA256 hashes and a status. No original animal
   identifiers, deployment rows or tracking observations are
   redistributed.
7. A 90% finite nonvacuous rank bound requires at least nine
   independent calibration individuals and one separate validation
   individual **within the same stratum**, before considering
   training-group support. Therefore at least 10 genuinely new
   same-species individual IDs is a *necessary count*, not sufficient
   biological evidence; telemetry eligibility and equal-distribution
   group exchangeability remain untested.

## Decision categories

- SOURCE_UNAVAILABLE: provider reference was inaccessible, changed
  checksum or violated source constraints; no substitute is selected.
- METADATA_SCHEMA_MISMATCH: original reference columns/animal counts
  cannot be reliably parsed.
- VERSION_IDENTITY_AMBIGUOUS: correction, disappearance or taxon
  conflict prevents a defensible new-ID count.
- NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT: the reported candidate
  ID count is insufficient within every taxon to split a nine-animal
  calibration cohort and at least one validation individual.
- METADATA_ONLY_CANDIDATE_NEEDS_OUTCOME_BLIND_GPS_ELIGIBILITY: one
  species passes that crude necessary roster count, but **not** yet
  telemetry eligibility, source temporal independence, individual
  group exchangeability or prediction performance.

These statuses preserve scientific missingness and avoid using extra
GPS fixes as fake independent individuals.

## How to execute

Run the deterministic synthetic reference fixtures first:

    python -m pytest tests/test_bop_v3_v2026_reference_roster_gate_v1.py

Then run the **metadata-only** source check:

    python scripts/bop_v3_v2026_reference_roster_preflight_v1.py --out /tmp/bop-reference-only-v1.json

The dedicated GitHub workflow pins the outcome-free comparison
result in an artifact and never opens a GPS dataset.

## What remains deliberately unopened

Regardless of source gate result, the next ecological endpoint must
freeze all still-unseen individual/source identities, tag metadata,
deployment continuity and independent-group admission before opening
per-event GPS height or time data. Previously scored BOP v3 birds
must not be misclassified as untouched validation groups. Even if
distinct additional animals are present, being in the same Movebank
study does not support external **study-level** transfer.

The ODSP BOP closed prospective terminal and the new managed
categorical known-truth results remain unchanged.
