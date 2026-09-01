# Chapter 2 roadmap — multidimensional niche geometry

Program ID: `niche-to-survey-four-chapter-v1`

## Terminal scientific goal

Demonstrate, with known truth and then independent empirical evidence, that a flat x-y niche representation can discard biologically meaningful state-space structure, and provide auditable quantities for the amount and source of that loss.

A successful Chapter 2 should answer three levels of question:

1. **Thickness:** how many effective z/t/structural states remain after x-y location is known?
2. **Projection loss:** how much apparent niche overlap is created by marginalizing those axes?
3. **Habitat complexity:** does ecological state-space thickness differ systematically among habitat structures, with layered systems such as forests predicted to carry more vertical state capacity than simpler planar systems under comparable observation semantics?

## Gate A — mathematical core

Status: **implemented and tested**.

Required quantities:

- `H(Z|XY)`, `H(T|XY)`, `H(Z,T|XY)`;
- effective conditional states `exp(H(...))`;
- full added-axis information beyond x-y;
- z–t conditional dependence diagnostic;
- pairwise Schoener overlap before/after projection;
- planar, vertical, temporal and joint-only overlap inflation.

All functions remain model-agnostic, accept explicit unavailable masks, and fail closed on invalid support.

## Gate B — known-truth projection benchmark

Status: **B1 analytic truth fixtures implemented; B2 concealed-estimator recovery pending**.

### B1 — analytic truth fixtures

`odsp.synthetic_benchmark` now fixes and checks these generating families:

- planar sufficiency;
- pure vertical thickness;
- pure temporal thickness;
- independent z×t thickness;
- coupled z×t support;
- vertically partitioned taxa with identical x-y marginals;
- temporally partitioned taxa with identical x-y marginals;
- joint-only z×t partition where x-y, z and t marginals alone are identical;
- simple versus layered habitat capacity with horizontal footprint held fixed.

The analytic fixtures verify exact effective-state counts and expected projection-overlap inflation before empirical development.

### B2 — concealed-estimator recovery

Next, generate occurrence/observation samples from the fixed truth tensors, hide the generating tensor from the estimator, reconstruct support from the allowed training information, and open truth only for final scoring.

Primary checks:

- recover the correct effective conditional state counts within predeclared tolerance;
- recover the correct ranking of projection loss;
- distinguish marginal from joint-only hidden structure;
- retain abstention under missing/structurally non-identifiable axes;
- do not improve results by post-outcome bin or estimator tuning.

## Gate C — source/effort layer

Status: **time ingestion implemented; vertical layer pending**.

Current source-preserving time ingestion supports GBIF and iNaturalist without substituting upload timestamps for observation time.

Next vertical/depth input contract must preserve, when genuinely measured:

- vertical stratum / canopy layer / height / depth;
- measurement unit and reference surface;
- sensor vertical coverage or detection cone;
- precision/uncertainty;
- effort/downtime relevant to the stratum.

No height/depth may be fabricated from land-cover class alone.

## Gate D — independent empirical demonstration

Status: **not started**.

Candidate systems should have defensible observation effort across the added axis. Strong source classes include telemetry with depth/altitude, vertically stratified cameras/acoustics, canopy surveys, depth loggers, or similarly explicit effort designs.

The first empirical target should test whether an x-y projection materially inflates overlap or suppresses state-space thickness relative to the measured axis-resolved representation.

## Gate E — habitat-complexity synthesis

Status: **future**.

Predeclare habitat structural classes and compare thickness only after harmonizing state definitions and observation coverage. A forest-versus-grassland contrast is a motivating hypothesis, not a result to assume in advance.

## Hard boundaries

- Do not alter or reopen SDMR Product A.
- Do not revive ODSP's retired spatial topology/reachability methods; those belong to EOG.
- Do not infer fundamental niche, causal coexistence, competition or predation from thickness/overlap alone.
- Do not treat opportunistic occurrence count as unbiased use probability without an observation model or defensible weighting.
- Do not tune z/t bins after seeing the biological outcome in confirmatory work.
