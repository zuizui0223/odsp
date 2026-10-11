# Original EcoBank v1.1 Uljin wildlife archive: biological feasibility before ecological effect estimation

The last confirmed original public dataset release is attributed to the
National Institute of Ecology NIE EcoBank Version 1.1, DOI
https://doi.org/10.22756/ETC.20260000001022 (KOGL Type 1 attribution).
Jeon & Lim 2026, Biodiversity Data Journal 14 e191556,
https://doi.org/10.3897/BDJ.14.e191556, document the following
original archive members:

- `01_core_data/cameratrap_event_records.csv`: original focal ungulate
  independently deduplicated station/species/date/time events;
- `01_core_data/camera_operation_log.csv`: potentially original device
  deployment / downtime record, requiring original schema audit;
- `01_core_data/site_covariates_public.csv`: only public protected-site
  generalized representative coordinates/covariates;
- `03_documentation/MANIFEST.tsv`: released file inventory, NOT by
  itself proof of hosting provenance or external checksum.

The journal's **supplementary files** provide plots and processed
temporal overlap/rate tables, NOT automatically the above original
EcoBank v1.1 event and independent hourly deployment members.
Do not pass a supplementary figures ZIP as the original raw source.
An attempted direct DOI fetch did not return the original data archive.

## What was implemented before original source access

`odsp/uljin_original_source_zip_feasibility_v0.py` plus
`scripts/run_uljin_original_v1p1_source_feasibility_v0.py`:

1. Require a user-obtained original EcoBank Version 1.1 ZIP AND an
   independently attested 64-character SHA256 checksum from its
   hosting record. Compare SHA256 on the raw entire ZIP BEFORE
   opening source records. Source archive naming alone is not
   sufficient identity evidence.
2. Verify original archive members are present, only allow sane
   non-traversal paths and a bounded total expanded size, and
   check published independent event table column labels.
3. Preserve the PREEXISTING 41 matched rising/falling
   astronomical daylength pairs. These are **May 1–June 10 2022**
   versus **July 1–August 31 2022**, NOT spring versus autumn.
   Do not rematch or select calendar dates based on event counts.
4. For EACH of all four prespecified taxa, report original
   event counts in both calendar branches and fixed solar
   core/edge/night time zones, the number of unique original
   PHYSICAL camera stations with events in each branch, the
   intersection of station rosters with events in both branches,
   numbers of original date pairs with at least one event on
   each date at a shared station, and numbers of station×pair
   cells with both dates detecting that taxon. All zeros remain.
5. Report event and original operation-log CSV headers and row
   counts ONLY. Operation log field names MUST be independently
   mapped to start/end/downtime hour intervals and externally
   attested before trying to calculate camera-hour denominators.
   Do not infer hourly operation from `station_season_effort.csv`
   functional nights, or infer source completeness from a ZIP
   filename.
6. Flag <30 independent released events in EITHER photoperiod
   branch or <8 physical event sites appearing in BOTH branches
   as LOW_SUPPORT, but do NOT delete the taxon or station from
   the report. This is NOT statistical power or a test.

Example, after external original archive provenance was verified:

```bash
python scripts/run_uljin_original_v1p1_source_feasibility_v0.py \
  --original-v1p1-zip /safe/original/EcoBank_V1p1.zip \
  --independently-attested-original-v1p1 \
  --original-release-sha256 ACTUAL_64_HEX_SHA256_FROM_TRUSTED_RELEASE_HOST
```

The default with NO archive prints a strict
`HOLD_NOT_ORIGINAL_SOURCE_INPUT_AND_CHECKSUM_ATTESTED`,
so CI and readers cannot accidentally mistake synthetic or
published full-period aggregate data for the original fixed
41-pair outcome.

## What remains unavailable and non-claimable

The original NIE EcoBank ZIP itself and externally documented
SHA256 identity have NOT been supplied in this repository.
The output of the above preflight is only
`SOURCE_ATTESTED_ORIGINAL_EVENT_TIMESTAMP_FEASIBILITY_ONLY`
after original source and independent checks. That would
answer the key ecological design question **which ungulate taxa
and unchanged physical sites have enough timestamps to compare?**

Even if timestamps are complete, temporal refuge *RATE* effects
require verified camera-hours within all 3 original solar
zones on BOTH paired dates from the original operation log.
Independent detector calibration for source q would still be
necessary to infer latent activity rather than detected
encounters. Environmental temperature/human activity
mechanisms additionally require independently time-resolved
exposure sources; no causal thermal/competition/zeitgeber
claim can be inferred from timestamps alone.

No original protected camera station GPS are requested,
inferred, downloaded, or released by the preflight.
All previous qualified ODSP findings and artificial
detector-q first-result routes remain unchanged.
