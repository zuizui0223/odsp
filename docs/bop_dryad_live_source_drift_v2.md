# Dryad v1 original evidence vs live-source drift: operational check v2

## Why this repair exists

Original source-only Dryad preflight was frozen before the official first run
([GitHub Actions 40275944700](https://github.com/zuizui0223/odsp/actions/runs/40275944700)).
The first report and its source fingerprints remain immutable. A subsequent
official replay failed only because the **raw SHA256 of the Dryad `/versions`
JSON changed**. This is a true source-response drift, but by itself it is
**not evidence of a new ecological dataset version or a prediction failure**.

Previous evidence and its failing CI are not deleted or reclassified.

## Separate, explicit checks

1. Strict original-evidence check:
   `scripts/validate_bop_dryad_external_schema_first_result_v1.py`
   is run against the **original archived v1 scientific summary**, not
   today's changing provider response. It still rejects any change of the
   frozen contract, initial evidence, archive IDs, source SHA or historical
   BOP model verdict.

2. Live-source drift diagnostics:
   `scripts/classify_live_bop_dryad_source_drift_v2.py` classifies a
   later official source-only response as:
   - `EXACT_FIRST_SOURCE_REPLAY` if every sanitized field is identical;
   - `SOURCE_METADATA_DRIFT_HOLD` when source response fields differ but
     provider access roles remain unchanged;
   - `SOURCE_ACCESS_CHANGED_HOLD` when a previously accessible API
     or small non-GPS sidecar becomes unavailable/available.

   It records **only changed field paths**, not source identifiers,
   animal/GPS records or changed raw provider values. It cannot promote
   the Dryad dataset to an empirical validation sample. A modification of
   the original BOP `mixed` terminal, proposed reuse of an incompatible
   original RF, newly read GPS outcomes or changed scientific contract
   triggers an **error**, not an allowed source drift status.

3. Semantic version-level test:
   The existing, separately frozen
   `scripts/bop_dryad_semantic_version_v2.py` is the stronger qualified
   comparison for substantive Dryad *source identity*: it checks
   DOI, published version link/date/license and exact five filenames
   and sizes from API metadata, excluding known volatile bookkeeping
   fields. It never downloads GPS files.
   **Raw-response drift classification is not an independent semantic
   version qualification.** These two diagnostics answer different
   questions and their outcomes are not substituted.

## Execution

```bash
python -m pytest tests/test_bop_dryad_live_source_drift_v2.py
python scripts/validate_bop_dryad_external_schema_first_result_v1.py --result research/BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_FIRST_RESULT.json
python scripts/bop_dryad_external_schema_preflight_v1.py --out /tmp/bop-dryad-live-source.json
python scripts/classify_live_bop_dryad_source_drift_v2.py \
  --result /tmp/bop-dryad-live-source.json \
  --out /tmp/bop-dryad-live-drift.json
```

The source probe remains restricted to the two known Dryad JSON endpoints
and three fixed small non-GPS sidecar IDs. It holds on 403 or an unpinned
redirect rather than downloading any 888 MB/2.16 GB GPS file. The two
metadata API responses had been readable; all three sidecars were
403-unavailable. Source changes after the first run remain visible.

The scientific endpoint remains:
**`EXTERNAL_METADATA_CANDIDATE_NOT_ADMITTED`**.
The original BOP_RF lacks an equivalent `external-temperature`
predictor in the documented Dryad Data_1a schema, source coordinates
are rounded to 0.1°, animal and source-study overlap remains unknown,
and no real held-out bird accuracy, altitude or positive group gain is
inferred. No BOP or Dryad empirical endpoint is reclassified.
