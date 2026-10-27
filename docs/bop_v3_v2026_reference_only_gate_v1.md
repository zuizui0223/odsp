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


## First source-qualified outcome (closed)

The first official reference-only GitHub Actions run passed:
[workflow 40270328971](https://github.com/zuizui0223/odsp/actions/runs/40270328971),
official reference probe job 121401647193 at head
266cc965c573f3b22e352a47ae9d6642d77d50aa.

**Source receipts**:

- Frozen contract committed before reference access at
  cf8d1cc94cf78b128911b31c43ff096fe4b32fd2.
- Contract SHA256:
  cec6373d5787e83c9966ead902dc09aeffef179daa69ea68bde2f65d9ecd25ba.
- Original source-only JSON artifact ID 12627019951, ZIP SHA256
  a75379cd04409e316f3b05d3d193ccaaea6bac360bfc817179e9dbdc7c2811f5;
  original JSON SHA256:
  a380740b228cea7c52b1b58d9b8aeb81c28aed00f526d80e794b22a3c7353fb8.
- The complete original safe summary is now retained in
  research/BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_FIRST_RESULT.json and the
  pinned interpretation is in BOP_V3_V2026_REFERENCE_ONLY_GATE_V1_TERMINAL_RECEIPT.json.

The original reference CSV contains 35 rows for 35 unique animals.
The September 2026 reference CSV contains **46 rows but 45 unique animal
IDs**. Exactly **one known alias correction** was applied, leaving all
35 older unique animal IDs matched in the new reference and **10 new
ID candidates**, split as follows:

| Original canonical taxon | v3 individuals | 2026 individuals | New ID candidates |
|---|---:|---:|---:|
| Asio flammeus | 3 | 5 | **2** |
| Buteo buteo | 5 | 6 | **1** |
| Circus aeruginosus | 9 | 15 | **6** |
| Circus cyaneus | 9 | 9 | **0** |
| Circus pygargus | 9 | 10 | **1** |
| **Total** | **35** | **45** | **10** |

The provider's version note says a historical out-of-scope animal
was removed, but the **reference roster itself** shows no missing old
unique ID after the corrected-alias normalization (old-absent count
0). That is a source-meaning distinction, not grounds to "repair" the
source or inflate the unseen group count. A removal from GPS observations
must not be confused with removal from the metadata reference roster.

No stratum contains ten new IDs. The largest single-species candidate
frame is six Circus aeruginosus animals. At alpha 0.10, six potential
calibration group gains give rank floor((6+1)*0.1)=0: a **vacuous**
one-sided finite-sample lower bound even *before* reserving any separate
untouched validation animal. Thus the predeclared terminal is

    NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT

The original BOP model, state scores and terminal mixed status remain
untouched. No GPS or biological outcomes were read in this test.
**This same-source 2026 reference update cannot support the frozen
new-individual 90%-rank endpoint**, and the route must not be rescued by
pooling species or reducing the 90% target after source inspection.

The replay validator,
scripts/validate_bop_v3_v2026_reference_first_result_v1.py,
checks byte-identical first-result content, the pre-source contract
digest, exact official source hashes, original species-specific counts,
the no-GPS restriction and terminal status. Source drift or failure
will be recorded and **cannot silently change the frozen conclusion**.


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
