# BOP source-candidate preaccess screening v1 — design / 2026-11-22

## Goal and current evidence gap

ODSP has an immutable source/model/forecast/identity pipeline and exact
positive-content inference. However, that machinery starts AFTER a potential
source has compatible schema and enough independent individuals. There is no
single source-metadata-only triage for these prerequisites.

A retrospective public metadata search on 2026-11-22 preceded this design;
this is an operational metadata screen, NOT a prospectively discovered
biological result, and not a permission or individual-independence audit.

## Fixed scope

Create one pure, offline standard-library API that screens publisher-declared
candidate metadata for two explicitly distinct predictor routes:

1. historic_rf_direct: unmodified BOP RF requires all declared predictor
   fields, including external temperature, and altitude-state semantics.
2. new_reduced_common_input: explicitly different learner requires species,
   timestamp, coarse-compatible longitude, and native GPS altitude state.
   For 90%-positive content at 95% confidence, minimum candidate capacity is
   29 eligible calibration animals + 1 separate validation animal IN THE SAME
   TARGET STRATUM, not 29 total seasons or multiple-model scores.

A metadata screen NEVER admits biological data. It can return only:
- KNOWN_INCOMPATIBLE: one or more supported hard blockers;
- HOLD_METADATA_OR_PERMISSION: incomplete or externally unverified condition;
- ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT: all required fields declared at metadata
  level, but no outcome data or data-source identity validated.

Do not claim cross-source independence from study IDs or reference counts.
A source with "unknown" access, legal reuse, crosswalk or feature remains HOLD.
Preserve all partial blockers simultaneously (count+altitude).
Never combine species/strata or studies to pass an individual-count gate.

## Input and provenance

Each CandidateMetadata contains:
- immutable candidate key, official source URL and published dataset version;
- declared supported species (per-stratum *upper bounds* on animals), not pooled
  observations, deployments, seasons or GPS records;
- status of known required fields (present, absent, unknown);
- independent identity crosswalk to model-train animals (verified, overlap,
  unknown) as an EXTERNAL assertion, never machine certified;
- permission to fetch/use (confirmed_open, requires_consent, unknown);
- source definition compatibility (verified_same_state, incompatible, unknown);
- a route-specific predictor availability declaration with a separate
  "external_temperature" requirement for the historic RF.

For the reduced learner require counts >=30 in one preselected stratum.
The original RF requires independent train/test individuals, but no
29-positive-content threshold unless that additional inferential route
is explicitly requested. Keep this difference.

Inspect official public metadata pages only; never fetch GPS/position/
animal-level identifiers, training/holdout outcomes or restricted archives.
Capture evidence URL and quoted publisher-level summary as provenance.

## Baseline candidate snapshot: evidence known before specification

- Dryad 2017 Schlaich et al. Circus pygargus: 29 tagged birds total;
  official usage notes enumerate timestamp/lat/lon/speed columns and do NOT
  list altitude. Two hard barriers for new positive-content test: <=29 birds
  and missing published altitude.
- Three Zenodo Movebank marsh-harrier studies described by Milotic et al.
  2020: H_GRONINGEN 4, MH_WATERLAND 7, MH_ANTWERPEN 3 marsh harriers
  (one separate Antwerp buzzard). Site-specific upper bounds individually
  below 30; do not pool without an external crosswalk.
- Dryad Schaub et al. 2026: six species/280 overall, but counts are publisher
  totals, not an admitted independent calibration/test roster. Original RF
  feature external temperature absent and rounded longitude; schema of
  original archived RF incompatible; reduced learner remains HOLD pending
  independent canonical crosswalk, source version/permissions and per-stratum
  eligibility.
- Swiss 2024 NestTool: 697 year episodes/258 red kite IDs, no overlap
  with original four BOP taxa; historical source HR/nest outcomes already
  accessed, so not an unopened external altitude-state test.
- German Movebank metadata study 294443150: official access returned an
  unspecified HTTPError in previously frozen #292; no invented permission
  status or source counts.

These are bounded examples, not an exhaustive source discovery survey.
Every source snapshot must distinguish "absent in stated published file
schema" from "we did not retrieve and inspect private raw data."

## Tests and integration

- Missing field vs unknown field, no mixed-species pooling, 29 vs 30
  individuals, per-species target selection, required extra validation animal.
- Original RF needs external temperature; reduced learner does not.
- Privileged/no-consent source stays HOLD even if other fields pass.
- Unknown original-vs-new identity remains HOLD despite distinct names.
- No candidate is automatically set as real-data ADMITTED after metadata.
- Unknown/extra keys and non-HTTPS provenance rejected.
- Deterministic output; no animal keys, locations, trajectories, raw rows,
  observed altitudes or outcomes in publicly emitted summary.
- Existing historic BOP mixed, Dryad NOT_ADMITTED and red-kite HOLD unchanged.
- No auto-download, R refit or source GPS process in CI.
