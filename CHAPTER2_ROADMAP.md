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

Status: **B1 analytic truth fixtures and B2 concealed finite-observation recovery implemented and tested**.

### B1 — analytic truth fixtures

`odsp.synthetic_benchmark` fixes and checks these generating families:

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

### B2 — concealed finite-observation recovery

`odsp.concealed_recovery` samples finite observation-count tensors from the fixed generating supports, gives only those sampled counts to the estimator, and opens the generating tensor only for final truth scoring.

Frozen development settings:

- sample size: `100000` observations per synthetic support;
- RNG seed: `2026090102` plus deterministic family offsets;
- effective-state absolute tolerance: `0.08`;
- overlap/projection-loss absolute tolerance: `0.03`.

The benchmark covers thickness recovery, vertical/temporal/joint projection loss, and the ordering of simple versus layered habitat capacity. The current implementation passes the frozen checks across Python 3.10–3.13.

This is synthetic recovery evidence only. It does not license interpreting raw opportunistic occurrence counts as unbiased use probabilities.

## Gate C — source/effort layer

Status: **generic time/vertical schemas implemented; first source-specific empirical binding designed under Gate D**.

### Time

`odsp.temporal_information` preserves GBIF/iNaturalist observation dates/times, source precision, UTC/time-zone information when supplied, and quality flags. Upload/update timestamps are never substituted for observation time.

### Vertical/depth

`odsp.vertical_information` requires callers to declare the semantic meaning of a vertical field. Supported declared kinds include organism height, organism depth, canopy stratum, sensor height/depth, locality elevation and another explicitly declared vertical axis.

The schema preserves:

- point, interval or categorical vertical information;
- unit and reference surface;
- uncertainty;
- sensor vertical coverage when supplied;
- raw source fields and quality flags.

Important fail-closed distinctions:

- GBIF locality elevation is preserved as contextual geography but explicitly **not** treated as within-cell niche-z;
- sensor height/depth is observation geometry and is **not** silently treated as organism z;
- numeric biological z without units is not considered usable;
- reversed intervals and missing semantics fail closed;
- no height/depth is fabricated from land-cover class alone.

## Gate D — independent empirical demonstration

Status: **first dataset screened and pre-outcome contract implemented; ODSP outcome not yet opened**.

The first admitted system is Fiordland penguin / tawaki (`Eudyptes pachyrhynchus`) GPS+dive-logger data from Piopiotahi / Milford Sound, 2019–2020. The selection rationale and rejected/reserved alternatives are frozen in `GATE_D_DATASET_SCREEN.md`.

The prospective ODSP rules are frozen in `GATE_D_TAWAKI_CONTRACT.json` and `odsp.gate_d_contract` before any Gate-D thickness result is calculated. Primary design choices include:

- organism-z = qualifying dive maximum depth, not bathymetry/locality elevation;
- source threshold `>=0.5 m` and `>=5 s` retained;
- powers-of-two z bins from 0.5 m, not empirical quantiles;
- primary 5 km NZTM2000 x-y grid, with 2.5/10 km sensitivity unable to replace primary;
- equal total weight per bird-trip;
- whole-bird 25% sealed split within site × year using a deterministic SHA-256 ranking;
- explicit cell estimability gates;
- unlocated dives remain in the effort denominator and are never treated as absence or assigned a fabricated x-y location;
- primary inference is therefore about **location-resolved dive-depth state support**;
- held-out answer check uses sealed birds only after the frozen model-pool representation exists.

The source paper is already published and reports related foraging/depth patterns. Gate D is therefore not described as source-paper-blind. What is prospective is the ODSP estimand, grid, bins, weighting, eligibility, uncertainty and held-out decision machinery.

No `H(Z|X,Y)`, local thickness map, projection-loss result, colony/year ODSP contrast or held-out Gate-D decision may be computed until this contract is merged on `main`.

## Gate E — habitat-complexity synthesis

Status: **future; blocked on a valid Gate-D empirical read**.

Predeclare habitat structural classes and compare thickness only after harmonizing state definitions and observation coverage. A forest-versus-grassland contrast is a motivating hypothesis, not a result to assume in advance.

## Hard boundaries

- Do not alter or reopen SDMR Product A.
- Do not revive ODSP's retired spatial topology/reachability methods; those belong to EOG.
- Do not infer fundamental niche, causal coexistence, competition or predation from thickness/overlap alone.
- Do not treat opportunistic occurrence count as unbiased use probability without an observation model or defensible weighting.
- Do not tune z/t bins after seeing the biological outcome in confirmatory work.
