# German red kite original sample provenance: public Movebank study-summary gate

## Why this gate follows the now-complete ZIP/GPS analysis

The ODSP red-kite source audit (merged #286–#291) independently established that the exact deposited 2024 German source CSV contains **159 season-ID strings / 63 bird-ID strings**, and its original-GPS season-coverage screen (>800 fixes after the dated authors' spatial/temporal filter) yields **99 season IDs / 49 bird-ID strings**. The journal article reports **163 initial individual-seasons / 65 birds**, then **99 eligible seasons / 63 birds**. The 2024 ZIP's `R/data_prep.R` was verified byte-identical to the dated GitHub version, but the pre-archive 60-minute subsampling and 163/65 original roster are not reconstructed. The original deposited GPS had **48.74% of positive intervals shorter than 55 minutes** in its 99-season source-eligible sample.

Oppel et al. ([DOI 10.1111/jav.03246](https://doi.org/10.1111/jav.03246)) list three Movebank IDs for tracking data: `230545451`, `1356790386`, and `294443150`. The third is explicitly associated with **Red Kites in Saxony-Anhalt**; it is not guaranteed to cover all of the German birds or both German data providers. Movebank study attributes are live and can be revised, and counts of deployed individuals in a whole study are **not** counts of bird-years in a historical subset. Movebank's permission settings are controlled by data owners.

## The strictly frozen next question

**Can an anonymous public GET for the metadata of source study ID `294443150` return a legitimate study summary without logging in or accepting a licence?** Only a small study metadata row will be read, never animal, tag, deployment or event records.

Before any provider read, contract `research/BOP_RED_KITE_GER_MOVEBANK_STUDY_METADATA_V1_CONTRACT.json` was committed on `2026-11-18` as **`69836d5888a36f5a21a1f604c6ef2528400cc69d`**. It authorizes only:

`https://www.movebank.org/movebank/service/direct-read?entity_type=study&study_id=294443150`

The HTTP GET is unauthenticated and small (at most 64 KiB). The parser checks that the response is exactly one study record with `id=294443150`, validates the red kite study-name match, and emits only safe current study totals and visibility/download permissions. It never exports the raw row, contact-person fields, email addresses, tag IDs or study owner metadata. Provider permission/terms notices, unexpected pages, mismatched study IDs and transport failures produce an explicit **HOLD**.

The output may establish that a **currently accessible** study exists and report its **current totals**. It can neither prove the archived 2024 163/65 roster nor the paper's reported 99/63 eligible birds, because it is not a 2024 frozen source snapshot and the German paper included more than one data source. No outcomes, GPS movements or source animal identities are accessed.

## Scientific stop

No new animal prediction probabilities, no reclassification of the historical BOP mixed endpoint, no new red-kite gain. The red-kite biological endpoint stays `HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`. If metadata are restricted, keep the HOLD rather than attempting credentials/terms acceptance in CI. If metadata are public, another clearly **separately frozen** historical source record and identity crosswalk would still be needed before any individual-level biological inference.

## Offline tests

```bash
python -m pytest tests/test_bop_red_kite_ger_movebank_public_study_meta_v1.py
```

Official GitHub Actions job is gated on Python 3.10/3.12/3.13 safety tests and emits a safe aggregate/permission-status artifact even when source access is unavailable.
