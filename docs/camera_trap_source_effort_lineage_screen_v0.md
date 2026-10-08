# New ecological source discovery after detecting photo-derived metadata dates

Status: **public protocol/documentation screen only**. No deployment or animal
detection rows from these sources were read, and no source is yet
eligible for ODSP primary future-refit success-probability inference.

The source-independent validation design must identify the ORIGINAL
metadata-generating mechanism. A file labelled deployment.csv or
start_date/end_date does not demonstrate independence from photo-derived
outcome records; Snapshot USA 2024 is a documented counterexample.

## Potentially useful public source families

### Rhode Island wildlife camera-trap survey 2018–2023

- Data paper: Mayer et al. (2025), Ecology 106:e70094,
  DOI 10.1002/ecy.70094.
- Zenodo archived version: https://zenodo.org/records/14508932
- Published 249 survey sites across 12 seasonal survey periods, with
  separate deployment and detection CSV files; deployment file describes
  camera operation dates, and detection file includes species and
  detection timestamps.
- **Advantages:** repeated seasonal design, named primary physical
  sites/camera IDs, and explicitly separate operations metadata.
- **Unresolved:** source logs may be corrected from photos, not independently
  timestamped; camera-site selections originally targeted bobcats and
  fishers in suitable forest habitats; two regional sections and
  repeated years produce dependent clusters. 249 site names over many
  seasons are not 249 *iid within each validation group*.
- **Status:** METHODS_PROVENANCE_PENDING. Screening the article is not
  a license to open response timestamps before a new source plan.

### TEAM tropical-forest camera-trap network

- Global protocol described in
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3140736/.
- Around 60 systematically spaced cameras over >=120 square kilometres
  for >=30 days at each tropical-forest location, often deployed in
  sequential batches.
- **Advantages:** documented regular spatial sampling grid, fixed dry-season
  timing, potential repeated ecological states.
- **Unresolved:** within-network camera points are spatially clustered,
  and shared site conditions are not independent; the primary ecological
  sampling unit may be the protected-area location, not every camera
  grid cell. Authentic original operation logs and corrections must be
  inspected separately from image times.
- **Status:** METHODS_PROVENANCE_PENDING.

### Snapshot Japan 2023

- Article: https://pmc.ncbi.nlm.nih.gov/articles/PMC11926606/
- Protocol: https://www.nies.go.jp/biology/snapshot_japan/en/protocol.html
- Published 90 camera deployments with separate date fields.
- The official protocol explicitly requests camera-operator photographs
  on deployment/retrieval to determine start/end dates, and indicates
  that the last available image may substitute for the retrieval photo.
- **Advantage:** field operator photos could distinguish operator actions
  from wildlife detections if original unmodified logs are available.
- **Limitation:** photo-dependent date construction is not automatically
  independent of the wildlife observation process; physical site-level
  independence and small-effect power also remain unresolved.
- **Status:** DO_NOT_AUTOMATICALLY_ADMIT.

### Public South Korean year-long ungulate camera-trap study (2026)

- Public methods and DOI context:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC13379711/
- Authors report 82 camera stations in two study-site groups and a
  distinct camera-operation log with start/end and recorded downtime.
- **Advantage:** the stated presence of explicit downtime intervals
  is better suited to validating active camera effort than inferring
  uptime from first/last animal photographs.
- **Limitation:** no proof has been obtained that the log is original
  and unmodified by detection outcomes. Two clustered regions with
  82 stations also do not imply hundreds of iid validation blocks.
- **Status:** METHODS_PROVENANCE_PENDING.

## Decision for ODSP

For a study targeting true success probability p_success>0.8 on EVERY
group/contrast under the experimental bounded e-IUT with a=0.002,
the nonparametric two-point-null theorem in
odsp/weak_gain_nonparametric_barrier_v1.py gives a sharp necessity:
at least **128 iid validation blocks per group** are required for a
nonrandomized distribution-free test even to reject the ideal constant
positive +0.05 gain point alternative. Real noisy gains require a
separately justified, often larger design.

This is a conditional **design barrier**, not an estimate of any
archive's ecological information gain. It should be used to stop
low-power route proliferation, not to declare that temporal/vertical
ecological structure is absent.

The nearer-term scientific use of properly screened published data is
a site/individual-clustered **mean predictive gain** or temporal/vertical
organization question, with frozen comparators and explicitly limited
population claims. ODSP already has qualified process-mean route(s);
there is no scientific requirement that every ecological state-space
result also demonstrate near-certain success of a future model refit.

New source access requires a NEW preregistered study identity,
physical-unit sampling roster, independent effort lineage, exclusion
of overlapping original source units, and untouched response scoring.
Do not reuse already-closed Serengeti, BOP_RODENT, Tadarida or Tawaki
terminal observations as if they were new external validation.
