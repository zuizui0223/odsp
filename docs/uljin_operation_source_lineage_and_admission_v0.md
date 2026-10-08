# Uljin ungulates: outcome-embargoed source and operation-log admission

**Phase status:** outcome-free astronomy calendar PASS; raw dataset/source
eligibility HOLD. This is a prospective *research design* and source-quality
workflow, not a finding about ungulate behaviour or photoperiod hysteresis.
The original Rhode Island observations and qualified ODSP methods are
untouched.

## Source evidence and the problem to solve

Jeon & Lim (2026), Biodiversity Data Journal 14:e191556
(DOI 10.3897/BDJ.14.e191556) report 82 camera stations in two nearby
study regions UJ1 (52 stations) and UJ2 (30 stations); 4,623 independently
filtered ungulate detections from four taxa; and 29,850 functional
camera-nights out of 30,410 scheduled, with 560 inactive nights.

The public EcoBank v1.1 package DOI 10.22756/ETC.20260000001022
is said to contain separate camera-operation windows and downtime logs,
event records, station covariates, station×season effort and QA tables.
Event timestamps are local standard time Asia/Seoul (UTC+09).

**Important provenance distinctions:**

- An article mentioning a deployment/downtime log does not prove its
  values were originally recorded independently of camera photos.
- Whole-night functioning status does NOT supply device operation by
  hour, and a camera that was operational does not imply a constant
  detection probability across clock hour, season or vegetation state.
- The public release withholds precise protected-species station
  coordinates. The published points are REGION-level representative
  coordinates, not an individual camera's true location. We must
  not manufacture exact station latitudes/longitudes.
- Within-region cameras may share landscape, operator, weather and
  animal movements. 82 cameras are NOT 82 iid regional samples. The
  across-region population sample is only TWO region clusters.
- Existing article photoperiod-adjustment examples mean the existence
  of a solar-time effect in this dataset is not a new unpublished
  discovery by itself.

## Stage A completed: astronomy-only pairs

The immutable v0 plan compares dates ascending toward the June
solstice (May 1 to Jun 10, 2022) against dates descending after the
solstice (Jul 1 to Aug 31). The source-free original pre-outcome rule
uses representative latitude 36.85°N, NOAA apparent zenith 90.833°,
one-to-one pairing without calendar-date reuse, at least 21 days
between dates and at most 9 minutes daylength mismatch.

Official first original CI run 37771342454 PASS:
41 nonoverlapping calendar date pairs, worst daylength discrepancy
0.544315 minutes. It opened NO species detections, source operation
rows or metadata bytes. First outcome-free result is preserved at
https://github.com/zuizui0223/odsp/actions/runs/37771342454.

This does NOT mean any one station operated across a matched pair,
nor that any ungulate was detected on both dates. Sites and pairs
must be verified separately against ORIGINAL operation logs, with
an operator-independent source-value lineage and zero-selection-on-
detection rule.

## Stage B: verify the operation source without touching outcomes

The independent frozen source preflight
ULJIN_OPERATION_METADATA_HEADER_PREFLIGHT_V0_CONTRACT.json requires:

- an authentic v1.1 EcoBank ZIP supplied through an explicit path and
  its documented version/integrity metadata; no invented direct link;
- inspect only the ZIP central directory and FIRST CSV HEADER LINE
  of 01_core_data/camera_operation_log.csv;
- **never** open or read a byte of the
  01_core_data/cameratrap_event_records.csv member;
- never read an operation LOG DATA ROW, station ID, animal species or
  event time; never publish detailed location or operation times;
- reject encrypted ZIPs, unsafe paths, duplicate members and archive
  sizes exceeding the predeclared ceilings;
- report only source ZIP digest and operation column names with all
  evidence/admission flags initially FALSE.

The standalone program
scripts/uljin_operation_header_preflight_v0.py
emits SOURCE_ARCHIVE_NOT_MATERIALIZED when a trustworthy direct
EcoBank v1.1 archive is unavailable. The current verified DOI is a
landing identifier; it has not been verified as a downloadable ZIP.
It MUST NOT silently substitute a PDF, an earlier v1.0 release, or
a different site's data.

A correct header only establishes a probable mapping for a later
predeclared OPERATION-RECORD audit. It does NOT certify that reported
downtime intervals have hours/minutes rather than days, that timestamps
reflect field deployment rather than first/last wildlife photographs,
or that the expected 41 date pairs have functioning devices.

## Three necessary proofs before opening event-level wildlife records

1. **Source-value lineage:** independently dated hardware install/
   retrieval/maintenance logs, demonstrably not revised using the
   animal detection sequence. A file hash and publication date alone
   are insufficient.
2. **Exposure reconstruction:** actual operating time in the
   predeclared time categories for BOTH dates at each station.
   If only functional *nights* are available, label
   HOLD_HOURLY_EXPOSURE_UNKNOWN; a daylength-matched site-day event
   comparison is NOT automatically exposure corrected.
3. **Sampling support:** count eligible station×date pairs from the
   complete operation frame, including cameras with ZERO detections.
   Group by UJ1/UJ2; no relabelled iid-site or entire-region claim.
   The actual number of eligible station pairs remains unknown.

Only after these stages could a NEW source-specific, prospectively
frozen observation scoring contract specify station holdouts,
species-level support and valid effort-normalized temporal
densities. The original calendar design must never be changed
postoutcome to increase the number of positive stations or
enhance a desired direction.

## New biological hypothesis and what can disprove it

The interesting scientific hypothesis is not that the clock and
the sun disagree, but whether **rising-versus-falling photoperiod
branch** carries transportable residual information among near-
equal-daylength dates at the same station.

At equal astronomical geometry, a model that depends ONLY on
solar phase and species predicts the same phase distribution.
A stable branch-dependent residual, evaluated on unseen
stations with externally logged hour-level camera effort,
would be consistent with season-specific ecological context,
not necessarily endogenous animal photoperiod memory.
Ambient temperature, food phenology, human disturbance,
predator pressure and species detection can remain confounders.

If no branch residual exists after proper normalization, that is
an informative negative result for this particular predictive
definition, not evidence that photoperiod has no biological effect.

## Current stop boundary

The first 41 astronomical pairs are VALID AS A PLANNING CATALOG.
Real camera-eligibility numbers, time-stratified operating effort,
matched ungulate detections and any seasonal hysteresis effect
are NOT YET VERIFIED. Do not classify them as a new positive ODSP
ecological result, an external confirmation of Rhode Island, or a
qualified stochastic process probability inference route.
