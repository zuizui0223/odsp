# Chapter 2 roadmap — multidimensional niche geometry

Program ID: `niche-to-survey-four-chapter-v1`

Spine: **N2 — HOW THICK is it? / 地図は、niche を薄くする。**

## Scientific goal

Chapter N2 asks what is lost when ecological state is projected onto a flat x-y map. The core representation is an axis-resolved support state such as `S(x,y,z,t,...)`, with explicit observation semantics for every added axis.

The chapter now distinguishes two questions that must not be conflated:

1. **Thickness magnitude** — how much added-axis information remains after x-y location is known, e.g. `H(Z|X,Y)` and `exp(H(Z|X,Y))`.
2. **Thickness organization / transferability** — whether the location-conditioned added-axis distribution is stable enough to predict independently held-out individuals or observations better than a lower-information marginal representation.

A fitted support can be descriptively thick while its detailed x-y-resolved organization fails to generalize.

## Gate A — mathematical core

Status: **implemented and tested**.

Main quantities include:

- `H(Z|X,Y)`, `H(T|X,Y)`, `H(Z,T|X,Y)`;
- effective conditional states `exp(H(...))`;
- `I(Z;T|X,Y)` as conditional dependence, not a causal interaction;
- per-cell `axis_thickness_map`;
- full-versus-projected overlap and projection-loss diagnostics.

The implementation is model-agnostic and fails closed on invalid or unavailable state support.

## Gate B — known-truth recovery

Status: **implemented and tested**.

Analytic fixtures and concealed finite-observation recovery cover:

- planar sufficiency;
- pure vertical and temporal thickness;
- independent and coupled z×t structure;
- vertical, temporal and joint-only partition hidden by x-y projection;
- simple versus layered structural state-space capacity.

Known-truth recovery remains methodological evidence. It does not license treating opportunistic occurrence counts as unbiased organism-use probabilities.

## Gate C — source and observation semantics

Status: **implemented**.

`odsp.temporal_information` preserves observation time, precision and time-zone semantics without substituting upload time. `odsp.vertical_information` requires an explicit vertical meaning and distinguishes organism z from locality elevation, bathymetry, sensor placement and other contextual fields.

For empirical N2 work, x-y and the added biological/structural axis must be jointly observed or linked under a prospectively defensible observation architecture.

## Gate D — empirical axis-resolved validation

Status: **two prospectively bounded lanes completed; neither authorizes Gate E**.

### D1 — Tawaki GPS + dive data

Terminal category: **`empirical_gate_d_unavailable`**.

The pre-outcome Tawaki contract froze organism-z semantics, a 5 km primary grid, depth bins, whole-bird split and full structural denominator. The structural preflight then failed the frozen full site×year coverage rule because Harrison Cove 2019 and 2020 had zero estimable primary cells. No `H(Z|X,Y)`, thickness map or sealed biological score was opened.

This is a valid empirical-unavailability result, not a null biological result. No grid/bin/dataset rescue is authorized.

### D2 — European free-tailed bat native 3D tracking

Terminal category: **`empirical_n2_thickness_not_generalizing`**.

The v2 programme first froze an architecture-only candidate universe. The European free-tailed bat (`Tadarida teniotis`) Movebank archive was selected before N2 outcomes because x-y, timestamp and native GPS height occur on the same event stream, effort is approximately regular, raw/outlier-marked fixes are retained, and the source is public and version-pinnable.

Frozen boundaries:

- structural-preflight merge: `be5a86e850b99457d1e6055289c2990fb8ca358f`;
- thickness-contract merge: `8250331209cbabf85afdcf92672104e8543816c7`;
- outcome-engine merge: `e99022ffe7a904d3f9917d9315d85ba4cdc91d5c`;
- one-shot terminal workflow: run `33481773409`;
- terminal decision receipt: `N2_BAT_THICKNESS_TERMINAL_DECISION.json`.

Primary frozen representation:

- native z: `height_above_msl`; no AGL/DEM conversion;
- x-y: EPSG:3035, 5 km;
- 18 model-pool structurally eligible cells;
- fixed z bins `[-inf,0,50,100,200,400,800,1600,3200,inf]` m;
- 6 model bats / 2 sealed bats;
- individual-equal conditional and marginal z distributions with Jeffreys smoothing.

Numeric QC passed at 10,335 / 10,335 finite heights.

Descriptive model-pool thickness:

- `H(Z|X,Y) = 1.3918623004770097` nats;
- `exp(H) = 4.022333876564191` effective vertical states.

Independent sealed answer check:

- Bat5 mean `log P_model(z|x,y) - log P_model(z)` = `-0.43541033813280833`;
- Bat7 = `-0.021938657402345435`;
- equal-individual mean = `-0.22867449776757687`.

Both sealed gains were <=0, so the frozen answer-check category is `estimable_but_non_generalizing` and the terminal category is `empirical_n2_thickness_not_generalizing`.

The correct interpretation is:

> The model-pool support is descriptively vertically thick, but its detailed x-y-conditioned vertical geometry did not transfer to either independently sealed individual better than the model-pool marginal vertical distribution.

Do **not** convert this into either "there is no z niche" or "the 3D niche was validated".

Frozen 2.5 km, 10 km, fine-bin and coarse-bin sensitivities were also non-generalizing with both sealed gains negative. The source-marked-outlier exclusion sensitivity was not evaluable because it could not retain the frozen 18-cell support denominator. Sensitivities cannot override the primary result.

## Gate E — habitat-complexity synthesis

Status: **not authorized / blocked under the current empirical chain**.

The motivating hypothesis remains scientifically interesting:

> Equal horizontal area can contain unequal ecological state-space capacity; a vertically layered forest may contain more distinguishable within-cell states than a structurally simple open habitat under harmonized state definitions and observation semantics.

However, neither completed Gate-D lane provides the prospective empirical validation required to promote this contrast as the next confirmatory endpoint:

- Tawaki was structurally unavailable;
- the bat lane was structurally evaluable but its x-y-resolved vertical organization did not generalize across individuals.

Therefore the forest-versus-grassland hypothesis is **not** tested, supported or rejected here. Pursuing it would require a separately frozen scientific programme with its own measurement architecture and validation logic; it cannot be used to rescue the completed bat endpoint.

## Current Chapter-N2 evidence spine

```text
known-truth thickness/projection recovery       supported
                ↓
source/axis semantics                           implemented
                ↓
Tawaki first empirical lane                     unavailable
                ↓
native x-y-z architecture gate                  implemented
                ↓
Bat structural feasibility                      supported
                ↓
Bat descriptive thickness magnitude             present (~4.02 effective states)
                ↓
Bat independent thickness organization          not generalizing
                ↓
Gate E habitat-complexity promotion              blocked
```

## Hard boundaries

- Do not alter or reopen SDMR Product A.
- Do not revive retired ODSP spatial topology/reachability; that belongs to EOG.
- Do not infer fundamental niche, causal coexistence, competition or predation from thickness alone.
- Do not equate native altitude above mean sea level with height above ground.
- Do not tune z/t bins, spatial grain, individual denominator or candidate dataset after empirical outcome access.
- Do not rerun or rescue the completed Tawaki or bat empirical endpoints.
- Do not promote Gate E from descriptive model-pool thickness alone.
