# External BOP state-prediction feasibility: Schaub 2026 Dryad source gate

## Main answer before opening biological outcomes

The closed BOP_RODENT v3 primary Random Forest used external temperature,
unrounded GPS latitude and longitude, cyclic local solar hour and day-of-year,
plus species identity to predict four classes of **raw GPS altitude above MSL**.
The new Schaub et al. (2026) Dryad candidate has a large original
GPS-tracking dataset, but **documented Data_1a predictors are not directly
compatible with this already-frozen RF**. No feature substitution,
imputation or "external validation" reclassification is permitted after
seeing the old or new RF results.

This is a new source-only preflight, **not** a prospective external
BOP transfer prediction. It extends, but never reopens, the closed
BOP-v3-to-v2026 same-study identity gate (10 new IDs in four taxa,
maximum 6 within one taxon, 90%-rank gate unavailable).

## Pinned source and verification boundary

The external candidate is the officially published Dryad dataset:

- Schaub et al. (2026), *Evaluating the sensitivity of raptors to
  wind turbine collisions: an integrative approach based on GPS tracking*.
- DOI https://doi.org/10.5061/dryad.n8pk0p398
- Public release date: 17 August 2026.
- Six reported taxa, 280 tagged individuals, 15 study areas.
- Four BOP taxa in the **whole dataset README**: C. pygargus 101,
  C. cyaneus 54, C. aeruginosus 31, and B. buteo 31 = **217**.
- The 271 individuals in Data_1a (3,302,242 GPS fixes) and 162 in
  Data_2a (7,013,897 high-frequency in-flight fixes) are not
  independently validated BOP-like calibration/validation individuals.
  No biological denominators may be inferred from number of GPS fixes.

The following files are deliberately **not opened**:
Data_1a.csv (about 888 MB) and Data_2a.csv (about 2.16 GB).
No altitude, GPS timestamps, row-level coordinates, animal IDs,
individual tracking steps or altitude distributions are read in the
preflight.

The only authorized network access is:
1. the two public Dryad dataset/versions metadata API JSON endpoints
   for the specified DOI, limited to 128 KiB each;
2. exactly three small, official provider, non-GPS files from
   already identified native file IDs (README.md,
   Study_areas_bounding_boxes.csv,
   Complete_succesful_breeding_seasons.csv).

All URLs are fixed in a source-only contract committed **before
running the official download probe**:
research/BOP_DRYAD_EXTERNAL_SCHEMA_PREFLIGHT_V1_CONTRACT.json.

Redirects to unpinned hosts, HTTP 403, oversized data, schema mismatch,
and unavailable files produce explicit **SOURCE_HOLD** statuses.
No mirror or alternative source is silently substituted, and no raw
study area names, individual IDs, bounding box coordinates or source
content are redistributed. Metadata fingerprints and aggregate counts
can be retained. A small table of complete successful breeding
seasons is **not** the entire roster of tagged individuals.

## Predictor and target compatibility

| Frozen original BOP input | Dryad Data_1a README variable | Result |
|---|---|---|
| timestamp | timestamp (UTC) | documented input |
| location-long / location-lat | location.long.rnd / location.lat.rnd | 0.1-degree-rounded spatial features, *not equivalent precision* |
| external-temperature | **not documented** | **REQUIRED ORIGINAL RF PREDICTOR MISSING** |
| height-above-msl | height.above.msl | raw AMSL target field documented; values not opened |
| individual-local-identifier | individual.global.identifier | namespace crosswalk unknown; cannot assert same or distinct biological animals |
| individual-taxon-canonical-name | individual.taxon.canonical.name | documented taxon |

Data_2a has a corrected altitude MSL field and consists of
selected **in-flight** locations. It is a changed observation process
and target-support distribution, not interchangeable with the
original BOP endpoint or Data_1a.

The current **direct-original-RF verdict** is:
\`ORIGINAL_RF_PREDICTOR_INCOMPATIBLE\`.

This verdict is based exclusively on **published schema and the
unchanged original model contract**, not raw GPS header measurement.
The feature gate does not claim a biological null, identify causation,
assess the independence of the external candidate, or alter the
original \`empirical_state_prediction_mixed\` terminal.

## Official-source probe and next-stage gate

The script
\`scripts/bop_dryad_external_schema_preflight_v1.py\`
checks the feature crosswalk against
\`BOP_RODENT_STATE_PREDICTION_CONTRACT.json\`, attempts only
the allowlisted official metadata/sidecar resources, and produces an
aggregated, source-only JSON report with each check's source SHA256
(if accessible) or explicit hold code.

\`\`\`bash
python -m pytest tests/test_bop_dryad_external_schema_preflight_v1.py
python scripts/bop_dryad_external_schema_preflight_v1.py \
  --out /tmp/bop-dryad-external-source-only.json
\`\`\`

A later **distinct, prospectively frozen ecological-state prediction**
could use a new common-feature learner, but only after resolving
licensing, individual identity/study-area overlap, source version,
Data_1a eligibility and coordinate precision. Its training population,
predictor, altitude target, baseline, individual-group roster,
exchangeability assumptions and model-to-score execution must be
frozen **before opening GPS outcomes**. A positive cross-validation
result in the historic BOP archive cannot serve as an untouched
external calibration group for the new candidate.

The current scientific status remains
\`EXTERNAL_METADATA_CANDIDATE_NOT_ADMITTED\` until those conditions
are satisfied. Neither a successful Dryad metadata API response nor
a successful CI test means the biological dataset is admitted.
