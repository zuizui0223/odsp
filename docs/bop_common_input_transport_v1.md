# BOP method v1: transported reduced inputs for future independent individual groups

## Methodological question

The original prospectively frozen BOP_RODENT random forest used
external temperature, unrounded GPS locations, season, local solar
clock hour and species. It cannot be scored unchanged against the
published Schaub 2026 Dryad Data_1a feature roster because
**external-temperature is undocumented there** and locations were
rounded to 0.1 degrees. No retrospective feature substitution or
imputation can call that original RF "externally validated."

We therefore introduce a **new, separate, explicitly reduced-input
categorical reference learner** that trains on one set of biologically
independent individual groups and evaluates new individual groups in
a different data source. Its predictor and baseline are frozen *before*
target-source calibration or validation outcomes open.

This is software methodology validated on generated known-truth
source schemas, **not** an external empirical BOP or Dryad result.

## Common feature definition and frozen semantics

- Training role accepts precisely the source-projected BOP fields:
  row ID, individual ID, taxon, ISO8601 UTC timestamp with explicit
  Z or +00:00, unrounded longitude and raw altitude above MSL.
- Target calibration/validation roles accept precisely the source-
  projected Dryad fields: row ID, global individual ID, canonical
  taxon, UTC timestamp, and longitude rounded to 0.1 degrees.
  **No altitude, speed, temperature, model predictions, outcome or
  any other post-treatment field is allowed in target features.**
- Restrict to the original four prespecified raptor taxa.
- Preserve BOP raw **AMSL** training target categories:
  <50, 50–200, 200–500 and >=500 metres. The old BOP admissible
  -100 to 5000 metres range is retained for training; these are not
  heights above ground and Dryad Data_2a's flight-only corrected
  height is explicitly out of scope.
- Compute one **binary local mean-solar CLOCK** context per row from
  UTC plus longitude/15. Context 1 is 06:00–18:00, context 0 otherwise.
  It is not a calculated solar elevation, sunrise or biological daylight
  period; this is solely a reproducible common statistical feature.
  No claim about ecological activity rhythms is made by this method.
- Longitude rounding by at most 0.05 degrees can move mean solar time
  by at most 0.05/15 hours = **12 seconds**. Reject every source row
  within this 12-second window of 06:00 or 18:00. Apply the **same**
  rejection to both BOP-style and Dryad-style rows, so rounding cannot
  silently reverse a hard day/night class.
- Exclude latitude, original unrounded longitude as a direct spatial
  feature, and external temperature from the **new** learner. Reject
  target fields that could leak altitude or future realized outcomes.
  Only an explicit UTC timestamp and longitudinal transformation may
  contribute this one context.

Source-specific IDs are namespaced to avoid accidental software
collisions. Namespacing is **not proof** that two records refer to
biologically distinct birds: a real-source identity crosswalk and
study/population design would need independent confirmation.

## Executable prediction-and-calibration path

1. Strictly project the source-native training, calibration and
   validation feature rosters. Reject unsupported taxa, naïve clock
   timestamps, unrounded target-source longitudes, ambiguous clock
   boundaries, missing values, mixed species within an ID, or any
   holdout target outcome.
2. Call the already developed managed ODSP learner, using only
   BOP-style **training** outcomes, with equal per-individual
   training mass, species×binary-context categorical state
   probabilities and a training-only **species marginal** reference.
   The model/reference byte digests, training source and BOTH future
   feature/prediction rosters are frozen.
3. Fit one mean per-individual log predictive *context gain above species
   marginal* on independent calibration individuals from the target
   source. A rank bound remains vacuous when group count is too small.
4. Verify model/source/prediction and calibration digests, then score
   untouched test individuals of the same target source. No held-out
   data are used to refit the model. Full group-rank finite-sample
   coverage remains conditional on **exchangeability of calibration
   and validation individual gains within the new source**, not on
   equal membership in the original training distribution.

The critical scientific distinction is:

> A model can be inaccurate or have negative average transfer gain
> after source shift, yet its one-sided group gain prediction bound
> can still have valid *coverage* if target-source calibration
> individuals and future target-source individuals are exchangeable.

Coverage is not proof of positive predictive skill, source similarity,
all-individual positivity or population causality.

## Separate known-truth, pre-outcome contract

Before opening any simulated target outcomes, we froze:
\`research/BOP_COMMON_INPUT_TRANSPORT_V1_CONTRACT.json\`.

- 24 independently seeded synthetic worlds beginning at seed 20261028.
- Four original BOP taxa, 4 original raw AM SL altitude-state bins,
  and binary common solar-clock contexts.
- For each species/world: **20 independent BOP-style training birds,
  39 Dryad-style calibration birds and 30 Dryad-style final validation
  birds** (8–16 events per individual).
- Training-source context amplitude 1.4; target-source amplitude 1.1:
  a modest train→target change, with target calibration/test draws
  remaining exchangeable conditional on the frozen training predictor.
- The target calibration and test roles are generated without
  altitude states until *after model and both future forecast rosters
  are fixed*. Their mean log-score gains and rank lower bounds
  are computed at the individual level, not per event.
- Explicit negative control: rotate only the final validation
  state labels by +2 modulo four categories, without retraining or
  recalibration. It deliberately breaks within-target distribution
  exchangeability and may invalidate rank coverage.
- One-sided miscoverage 0.10 gives rank 4 for 39 calibration
  individuals within each species. There are exactly
  24×4×30 = **2,880 independent synthetic target validation birds**
  in each condition.
- Prior-to-first-result success window: same-source coverage
  0.84–0.96, negative-control coverage <=0.80, correct 2,880
  independent groups, frozen model/forecast/calibration signatures
  and original BOP/2026 source gate/Dryad no-admission unchanged.

First run must be archived even on failure. No result-driven source,
feature, reference or threshold tuning is allowed within this route.

## Source files and running

- \`odsp/common_input_transport.py\`: exact two-source projections,
  date/longitude normalization, preserved original AMSL bins,
  common feature construction and managed learner bridge.
- \`scripts/run_bop_common_input_transport_v1.py\`: prespecified
  synthetic source-shift and target-only shift experiment.
- \`tests/test_common_input_transport.py\`: clock/precision boundary,
  outcome leakage, source-role/stratum and replay regression tests.
- \`tests/test_bop_common_input_transport_contract.py\`: contract freeze
  and known-truth generator checks.

Commands:

\`\`\`bash
python -m pytest tests/test_common_input_transport.py tests/test_bop_common_input_transport_contract.py
python scripts/run_bop_common_input_transport_v1.py --out /tmp/bop-common-input-transport-v1.json
\`\`\`

## External biological admission remains unresolved

Dryad's public API identity, CC0 license and semantic data version are
documented in PR #277. However, real Data_1a outcomes and individual
identities were deliberately not accessed; non-GPS supplementary file
downloads returned HTTP 403. The whole-dataset total of 217 individuals
from BOP's four species is **not** an eligible independent test roster.
The earlier BOP v3-v2026 same-study route remains closed (10 additional
IDs across taxa, maximum six within a single taxon).

To make any real cross-study claim, an **independently frozen new route**
must attest source version/checksums, all source ID crosswalks and
potential same tagged birds, licenses, event cadence and altitude
semantics, training-source reproduction of the *new model*, and
target-source independent calibration/validation group admission.
This would not be an unchanged-RF transfer experiment and would
not reclassify the original ODSP BOP **27/30 positive, mixed** result.
