# Snapshot USA 2024: deployment-only structural source screen v0

**Status: metadata-stage research only; no empirical ODSP endpoint is
registered.** This separate branch does not rerun or reinterpret the closed
Serengeti, BOP_RODENT, bat or Tawaki endpoints, and does not modify the
frozen shared-validation e-IUT statistical candidate in PR #217.

## Why this source, and what has been exposed?

Snapshot USA 2024 was released on Dryad on 2026-06-01:
https://datadryad.org/dataset/doi:10.5061/dryad.bnzs7h4qf

The public data description reports 3,127 deployment records at 2,715
distinct camera locations within 184 arrays in 49 states, and 377,427
sequence-data records. It describes separate files for deployment metadata
(~686 KB) and detection sequences (~73 MB).

The page and schema, including summary-level counts, were viewed before
the current design freeze. No actual 2024 deployment CSV row values or
species-identified detection/sequence rows were read by this effort before
the v0 contract was committed. Historical complete non-access is not
attested; prior publication of the source is disclosed.

The **v0 structural contract** in
ODSP_SNAPSHOT_USA_2024_DEPLOYMENT_SCREEN_V0_CONTRACT.json
was written before this run's deployment-content access. The runner
accepts only the frozen URL for ssusa_2024_deployments.csv. It does not
even provide a route to open ssusa_2024_sequences.csv.

## Frozen primary structural screen

With no animal detections or observation times:

- Define a physical site using the composite
  (Project, Camera_Trap_Array, Site_Name), never Deployment_ID or image ID.
- Group A is Habitat text containing forest (case insensitive);
  Group B contains grassland. Unassigned/ambiguous habitats cannot rescue
  the groups.
- A qualifying site needs at least 30 Survey_Nights from a SINGLE
  deployment. Multiple deployments at a site are not summed because
  deployment intervals could overlap.
- At least 8 distinct eligible sites AND at least 8 camera arrays
  per group are required for a positive STRUCTURAL count screen.
- Sites with conflicting rounded coordinates or state descriptions are
  excluded from primary eligibility. Each site is counted once.
- Secondary only: exclude sites flagged in deployment Feature_Type with
  trail, road, water, bait, feeder or salt text. This secondary result
  cannot override the frozen primary group rule.
- Metadata bytes and contract are SHA-256 hashed; only aggregate counts
  are emitted. Precise camera coordinates, deployment names and site IDs
  are never copied into the receipt.

If these tests pass, the ONLY output is
STRUCTURAL_COUNTS_ONLY_UNVERIFIED_INDEPENDENCE. The group and array counts
are not exchangeability or sampling-design tests. A positive status is
not permission to analyze old public species/time outcomes as confirmatory.

## Why 2,715 locations is not 2,715 independent validation blocks

Within an array the survey protocol places cameras approximately 200 m
to 5 km apart; they share habitat, observers, deployments, and potentially
animal movements and weather. Individual cameras do not necessarily
represent independent site draws. Arrays themselves were recruited by
collaborators, with nonuniform geographic and habitat representation.

The public data description says 73 of the 184 arrays contributed an
additional camera-calibration / density-estimation component, where
contributors were *asked* to select representative sites. This does
NOT mean the other arrays are random, or that every density array
achieved truly random sampling. The full sampling mechanism would
need separate study documentation and an analysis of spatial
correlation within and between arrays.

Thus even if both groups pass the minimum 8-array count, the assumptions
of independent identically distributed validation blocks demanded by
the experimental e-value method are NOT verified. A conservative
array-as-block analysis may have far fewer independent units than
the site count. Even arrays need not be iid across the U.S.

The source also publishes Survey_Nights as an observed effort summary.
It is not a guaranteed prospective randomization variable or proof of
uniform detection effort by local clock hour. The future 6-bin
detected-time target would require verified timestamp semantics and
true operating-hour denominators *after* freeze, and could still be
biased by occupancy/detection.

## What the source can and cannot answer

At the structural stage the answerable question is narrowly:

> Within the frozen forest and grassland filters, how many distinct
> physical sites and arrays have nonempty deployment effort metadata?

It cannot yet answer the interesting ecological Chapter-2 question:

> For a model trained without those validation sites, does adding
> species and then habitat/season information reliably improve the
> full detected-time state distribution at new camera sites, including
> uncertainty over the model training process?

For that substantive question, the new three-level probability models
must be frozen, trained and generated independently from the entire
separately defined training frame. Proper normalized multiclass Brier
scores supply two bounded contrasts. The original sampling scheme,
validation site identity, year-by-year source-overlap exclusions and
time-zone/effort rules must be fixed before any response-bearing
sequence records are opened.

If the validation score improvement is small, the pre-frozen synthetic
power screen in PR #217 demonstrates that a mathematically valid method
can have essentially zero certification power at 12 blocks per group.
A structural count pass must never be advertised as scientific power.

## Separation of stages

A — **Public source/schema discovery** (done from source summary):
aggregate descriptions and field definitions; no local response records.

B — **Outcome-record-free structural metadata screen** (this branch):
download only deployments and report aggregate site/array/effort counts,
or SOURCE_METADATA_UNAVAILABLE if download fails. Results contain no
per-camera response or time labels.

C — **Sampling-theory admissibility** (NOT DONE):
physically and statistically independent validation-block design,
source-frame exclusion, provenance and time-zone/effort proof. This
cannot be certified by the metadata count alone.

D — **Prospectively frozen new prediction endpoint** (NOT DONE):
managed model-to-score generation and immutable untouched observation
outcomes, a predeclared known-power route and appropriately controlled
uncertainty. Closed ecological endpoints are never reclassified.

Any failure at B/C terminates the proposed primary route for this
source as designed; new scientific questions require new versions,
not changing group choice or data after outcome inspection.
