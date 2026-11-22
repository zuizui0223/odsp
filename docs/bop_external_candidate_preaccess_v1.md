# External BOP source-candidate intake: public metadata screen v1

**Status:** retrospective publisher-metadata triage, not biological validation.
The current screen is frozen in
[research/BOP_EXTERNAL_SOURCE_CANDIDATE_METADATA_V1.json]
(../research/BOP_EXTERNAL_SOURCE_CANDIDATE_METADATA_V1.json).
The original BOP 2023 mixed outcome, 2026 v3/v2026 identity count HOLD,
Swiss retrospective model outcomes, and Dryad direct-RF NOT_ADMITTED remain
unaltered.

## First decision: can a candidate even be inspected for this purpose?

The empirical BOP question asks if the **same frozen predictor and
reference**, or an explicitly **different common-input learner**, can
predict individual altitude-state information beyond a less informative
reference in genuinely held-out individuals. Training/target animal
identity, altitude reference, temporal and coordinate semantics, predictor
availability and the number of *distinct animals per species* are nonoptional.

The additional #303 positive-population-content test requires a stronger
numerical and statistical contract than the 90%-marginal single-animal rank
bound: **29 calibration animals all positive plus a separate validation
animal** for 90% content/95% confidence in one prespecified stratum.
Even 30 names cannot certify that 30 biologically distinct, IID-eligible
animals with usable altitude and source provenance exist.

The metadata-only screen in odsp/external_source_candidate_gate.py
distinguishes three outputs:

- **KNOWN_INCOMPATIBLE:** explicit incompatible schema or a published
  animal-count upper bound below the necessary target-stratum roster.
- **HOLD_METADATA_OR_PERMISSION:** important unknowns including
  individual identity, access/permission, exact variable semantics, or
  whether an actual versioned dataset is available.
- **ELIGIBLE_FOR_SOURCE_ONLY_PREFLIGHT:** all *declared* metadata
  prerequisites pass, allowing a **separately frozen source-only audit**.
  This is emphatically **not** a permitted download, empirical model
  validation, accepted individual sample, or proof of IID gains.

Historical RF and the reduced-input learner are separate routes. The RF
requires original external temperature and sufficient coordinate precision.
The reduced-input learner is allowed to use the 0.1-degree mean-solar-clock
projection, but its model is **not** the original BOP RF, so any validation
needs a new prospectively frozen source/model/identity chain.

## Seven checked public-source candidates

| Published candidate (pinned version) | Publisher count in target BOP species | New reduced-input 90% content route | Original RF direct rank route | Why |
|---|---:|---|---|---|
| [Schlaich et al. Dryad 2017](https://datadryad.org/dataset/doi:10.5061/dryad.84jk0) | *Circus pygargus* 29 | **KNOWN_INCOMPATIBLE** | **KNOWN_INCOMPATIBLE** | Published tracking-file columns omit height; even a complete 29-individual roster cannot supply 29 calibration + one validation bird |
| [Schaub et al. Dryad 2026](https://datadryad.org/dataset/doi:10.5061/dryad.n8pk0p398) | *C. pygargus* 101; *C. cyaneus* 54; *C. aeruginosus* 31; *B. buteo* 31 | **HOLD_METADATA_OR_PERMISSION** | **KNOWN_INCOMPATIBLE** | Source-species counts are total tagged birds, not eligible independent calibration/test animals; canonical overlap unknown. Historic RF external temperature absent and longitude rounded to 0.1° |
| [MH_WATERLAND Zenodo v7](https://zenodo.org/records/10053583) | *C. aeruginosus* 7 | **KNOWN_INCOMPATIBLE** | **KNOWN_INCOMPATIBLE** | Fewer than 30 birds in this study |
| [H_GRONINGEN Zenodo v5](https://zenodo.org/records/6574736) | *C. aeruginosus* 4 | **KNOWN_INCOMPATIBLE** | **KNOWN_INCOMPATIBLE** | Fewer than 30 birds in this pinned version (newer version not substituted) |
| [MH_ANTWERPEN Zenodo v6](https://zenodo.org/records/10054153) | *C. aeruginosus* 3; *B. buteo* 1 | **KNOWN_INCOMPATIBLE** | **KNOWN_INCOMPATIBLE** | Fewer than 30 in either species, no pooled-stratum rescue |
| [Original Swiss 2024 NestTool archive](https://zenodo.org/records/13736049) | *Milvus milvus* 258; zero published original-four BOP taxa | **KNOWN_INCOMPATIBLE** | **KNOWN_INCOMPATIBLE** | Different species/response endpoint; Swiss source outcomes already retrospectively explored |
| Movebank German study 294443150, as [cited in the 2024 paper](https://www.vogelwarte.ch/en/publications/extracting-reproductive-parameters-from-gps-tracking-data-for-a-nesting-raptor-in-europe/) | *Milvus milvus* only, unknown verified current count | **KNOWN_INCOMPATIBLE** | **KNOWN_INCOMPATIBLE** | Not an original-four BOP target; the previously frozen #292 anonymous metadata request ended in unresolved HTTPError, so access remains HOLD |

**This is a bounded seven-candidate screen, not a claim that no suitable
open source exists worldwide.** In the two routes checked here, no candidate
can be promoted from publisher metadata directly to empirical testing.
The single potentially compatible **new reduced-input** candidate (Dryad
2026) still lacks verified external independent-individual crosswalks and
row-level eligible counts; its source name must not be mistaken for a new,
independent target population.

The 2017 Dryad column list and 29-bird count are explicitly reported in
its official *Usage notes*. The 2026 Dryad source reports 280 tagged birds
across six taxa, but Data_1a contains only 271 individuals in its actual
subsample, and Data_2a only 162 in-flight individuals. These total counts
are not interchangeable with the BOP per-species eligibility count.
The source rounds locations for nest privacy. No undocumented altitude,
temperature, animal count or independent model transfer is inferred.

The European marsh-harrier count descriptions come from the frozen Zenodo
pages and published 2020 dataset description. Although 4+7+3 = 14 across
these three studies, **they cannot be added as a validated independent
population sample**, and even the arithmetic sum remains below 30.

## Reproduction (offline; no download stage)

~~~bash
python -m pytest -q tests/test_external_source_candidate_gate.py
python scripts/audit_bop_external_candidate_snapshot_v1.py
~~~

The script checks exactly seven frozen publisher summaries and two named
routes, returning **14 source-metadata decisions** as JSON to stdout. It
does not accept source downloads, raw tracking rows, animal IDs,
observed outcomes or arbitrary external candidate URLs on its CLI.
No new data are fetched in CI. Source descriptions are not proof that the
publisher fields are currently downloadable or that the biological groups
would be IID if obtained.

A future actual study must pass **a separate prospective source-only
preflight** that confirms the exact versioned file, field/unit/precision
semantics, permission/license, animal identity reconciliation with training,
and true admissible per-stratum calibration/test group counts before any
target labels are opened. That remains undone.

## Public provenance (accessed for source metadata only)

- Schlaich AE et al. (2017) Dryad dataset
  https://doi.org/10.5061/dryad.84jk0 — usage notes and 29-bird count.
- Schaub T et al. (2026) Dryad dataset
  https://doi.org/10.5061/dryad.n8pk0p398 — total and per-species
  counts, Data_1a vs 2a, source longitude rounding.
- INBO Zenodo marsh-harrier datasets:
  https://zenodo.org/records/10053583,
  https://zenodo.org/records/6574736,
  https://zenodo.org/records/10054153.
- Oppel et al. (2024) Swiss red-kite NestTool Zenodo v1:
  https://zenodo.org/records/13736049.
- Existing frozen German Movebank metadata first-error record:
  PR [#292](https://github.com/zuizui0223/odsp/pull/292).

The frozen design was committed **after** these public-metadata observations.
None of these results are prospective hidden-outcome tests or a new
biological finding.
