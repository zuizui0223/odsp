# NIE EcoBank Uljin Version 1.1 source acquisition status — 2026-10-11

## Research purpose

Original source event timestamps and camera operation chronology are
needed to test the **ecological** hypotheses in PR #264:
(1) central-daylight to daylight-edge time refuge,
(2) daylight to nighttime redistribution, and
(3) species-specific differences in the same original matched
daylength pair, while retaining all four ungulates and all original
41 paired 2022 dates.

**Important calendar clarification:** original rising-daylength dates
are 2022-05-01..06-10 and original falling-daylength dates are
2022-07-01..08-31. They are early growing season vs midsummer,
NOT a spring-autumn comparison.

## Grounded public source facts

Jeon J-H and Lim A (2026), Biodiversity Data Journal 14 e191556,
https://doi.org/10.3897/BDJ.14.e191556, explicitly document
the year-long field dataset as **4,623** original independent
ungulate detections at **82** camera stations. The focal events
span 2022-05-01 to 2023-05-22; neither that whole-period number
nor a published activity overlap figure is the event sample size
of the preselected 41×2 astronomical 2022 dates.

The journal names the NIE EcoBank original data DOI
https://doi.org/10.22756/ETC.20260000001022 as Version 1.1,
while its landing-page title may continue to say v1.0. The
publication identifies these original members:

- `01_core_data/cameratrap_event_records.csv`
- `01_core_data/camera_operation_log.csv`
- `01_core_data/site_covariates_public.csv`
- `03_documentation/MANIFEST.tsv`

The publication says original operation windows and downtime
are included. This does not establish that the source CSV
contains every physical station's exact hour-level on/off
history until the actual content and schema are inspected.

The publicly indexed journal supplementary files
(`oo_1559452.zip`, `oo_1559453.zip`,
`oo_1559451.zip`) are respectively published
pairwise time-curve/overlap, photoperiod-adjusted
sensitivity, and rate-normalized daypart summary material.
These do NOT themselves constitute the separate original
NIE EcoBank release with required event and operation members.
Linked Zenodo supplement listings give only summary products.

## Acquisition attempts and their outcomes

1. DOI 10.22756/ETC.20260000001022 was found in
   journal metadata, but the web retrieval route did not return
   an original archived ZIP or validated member bytes in this
   session. Do not claim the original archive is downloaded.
2. Public web searches on exact dataset DOI and names
   `cameratrap_event_records.csv` and
   `camera_operation_log.csv` identified the published
   reference but did not reveal an independently authenticated
   direct ZIP file with a verifiable original Version 1.1
   release digest. An empty web search is not proof a file
   does not exist on the official portal.
3. Public NIE EcoBank Open API documentation at
   https://www.nie-ecobank.kr/data/api/intrcn.do shows that
   its **separate geospatial** service uses API access keys
   and approval. This is NOT evidence that the article's
   archived DOI ZIP requires that particular API key;
   the archive download and geospatial API are distinct workflows.
4. A scoped GitHub code search for the exact source filenames
   and DOI found no matching publicly searchable repository
   copies. Connected Google Drive search for EcoBank,
   cameratrap_event_records and Uljin returned no results.
   These are discovery results, not proof the data are
   unavailable to the right user or not on the provider portal.
5. The current Project/Library file content search did
   not identify a user-uploaded original release archive;
   downloaded CI artifacts with “uljin” filenames are
   **synthetic method results**, not original animal data.

## Minimum trustworthy ingestion path

1. Obtain the original **Version 1.1** archived release
   using the official EcoBank DOI landing page or its
   authenticated public download workflow. Retain exact
   official landing URL, original release/version and
   original licensing/attribution.
2. Record the SHA256 digest of the downloaded original
   archive, preferably corroborated by independently
   published release checksums or download authentication
   metadata; if no independent hash is published, its
   external provenance requires a separate attestation
   procedure. Do NOT invent a trusted external SHA256.
3. Run
   `scripts/run_uljin_original_v1p1_source_feasibility_v0.py`
   with an independently attested original release/checksum.
   That preflight verifies the four raw members and
   counts original species/branch/dayzone event timestamps,
   original same-PHYSICAL-station mirrored day pairs,
   low-support flags and the original source camera
   operation-log headers without guessing source hours.
4. Independently normalize and attest original camera
   operation start/end intervals (including downtime)
   in Asia/Seoul local clock time, preserving the full
   station×original 82 dates. Do not use station-season
   functional nights as an hour-by-hour denominator.
5. Only when true original clock-hour effort is known,
   run the descriptive, four-species
   `scripts/run_uljin_ecological_zone_rates_v0.py`.
   Then consider independent detector q and physical-site
   uncertainty before any claim of latent behavior.

## Current warranted scientific status

`HOLD_NOT_ORIGINAL_SOURCE_INPUT_AND_CHECKSUM_ATTESTED`

No authentic event rows, hour-verified camera operation,
species-specific 41-pair counts, ecological H1/H2/H3 rate
effect sizes, latent animal activity or causal sunlight/
thermal/competition mechanisms have been verified.

**Implementation correction dated 2026-10-11:** two
different physical cameras with events on opposite dates
of a mirrored pair are NOT one biologically paired site.
The source feasibility algorithm now requires both
event-positive dates to come from the SAME station and
has a regression fixture where the two stations each
appear in both branches but never on the corresponding
matched-pair dates. The test must report ZERO true
paired-station positive detection cells in that case.

All previously qualified ODSP results, original 41-day
calendar freeze and source-free camera-q demonstrations
are unchanged.
