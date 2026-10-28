# BOP ODSP core: joined identity-checked source-to-gain execution

## Purpose and status

ODSP's original BOP methodology is now integrated into main. The
individual-identity gate added in PR #279 catches reused canonical animals
and vacuous within-species group ranks **before outcomes are opened**.
But that standalone gate could previously be called without becoming a
precondition for the subsequent target calibration and validation APIs.

This small integration adds an **opt-in synthetic-only guarded route**
that executes the entire chain in one order:

\[
\text{source-training model}
\rightarrow\text{outcome-blind future forecasts}
\rightarrow\text{canonical animal identity + within-species rank}
\rightarrow\text{target calibration labels}
\rightarrow\text{untouched target validation labels}.
\]

This is a regression/acceptance test of the existing method components,
not a new model, a fresh statistical experiment or an ecological finding.

## What is independently replayed

The new module \`odsp/identity_checked_transport.py\` exposes:

- \`freeze_identity_checked_transport(...)\` — requires the existing
  \`CommonInputTransport\`, exactly matching identity metadata for its
  frozen training/calibration/validation groups and
  \`evidence_role="known_truth_synthetic_only"\`. The generic
  \`audit_frozen_group_identity_support\` must return
  \`COUNT_GATE_PASSED_EXCHANGEABILITY_NOT_PROVED\`, not a HOLD.
- \`calibrate_identity_checked_transport(...)\` — re-fits the same
  executable training-only model from its source rows, regenerates
  conditional/reference holdout probabilities, and **rechecks** the
  frozen cross-source individual IDs and group counts *before* accepting
  calibration outcomes. It delegates scoring to ODSP's unchanged
  managed calibration API.
- \`validate_identity_checked_transport(...)\` — rechecks source,
  model, forecasts, identity records, rank counts and calibration digest
  **before** reading validation outcomes. It then calls the existing
  untouched individual validation API and verifies that the observed
  validation group counts and rank equal the admitted group roster.
- \`FrozenIdentityCheckedTransport.as_public_dict()\` — outputs only
  per-species/stratum group counts, source names and status; **never**
  exports original source IDs, crosswalk animal identities, study
  cluster IDs or individual GPS/outcome values.

### Additional training-source protection

The generic \`FrozenGroupForecastPlan\` identifies training groups
without storing their fitted training stratum per group. A supplied
identity metadata roster could falsely assign training birds to a
different species and create fabricated training support for a
target source. The joined route **reconciles the declared training
metadata's \`group_id\` → \`stratum\` mapping with the actual
training-row source used in \`ManagedGroupForecast\`** before
counting any supported source species. The mapping is rechecked before
both calibration and validation.

### Snapshot immutability and identity ambiguity

The cross-source canonical ID map is snapshotted into immutable
\`GroupIdentityRecord\` dataclasses, sorted by group ID, and bound to
the frozen forecast plan by a private SHA256 digest. Later edits to
the caller's original dict/list objects cannot alter the stored
admission. Changing stored canonical IDs, source fields, model bytes,
predicted probabilities or the previously admitted count/attestation
raises an error at the next replay.

The private object retains the externally supplied identity rows to
repeat these checks, but its **public** representation never exposes
them. The SHA digest is not published as a surrogate for direct animal
identity data, and should not be treated as proof of authentic sampling.

Every operation carries a deliberately hard-coded synthetic-only
evidence-role restriction. This means **the route cannot be used as
permission to open actual BOP or Dryad GPS data**. Independent
biological source admission would require its own prospectively frozen
protocol and independently audited identity evidence.

## End-to-end synthetic fixture

\`tests/test_identity_checked_transport.py\` builds two artificial
raptor-stratum sources using the source-native public input schemas.
Per stratum, it fits a fresh managed categorical model on three
synthetic training birds, freezes identity-bearing source/target
features, admits nine independent target calibration birds and two
disjoint untouched target test birds. Each individual supplies a small
number of synthetic event rows.

The test executes actual
\`freeze_common_input_transport\` →
\`freeze_identity_checked_transport\` →
\`calibrate_identity_checked_transport\` →
\`validate_identity_checked_transport\`
and confirms the original frozen prediction-model digest, the
nonvacuous group-rank (\`k=1\` for \`n=9\`, \`alpha=0.10\`), calibration
digest and four target test-group scores.

Negative regressions:
- cross-source identity reuse even when provider IDs differ;
- false training-species claims inconsistent with the fitted model;
- eight calibration birds despite substantial pooled totals;
- target metadata exposing altitude, time or outcomes;
- edits to identity dictionaries after freezing;
- forged identity record, altered group-gate decision, model file or
  future forecast plan;
- passing validation outcomes during calibration or vice versa;
- attempts to treat this synthetic route as a real source admission.

No BOP historical GPS fixes or Dryad telemetry file is accessed,
no archived results are recalculated, and no claim of future real-bird
group-gain coverage is made.

## Running

\`\`\`bash
python -m pytest tests/test_identity_checked_transport.py tests/test_group_identity_gate.py tests/test_common_input_transport.py
\`\`\`

## Claim ceiling

The biological BOP result is still **27/30 positive individual
log-score gains, 30/30 Brier improvements, overall \`mixed\`**.

The 2026 update remains
\`NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT\`, and independent
Schaub/Dryad biological data remain \`NOT_ADMITTED\` under the original
BOP random-forest predictor schema. Original synthetic coverage
receipts and model/cross-source known-truth generation contracts
remain byte-for-byte intact. Passing this software execution check
does not demonstrate new species/population generality, authentic
identity crosswalks or biological calibration/test exchangeability.
