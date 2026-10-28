# ODSP — Chapter 2: multidimensional niche geometry

ODSP is **Chapter 2** of the fixed four-chapter programme `niche-to-survey-four-chapter-v1`:

1. **SDMR** — which environmental dimensions define an interpretable realized niche?
2. **ODSP** — how thick and multidimensional is that niche beyond a flat x-y map?
3. **EOG** — which distributional/transition worlds remain possible and reachable?
4. **ACSP** — where should field effort be directed next?

See [`FOUR_CHAPTER_PROGRAM.md`](FOUR_CHAPTER_PROGRAM.md), [`CHAPTER_CONTRACT.json`](CHAPTER_CONTRACT.json), and [`CHAPTER2_ROADMAP.md`](CHAPTER2_ROADMAP.md).

## Research domain handoff to RSDS — 2026-10-26

**Solar radiation, Sun azimuth, astronomical/civil time, seasonal GPS movement, same-photoperiod comparisons and related ecology now belong in [RSDS](https://github.com/zuizui0223/RSDS).** The complete original-data science migration was validated and merged in [RSDS PR #1](https://github.com/zuizui0223/RSDS/pull/1), with [390 matching original Git blobs](https://github.com/zuizui0223/RSDS/blob/main/provenance/RSDS_TRANSFER_VERIFICATION_20261026.json) and [passing RSDS main CI](https://github.com/zuizui0223/RSDS/actions/runs/40260697816).

This repository remains the primary home for ODSP **methodology**. Earlier solar/time ecology result receipts and PRs remain unchanged here for provenance, not as the destination of future ecological papers or new ecological conclusions. The preregistered external solar-radiation nonreplication is preserved in RSDS.

## Scientific center

A conventional species-distribution product ultimately collapses support to a horizontal field:

```text
S(x, y)
```

ODSP asks what that projection discards. An ecological state can instead be indexed by additional axes:

```text
S(x, y, z, t, ...)
```

where `z` may represent canopy stratum, height, water/soil depth or another explicit vertical state, and `t` may represent observation/activity time, date or season when the source precision permits it.

The Chapter-2 question is:

> **HOW THICK is it? — How much ecological state-space information is lost when a multidimensional niche/support distribution is flattened to x-y?**

The working principle is: **地図は、niche を薄くする。**

## State-resolved ecological prediction

ODSP now extends beyond projection-loss diagnosis to predict **full ecological-state probability distributions** rather than only single-valued suitability outputs. The common prediction targets are:

```text
P(A | B)   discrete/base-state prediction
P(A | X)   continuous-covariate prediction at new rows/locations
```

where `A` may be one or more added ecological states such as altitude layer, depth, time bin, phenophase, behaviour or microhabitat. The package includes a transparent conditional reference learner, event-table encoding, optional scikit-learn probability-estimator bridges, rich per-state output, and held-out log-score/Brier/top-1 evaluation.

The prospectively frozen BOP_RODENT public-data endpoint provides a larger multi-species empirical validation of this prediction layer. Thirty independently scored individuals from four admitted raptor species passed the frozen admission architecture. The primary random-forest state model improved held-out log score over the training marginal altitude distribution in **27/30 individuals** and improved multiclass Brier score in **30/30**. Under the deliberately conservative all-individual rule the terminal result is **mixed**, not generalizing: *Buteo buteo* and *Circus pygargus* were species-level generalizing, while *Circus aeruginosus* and *Circus cyaneus* contained conflicting held-out individuals. See [`BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json`](BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json) and [`docs/bop_rodent_state_prediction_terminal_2026-09-05.md`](docs/bop_rodent_state_prediction_terminal_2026-09-05.md).

This prediction layer does **not** turn ODSP into a new MaxEnt/RF-style occurrence algorithm. Upstream learners can produce state probabilities and ODSP supplies a common ecological-state target, richer prediction output and independent scoring architecture.

## Independent-group predictive gain envelopes

The historical BOP_RODENT 27/30 positive held-out RF log-score gains describe
performance for **30 tagged individuals**, not 154,655 independent future
animals. ODSP now exposes a one-sided **new-group gain lower envelope** that uses
one held-out mean gain per independent group and a finite-sample order
statistic. For a fixed predictor and exchangeable calibration/future group
scores, the rank construction has conditional marginal new-group coverage;
if too few groups exist it deliberately returns a vacuous lower bound.

The read-only archived BOP example gives a *descriptive* 90%-rank lower value
of -0.026803 for the original pooled-comparator RF gain. Because its folds use
different models and four species are heterogeneous, **this is not a formal
90% forecast guarantee** for a future BOP individual; the frozen mixed
terminal result is unchanged. See
[method, known-truth tests and archived BOP audit](docs/bop_new_group_gain_envelope_v1.md).

### Fixed-predictor independent-animal validation

The new [fixed-forecast group protocol](docs/bop_fixed_model_group_validation_v1.md)
locks training/calibration/validation animal rosters, pre-outcome state
probabilities and the actual fitted-model/reference bytes. It then scores
one mean held-out log-score gain **per independent individual**, estimates
a stratified lower transfer-gain bound from calibration individuals only,
and evaluates that frozen bound on previously unseen validation individuals.

Under the prospectively committed 128-world **known-truth** contract,
the first execution obtained **89.94%** group-level coverage for
same-process new animals (nominal 90%), and **6.81%** under a deliberate
four-state-label distribution shift. Each evaluation used 40,960 simulated
individual scores; all five frozen acceptance checks passed. Results are
archived in `BOP_FIXED_MODEL_GROUP_TRANSFER_V1_VALIDATION_RECEIPT.json`.
This is **synthetic method validation**, not evidence of 90% coverage for
new real BOP_RODENT birds; the archived BOP terminal outcome remains
`empirical_state_prediction_mixed`.

### Managed provenance for state probability forecasts

The [managed group forecast method](docs/bop_managed_source_to_forecast_v1.md)
repairs an important limit of hashing model files and caller-supplied
predictions separately: for its transparent stratum-by-binary-context
categorical reference learner, ODSP now **fits the model only from
training-source observations, generates holdout class probabilities
from the actual model/reference artifact bytes, and replays both**
before independent calibration or validation outcomes are scored.
Training rows, individual roles, feature rosters and model artifacts
are content-bound; group-balanced weighting and cross-role separation
are validated. This does not assert arbitrary RF artifact execution.

Under a separately frozen 64-world known-truth test, the fully managed
chain achieved **89.15%** independent-new-group coverage at nominal 90%
for 10,240 synthetic validation animals, versus **12.87%** under a
deliberately shifted state distribution. Its five predeclared checks
passed; the first-run summary and archive digests are pinned in
`BOP_MANAGED_SOURCE_TO_FORECAST_V1_VALIDATION_RECEIPT.json`.
These are mathematical-method results, not new empirical BOP_RODENT
outcomes. The original all-individual BOP endpoint remains **mixed**.

## Future-individual BOP methods-paper working draft

The [individual-level transfer-gain methods manuscript](manuscript/BOP_INDEPENDENT_ANIMAL_GAIN_METHODS_DRAFT_v1.md)
and [technical rank-coverage assumptions note](docs/bop_individual_gain_inference_theory_v1.md)
assemble the already frozen BOP #274–#280 method stages, biological
mixed endpoint, synthetic group-rank coverage and independent-source
admission stops into a single evidence-checked narrative.

The [paper's machine-checkable evidence crosswalk](research/BOP_METHOD_PAPER_EVIDENCE_MATRIX_V1.json)
binds all numeric claims to original Git blob identities; its tests
cannot turn synthetic coverage into real Dryad validation, claim that
standard conformal rank validity is novel, or change the original BOP
all-individual mixed endpoint. **Working draft only, not a ready
submission.** A separate eligible real external-bird study and/or a
clearly distinct methodological contribution beyond established
conformal ranks remain substantial scientific gaps.

## BOP method integration and independent animal admission

ODSP's five linked BOP methodology PRs [#274](https://github.com/zuizui0223/odsp/pull/274)–[#278](https://github.com/zuizui0223/odsp/pull/278) were **merged into main**. Their methods-paper evidence and explicit stopping conditions are collected in [the BOP methodology spine](docs/bop_method_spine_v1.md). They separate historical held-out individual prediction gain, future-group lower prediction bounds, exact trained-model-to-forecast replay, biological source admission and synthetic cross-source input transport.

The [identity-checked end-to-end source-to-gain chain](docs/bop_identity_checked_transport_integration_v1.md)
now composes the existing source-trained managed predictor, an exact
canonical-animal identity crosswalk, nonvacuous target calibration-group
rank admission, and untouched-group gain validation **in execution order**.
It replays both the fitted model/forecast probabilities and the identity
roster before each outcome-consuming step. Unlike simple provider-prefix
ID comparisons, it also requires the declared training species per
animal to match the actual fitted training source. This is **synthetic-only
method integration** and cannot certify real BOP–Dryad bird identity,
ecological exchangeability or source admission.

The new common-input transport example achieved nominal-90% group-bound coverage of **2,599/2,880 (90.24%)** across 24 independently simulated model/calibration worlds, versus **757/2,880 (26.28%)** under deliberate validation-only response shift. An additional *post-result descriptive* uncertainty audit correctly uses **24 model/calibrator worlds**, not 2,880 pseudoreplicated individuals, as its Monte Carlo unit. These are method checks, not new GPS or ecological findings.

For a real external study, **matching software group IDs is insufficient**: the same bird can appear under different provider names or multiple deployments. The [outcome-blind canonical animal identity gate](docs/bop_group_identity_admission_v1.md) checks externally mapped animal identity keys, immutable training/calibration/test group rosters and nonvacuous **within-species** rank support without opening test outcomes. A passed count is not a certification of independence or exchangeability. The historical BOP terminal stays **mixed**, the 2026 within-species new-animal route remains closed, and Dryad remains **NOT_ADMITTED** for direct historic RF external testing.

## Niche thickness

`odsp.niche_geometry` provides model-agnostic information-theoretic metrics on any non-negative support distribution.

For horizontal axes `X,Y`, vertical axis `Z` and time axis `T`:

```text
vertical information      = H(Z | X,Y)
temporal information      = H(T | X,Y)
joint added information   = H(Z,T | X,Y)
```

The corresponding effective state counts are:

```text
vertical thickness        = exp(H(Z | X,Y))
temporal thickness        = exp(H(T | X,Y))
joint added thickness     = exp(H(Z,T | X,Y))
```

These quantities answer: **after horizontal location is already known, how many effectively distinct states remain along the added axes?**

`axis_thickness_map(...)` returns the same information separately for each supported x-y cell. A species-support tensor yields descriptive niche thickness; an explicitly defined availability/capacity tensor can instead represent structural state-space capacity. Those interpretations must not be mixed.

## Thickness magnitude versus thickness organization

The empirical results show why two distinct questions are needed:

1. **Thickness magnitude:** is added-axis state information present in a fitted support?
2. **Thickness organization / transferability:** does the detailed conditioned added-axis distribution remain useful for independent individuals, sites or observations?

A fitted support can be descriptively thick without its detailed organization generalizing. Conversely, a thick added axis can contain identity-resolved organization that does generalize.

`odsp.transferability` makes that distinction explicit and model-agnostic. For base state `B` and added state `A`:

```text
in-sample organization    = I(A;B)
held-out transferability  = E_heldout[log P_model(A|B) - log P_model(A)]
```

`base_added_mutual_information(...)` measures fitted organization. `score_conditional_transferability(...)` tests whether that organization predicts independent support better than the lower-information marginal representation. `classify_independent_gains(...)` and the grouped-transferability layer provide conservative all-positive / all-nonpositive / mixed decisions for prospectively independent held-out groups without allowing a large group to rescue a failed one. Cross-fitted grouped scoring permits each held-out group to have its own prospectively defined training model.

The transferability core deliberately performs no hidden smoothing. Any smoothing or pseudocount rule must be declared upstream before held-out outcomes are opened. Known-truth tests include thick but unorganized support, stable organization with positive held-out gain, and shifted organization with negative held-out gain.

## Training-process uncertainty versus fixed-set robustness

ODSP now keeps two upstream-refit questions explicitly separate.

A **fixed supplied refit set** supports an intersection claim: every supplied
refit must pass. A **prospectively frozen training-resampling process** supports
a different estimand: the mean held-out directional gain over that stochastic
refitting process, conditional on the frozen empirical training source.

The qualified training-process route is deliberately narrow: one-sided
independent-group inference for an ordered two-contrast filtration. Its canonical
internal surface verifies the frozen process manifest, ODSP-managed model
generation and whole-source-frame training/validation separation before invoking
the qualified two-term CV3(2) intersection-union test. A separate qualified
untouched-external endpoint freezes row/group/block/weight metadata before
outcome access, derives scores through managed model-to-score execution, and
then calls the unchanged internal provenance-verifying wrapper.

The route does **not** claim that all possible refits are positive, estimate the
success probability of an individual future refit, or generalize over repeated
draws of the original ecological training dataset. Existing fixed-set and
historical empirical results are unchanged.

See
[`docs/training_process_v5_confirmatory_chain.md`](docs/training_process_v5_confirmatory_chain.md)
for the complete internal-to-external chain and its qualification boundaries.

## Temporal thickness versus temporal partitioning

Time is not treated as a special side analysis. It is an added niche axis with a separate identity-partition question.

For declared context `B` (for example site), time `T`, and a predeclared identity axis `C` such as species, individual or guild:

```text
temporal thickness      = H(T | B)
temporal states         = exp(H(T | B))
temporal partition      = I(C;T | B)
                       = H(C|B) + H(T|B) - H(C,T|B)
```

`odsp.temporal_partition` keeps three claims separate:

1. time may add ecological-state thickness;
2. identities may partition that time axis within the same context;
3. the fitted identity-specific temporal organization may or may not transfer to independent sampling units.

A large `H(T|B)` does not establish temporal partitioning, and a positive `I(C;T|B)` does not establish transfer. `I(C;T|B)` is descriptive conditional association and is not a causal displacement or competition metric.

## Current empirical status

### Tawaki lane

Terminal category: **`empirical_gate_d_unavailable`**.

The first GPS+dive lane failed its frozen full site×year structural coverage rule before any thickness outcome was opened. It remains a valid empirical-unavailability result and is not rescued by later work.

### European free-tailed bat vertical lane

Terminal category: **`empirical_n2_thickness_not_generalizing`**.

The second empirical lane used a public native same-event x-y-z Movebank stream for *Tadarida teniotis*. Source architecture, source identity/checksum, 5 km grid, z bins, individual weighting, 6-model/2-sealed split, and answer-check rule were all frozen before numeric height was opened.

Primary result:

```text
H(Z|X,Y)                   = 1.3918623004770097 nats
effective vertical states = 4.022333876564191
sealed Bat5 gain           = -0.43541033813280833
sealed Bat7 gain           = -0.021938657402345435
```

Thus the model-pool support is **descriptively vertically thick**, but the frozen `P_model(z|x,y)` did not predict either sealed bat's vertical state better than the model-pool marginal `P_model(z)`. The detailed x-y-conditioned vertical organization therefore did **not** generalize under this endpoint.

This does **not** mean the vertical axis is absent. It means the transferable spatial organization required by the frozen empirical support rule is not supported.

See [`N2_BAT_THICKNESS_TERMINAL_DECISION.json`](N2_BAT_THICKNESS_TERMINAL_DECISION.json) and [`docs/n2_bat_thickness_terminal_result_2026-09-01.md`](docs/n2_bat_thickness_terminal_result_2026-09-01.md).

### Snapshot Serengeti temporal-partition lane

Terminal category: **`temporal_partition_generalizing`**.

A third, independent empirical lane tested time rather than recycling the bat stream. The complete pre-outcome design is frozen in [`N2_TEMPORAL_PARTITION_CONTRACT.json`](N2_TEMPORAL_PARTITION_CONTRACT.json). It uses Snapshot Serengeti consensus camera detections and camera search-effort intervals, preserves Tanzania source local clock time (`UTC+3`), applies the frozen 30-minute same-species/site independence rule, inverse-camera-day weighting, six fixed four-hour bins, outcome-blind species admission, 199 within-site label permutations, and three deterministic leave-one-site-fold-out answer checks.

Seventeen species passed the frozen admission gate. The validated terminal result is:

```text
H(T|Site)                      = 1.6396235816361795 nats
effective temporal states     = 5.153229376935854 / 6 bins
I(Species;T|Site)              = 0.22427598739601606 nats
permutation p                  = 0.005
held-out site-fold 0 gain      = +0.0572411993741857
held-out site-fold 1 gain      = +0.045158861333215006
held-out site-fold 2 gain      = +0.04514355468571751
```

All three independently held-out site-fold gains are positive. The frozen species-conditioned temporal organization therefore **generalizes across the three held-out spatial folds** rather than merely appearing in the fitted support.

This is the complementary positive case to the bat result: the bat lane is thick but its detailed vertical organization is non-generalizing, whereas the Serengeti lane is temporally thick, species-partitioned, and independently generalizing. The combined empirical message is therefore not simply “multidimensional niches exist”; it is that **added-axis thickness and transferable added-axis organization are separate properties that can have different empirical outcomes**.

The original terminal workflow run `33726030526` encountered a post-calculation Python serialization error before any result artifact was saved. A technical recovery was frozen before numeric interpretation, checked out the original analysis SHA, changed only five JSON-style Python boolean literals, reused the checksum-pinned inputs and frozen analysis, and produced the recovered result. That result then passed an independently frozen fail-closed closeout validator. The canonical receipt is [`N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json`](N2_SERENGETI_TEMPORAL_TERMINAL_RECEIPT.json); full provenance and claim boundaries are in [`N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json`](N2_SERENGETI_TEMPORAL_TERMINAL_DECISION.json) and [`docs/n2_serengeti_temporal_terminal_result_2026-09-04.md`](docs/n2_serengeti_temporal_terminal_result_2026-09-04.md).

The positive result is still about camera-detected local-clock-time organization under the frozen observation architecture. It does not by itself identify true activity-time partition independent of detection, solar-time partition, competition or temporal displacement, or cross-region/cross-dataset generality.

## Input layers

### Source-preserving observation time

`odsp.temporal_information` standardizes observation-time metadata already present in public occurrence sources while retaining source fields and actual precision.

For GBIF this includes fields such as `eventDate`, `eventTime`, year/month/day, day-of-year interval fields and verbatim date. For iNaturalist it includes `observed_on`, `observed_on_string`, `time_observed_at`, `time_observed_at_utc`, `time_zone` and `zic_time_zone` when present.

Rules include:

- upload/creation/update timestamps are **never** substituted for biological observation time;
- date-only records do not become ecological midnight observations;
- timezone is not invented from coordinates at ingestion;
- conflicting duplicate fields are flagged rather than silently resolved;
- missing/partial time remains missing/partial.

### Explicit vertical semantics

`odsp.vertical_information` requires callers to declare the semantic meaning of a vertical field. It distinguishes organism height/depth or structural state from locality elevation, bathymetry, sensor placement and other contextual fields.

The bat primary axis is deliberately the native GPS `height_above_msl`. It is not relabeled as height above ground and no DEM subtraction is introduced post hoc.

## Example

```python
import numpy as np
from odsp import niche_thickness_profile, normalize_occurrence_time

observation_time = normalize_occurrence_time(
    "gbif",
    {
        "key": 123,
        "eventDate": "2026-05-17T21:34:12+09:00",
        "year": 2026,
        "month": 5,
        "day": 17,
    },
)

# y × x × canopy-stratum support.
forest_support = np.ones((2, 3, 4), dtype=float)
profile = niche_thickness_profile(
    forest_support,
    horizontal_axes=(0, 1),
    vertical_axis=2,
)

print(observation_time.temporal_precision)  # second
print(profile.effective_vertical_states)   # 4.0
```

## Scientific boundary

ODSP does **not** modify SDMR Product A. It is not a new environmental-variable selector, AUC replacement, or SDM tuning endpoint.

Raw opportunistic record counts are not automatically treated as unbiased biological-use probabilities. Empirical niche-thickness inference must separately address effort, detectability, sensor geometry, time coverage and vertical coverage. Exact generating niche geometry is available only in known-truth/synthetic validation; empirical claims are about measured or model-supported realized state use under declared observation semantics.

Camera-detected temporal partitioning is not automatically true activity-time niche partitioning because detection probability may vary through time. Clock-time partitioning is not solar-time partitioning. A positive `I(C;T|B)` does not identify interspecific displacement, competition or any other causal mechanism.

The former ODSP spatial-patch/topology method remains retired. Its defensible support-topology component was migrated to EOG. ODSP must not grow a duplicate reachability/topology implementation.

## Current development boundary

The current N2 empirical chain is scientifically closed at:

```text
known-truth thickness/projection recovery          supported
model-agnostic organization/transferability        implemented
Tawaki empirical lane                              unavailable
Bat descriptive vertical thickness                 present (~4.02 effective z states)
Bat cross-individual x-y-z organization             not generalizing
Serengeti temporal thickness                       present (~5.15 / 6 effective t states)
Serengeti within-site species-time partition        detected (p = 0.005)
Serengeti cross-site-fold temporal organization     generalizing (3/3 gains > 0)
BOP_RODENT state-resolved altitude prediction       mixed (27/30 individual gains > 0)
Gate-E forest/grassland promotion                   blocked
```

The thickness and prediction lanes deliberately do not collapse into one answer about “multidimensionality”: the bat and Serengeti lanes show that thickness magnitude can be present while transferability differs, and the BOP_RODENT endpoint shows that richer state-resolved prediction can improve strongly on average while still failing the all-individual generalization rule. These distinctions are empirical results, not just methodological warnings.

Neither the bat terminal summary nor the Serengeti terminal summary is an integrity-pinned N3 state artifact. No empirical N3 state payload is issued from the Serengeti summary despite its positive transferability result. The BOP_RODENT prediction result is likewise an N2 predictive terminal receipt, not an automatic N3 state promotion.

The forest-versus-grassland structural-capacity hypothesis remains interesting but is **not authorized as a continuation or rescue of the completed bat endpoint**. Any future test would require a separately frozen programme with its own measurement architecture and validation logic.

Do not rerun or retune the completed Tawaki, bat, Serengeti, MH_ANTWERPEN or BOP_RODENT endpoints, swap datasets after outcome access, replace primary bins/species gates, or use a descriptive mean or terminal summary alone to claim an empirical N3 state.
