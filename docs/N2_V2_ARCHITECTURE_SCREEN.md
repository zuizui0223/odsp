# N2 empirical validation v2 — architecture-only screen

Program: `niche-to-survey-four-chapter-v1`  
Chapter: **N2 / ODSP — HOW THICK is it?**  
Spine: **地図は、niche を薄くする。**

This screen is a new empirical programme after the closed Tawaki lane. The Tawaki terminal category remains `empirical_gate_d_unavailable`; none of its grid, bin or eligibility choices are changed here.

## What may be inspected

Only source architecture and reproducibility are admissible for this selection:

- whether x-y and the added organism/structural axis are attached to the same observation event;
- whether the added axis is biological/structural rather than a contextual proxy;
- sampling schedule and effort semantics;
- cluster identifiers;
- source precision and coordinate disclosure;
- public/versioned availability;
- whether structural support can be audited without reading the added-axis distribution.

Do **not** use z/t effect size, ODSP thickness, projection loss, biological group differences, or held-out scores to choose the dataset.

## Frozen candidate universe

### Antarctic petrel — Movebank DOI `10.5441/001/1.q206rm6b`

Architecture strengths: public versioned archive; same-event GPS position and altitude; clusterable repeated trips. Architecture limitation: the archived dataset is composed of selected departure/return commuting sections rather than the most complete native event stream.

### European free-tailed bat — Movebank DOI `10.5441/001/1.52nn82r9`

Architecture strengths: public versioned archive; GPS latitude, longitude and height recorded on the same event stream; approximately 30 s schedule; source documentation states that the archive retains all data including fixes treated as outliers by the source analysis. This is the strongest architecture-only candidate in the frozen universe.

### Two-banded plover — Zenodo DOI `10.5281/zenodo.20748797`

Architecture strength: each public flight row contains timestamp, x-y, height above ground and vertical uncertainty. Architecture failures for the N2 v2 primary lane: the public repository contains only the final 237-flight analysis table, not raw GPS or the upstream cleaning/filter denominator, and latitude/longitude are rounded to two decimal places. It therefore cannot support the required source-precision/effort structural preflight.

## Deterministic selection

The machine-readable screen and selection manifests are:

- `N2_V2_ARCHITECTURE_SCREEN.json`
- `N2_V2_ARCHITECTURE_SELECTION.json`

Among architecture-admitted candidates, selection uses a frozen lexicographic source-only priority vector:

1. complete or near-complete native event stream;
2. same-event x-y-axis measurement;
3. regular/reconstructable effort schedule;
4. source-precision spatial coordinates;
5. raw/outlier flags retained;
6. candidate ID only as a final tie-break.

The selected lane is:

> **European free-tailed bat (`Tadarida teniotis`), Movebank Data Repository DOI `10.5441/001/1.52nn82r9`.**

This does not mean that the bat data are expected to yield a favourable ODSP thickness result. Source papers are not outcome-blind to their own biological questions, so that non-blindness must remain disclosed. The selection claim is narrower: among the frozen candidate architectures, this dataset best satisfies the pre-outcome measurement and reproducibility requirements.

## Next boundary

Before downloading/reading altitude distributions, freeze a bat-specific structural preflight covering:

- archive/file identity;
- schema only;
- event/individual/night denominators;
- timestamp interval/effort structure without altitude values;
- finite x-y and native altitude availability counts without altitude frequencies;
- whole-individual model/sealed split;
- predeclared x-y grid support counts that do not use z values.

Only if that structural preflight passes may a separate empirical N2 contract define the altitude reference, z bins/support estimator, spatial grain, thickness estimand and held-out answer-check. No result-dependent replacement of the selected dataset is allowed within this lane.
