# Chapter 2 roadmap — multidimensional niche geometry

Program ID: `niche-to-survey-four-chapter-v1`

Spine: **N2 — HOW THICK is it? / 地図は、niche を薄くする。**

## Scientific goal

Chapter N2 asks what is lost when ecological state is projected onto a flat x-y map. The core representation is an axis-resolved support state such as `S(x,y,z,t,...)`, with explicit observation semantics for every added axis.

The chapter distinguishes two questions that must not be conflated:

1. **Thickness magnitude** — how much added-axis information remains after the declared base state is known, e.g. `H(Z|X,Y)` or `H(T|Site)` and `exp(H(...))`.
2. **Thickness organization / transferability** — whether the conditioned added-axis distribution is stable enough to predict independently held-out individuals, sites or observations better than a lower-information marginal representation.

The completed empirical lanes now demonstrate that a support can be thick while detailed organization fails to generalize, and that another added axis can be both thick and independently generalizing.

## Gate A — mathematical core

Status: **implemented and tested**.

Main quantities include:

- `H(Z|X,Y)`, `H(T|X,Y)`, `H(Z,T|X,Y)`;
- effective conditional states `exp(H(...))`;
- `I(Z;T|X,Y)` as conditional dependence, not a causal interaction;
- identity-conditioned partitioning such as `I(C;T|B)`;
- per-cell `axis_thickness_map`;
- full-versus-projected overlap and projection-loss diagnostics;
- `I(A;B)` for in-sample organization between declared base state `B` and added state `A`;
- held-out conditional-versus-marginal log-score gain `E[log P_model(A|B) - log P_model(A)]`;
- conservative independent-group classification: all-positive = generalizing, all-nonpositive = non-generalizing, otherwise mixed;
- cross-fitted grouped scoring when each independent held-out group has its own prospectively defined training model.

The implementation is model-agnostic and fails closed on invalid or unavailable state support. The transferability core does not add hidden smoothing; any smoothing rule must be declared upstream before held-out outcomes are opened.

## Gate B — known-truth recovery

Status: **implemented and tested**.

Analytic fixtures and concealed finite-observation recovery cover:

- planar sufficiency;
- pure vertical and temporal thickness;
- independent and coupled z×t structure;
- vertical, temporal and joint-only partition hidden by x-y projection;
- simple versus layered structural state-space capacity;
- thick but base-unorganized support, where `H(A|B)>0` but `I(A;B)=0` and held-out conditional gain is zero;
- stable base-resolved organization, where same-generating-process held-out support has positive conditional gain;
- shifted organization, where fitted `I(A;B)>0` can coexist with negative held-out conditional gain;
- grouped and cross-fitted sign-pattern recovery without allowing large sampling groups to dominate the terminal decision.

Known-truth recovery remains methodological evidence. It does not license treating opportunistic occurrence counts as unbiased organism-use probabilities.

## Gate C — source and observation semantics

Status: **implemented**.

`odsp.temporal_information` preserves observation time, precision and time-zone semantics without substituting upload time. `odsp.vertical_information` requires an explicit vertical meaning and distinguishes organism z from locality elevation, bathymetry, sensor placement and other contextual fields.

For empirical N2 work, x-y/context and the added biological/structural axis must be jointly observed or linked under a prospectively defensible observation architecture.

## Gate D — empirical axis-resolved validation

Status: **three prospectively bounded lanes completed; one unavailable, one thick/non-generalizing, one temporal generalizing**.

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

### D3 — Snapshot Serengeti temporal partition

Terminal category: **`temporal_partition_generalizing`**.

This independent lane was frozen before temporal outcomes in `N2_TEMPORAL_PARTITION_CONTRACT.json`. It tests whether time remains a thick state dimension after site is known, whether admitted mammal species partition that time axis within sites, and whether species-conditioned time distributions transfer to deterministic held-out site folds.

Frozen architecture:

- Snapshot Serengeti consensus detections and explicit search-effort intervals;
- source Tanzania local clock time (`UTC+3`, no DST conversion);
- 30-minute same-species/site event independence rule;
- event weight `1 / valid camera-days at site`;
- six fixed four-hour bins;
- outcome-blind species admission: >=500 events, >=20 sites and >=50 events in every one of three deterministic site folds;
- 199 within-site species-label permutations, seed `20260903`, alpha `0.05`;
- model species×time pseudocount `0.5`;
- leave-one-site-fold-out transferability, with each held-out fold evaluated against a model fitted from the other two folds.

Seventeen species passed the frozen structural admission gate.

Validated primary result:

- `H(T|Site) = 1.6396235816361795` nats;
- `exp(H(T|Site)) = 5.153229376935854` effective states out of six bins;
- `I(Species;T|Site) = 0.22427598739601606` nats;
- permutation `p = 0.005`;
- fold-0 gain `+0.0572411993741857`;
- fold-1 gain `+0.045158861333215006`;
- fold-2 gain `+0.04514355468571751`.

All three independent gains are >0, so the frozen transfer category is `generalizing`.

The correct interpretation is:

> Camera-detected time is a broad added state dimension after site is known; species identity partitions that detected time within sites; and the fitted species-conditioned temporal organization predicts every independently held-out site fold better than the identity-blind temporal marginal.

This is not a causal displacement test and does not establish true activity-time niches independently of time-varying camera detection, solar-time partitioning, or cross-region/cross-dataset generality.

The original workflow run `33726030526` failed after the frozen calculations because of a Python result-serialization boolean typo and produced no artifact. The recovery boundary was frozen before numerical interpretation. Recovery run `33774650396` checked out the original analysis SHA, changed only the five predeclared executed boolean literals, reverified the same checksum-pinned inputs and produced the recovered artifact. Closeout run `33775057303` validated that fixed artifact through the pre-existing fail-closed validator. See `N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json` and `docs/n2_serengeti_temporal_terminal_result_2026-09-04.md`.

The terminal summary is **not** an integrity-pinned axis-resolved N3 state artifact. No empirical N3 state payload is issued from this result.

## Gate E — habitat-complexity synthesis

Status: **not authorized / blocked under the current vertical empirical chain**.

The motivating hypothesis remains scientifically interesting:

> Equal horizontal area can contain unequal ecological state-space capacity; a vertically layered forest may contain more distinguishable within-cell states than a structurally simple open habitat under harmonized state definitions and observation semantics.

The positive Serengeti temporal result establishes that N2 can recover independently generalizing organization on an added axis, but it does not validate this specifically vertical habitat-complexity mechanism. The relevant vertical lanes remain:

- Tawaki: structurally unavailable;
- bat: structurally evaluable and vertically thick, but x-y-resolved vertical organization did not generalize across sealed individuals.

Therefore the forest-versus-grassland hypothesis is **not** tested, supported or rejected here. Pursuing it would require a separately frozen scientific programme with its own measurement architecture and validation logic; the temporal result cannot be used to rescue the completed bat endpoint.

## Current Chapter-N2 evidence spine

```text
known-truth thickness/projection recovery             supported
                ↓
model-agnostic organization/transferability           implemented
                ↓
source/axis semantics                                  implemented
                ↓
Tawaki first empirical z lane                          unavailable
                ↓
Bat native x-y-z structural feasibility                supported
                ↓
Bat descriptive vertical thickness                     present (~4.02 states)
                ↓
Bat independent vertical organization                  not generalizing

Independent temporal lane:
Serengeti temporal thickness                           present (~5.15 / 6 states)
                ↓
Serengeti within-site species-time partition           detected (p = 0.005)
                ↓
Serengeti cross-site-fold temporal organization        generalizing (3/3 > 0)

Gate E vertical habitat-complexity promotion           blocked
```

## Hard boundaries

- Do not alter or reopen SDMR Product A.
- Do not revive retired ODSP spatial topology/reachability; that belongs to EOG.
- Do not infer fundamental niche, causal coexistence, competition or predation from thickness or temporal partition alone.
- Do not equate native altitude above mean sea level with height above ground.
- Do not tune z/t bins, spatial grain, independent-group denominator, species gates, pseudocounts or candidate datasets after empirical outcome access.
- Do not rerun or rescue the completed Tawaki, bat or Serengeti empirical endpoints.
- Do not promote Gate E from the temporal result or from descriptive bat thickness.
- Do not treat a validated terminal summary as an empirical N3 state artifact without separately integrity-pinned state data.
