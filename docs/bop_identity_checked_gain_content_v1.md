# BOP synthetic identity-checked positive-content integration (v1)

**Implementation only; no empirical BOP-to-Dryad validation.** This page
documents a new opt-in source-to-identity-to-content bridge. The original
BOP random-forest mixed result, unadmitted real Dryad candidate, Swiss
retrospective analyses and all historical evidence receipts are unchanged.

## Problem resolved

The lower-level exact binomial test (PR #303) binds an immutable forecast
plan, reference, content target, and threshold but does not itself establish
that each group is a different biological animal or that the probability
vectors were derived from a source-trained model. The existing synthetic
identity-checked transport can replay both obligations but previously
reported only the rank-based new-animal gain endpoint.

The additive adapter in odsp/identity_checked_gain_content.py makes these
**software checks executable in the same preaccess sequence**:

    frozen synthetic training rows
       -> managed categorical model and baseline artifacts
       -> frozen calibration/validation forecasts
       -> exact role-specific canonical animal crosswalk
       -> single-target-stratum content count preflight (no outcomes)
       -> calibration-only exact content assessment
       -> previously untouched validation under the same calibration

## API and use

Starting from a FrozenIdentityCheckedTransport object that has already
passed freeze_identity_checked_transport:

~~~python
from odsp.identity_checked_gain_content import (
    freeze_identity_checked_gain_content,
    assess_identity_checked_gain_content,
    validate_identity_checked_gain_content,
)

binding = freeze_identity_checked_gain_content(
    identity_checked,
    stratum="Buteo buteo",
    sampling_assumption="iid_group_gains_within_prespecified_stratum",
    minimum_positive_fraction="0.9",
    confidence_level="0.95",
    gain_threshold=0,
)
# No target label values are accessed here.
print(binding.as_public_dict())

assessment = assess_identity_checked_gain_content(
    binding, calibration_states_by_native_row,
)
print(assessment.as_public_dict())
validation = validate_identity_checked_gain_content(
    binding, assessment, validation_states_by_native_row,
)
~~~

Here identity_checked and both outcome mappings must be constructed within
the caller's separate **synthetic known-truth** protocol. The public APIs in
this existing source adapter explicitly reject real Dryad/BOP source
admission; the example is not a way to bypass that gate.

The adapter accepts **native, unprefixed Dryad row IDs** at assessment and
validation. It checks the exact calibration role key set before reading
a single value. It then snapshots each allowed calibration label once,
prefixes it with the frozen Dryad namespace, and delegates scoring to
the unchanged PR #303 procedure. Validation uses the returned original
FrozenGainCalibration without changing the content hypothesis or threshold.

The new integration deliberately requires exactly one target stratum across
the entire calibration and validation rosters. The underlying scorer needs
complete calibration-role outcomes; allowing a multi-stratum roster would
otherwise open labels of other, unselected strata. This restriction
is a preaccess privacy/confirmatory boundary, not a biological claim about
cross-taxon homogeneity.

At c=0.90 and confidence 0.95, 9 group IDs can pass the older rank-count
gate but cannot make an exact-content test pass. The first count capable of
support is 29 distinct admitted calibration animals, **all strictly above**
the fixed threshold; a separate validation animal is retained. With one
calibration gain at or below threshold, 46 total are required.

## What the adapter verifies

- Recreates the same source-trained managed categorical model and reference,
  their holdout probabilities and exact frozen source/feature rosters.
- Rechecks the supplied full canonical-animal identity crosswalk for
  reused animals across source, calibration and validation roles.
- Checks one target stratum and count feasibility before calibration labels.
- Rejects mismatched or extra validation/calibration native row IDs before
  reading any values; preserves a single calibration snapshot.
- Uses the established exact binomial p-value and finite weighted-mean
  threshold guard, then repeats provenance and result-integrity checks before
  untouched validation.
- Exports aggregate counts, hashes, source/identity replay flags and explicit
  non-admission/assumption flags, never animal keys or row-level outcomes.

## What it does not verify

A unique canonical identity string is not proof the crosswalk is authentic,
and different animals in the same study can remain statistically dependent.
A successful software audit does **not** prove IID animal-level gain
indicators, an ecological population model, a target sampling design,
real-source accessibility, calibration chronology, or external transfer.
The explicit IID assumption must be defended independently of this code.
There is no sequential stopping or multiple-stratum Type-I error control.

This bridge is **not** the 2024/2026 BOP random forest, and the synthetic
model/reference uses a different input alignment. A synthetic positive
binomial result cannot reclassify the historical BOP mixed terminal or the
real Dryad NOT_ADMITTED gate. The source data in the associated tests are
fabricated; no GPS, altitude observations from external birds, Swiss RDS,
or original sealed outcome labels were downloaded or opened.

## Verification

Tests in tests/test_identity_checked_gain_content.py exercise the
source-trained and identity-checked full path, 9/29 count boundary, an
untouched negative validation animal after a positive calibration-content
decision, group identity reuse, roster and artifact mutations, threshold
policy tampering, forged result counts, and poisoned lazy outcome mappings.
They also enforce the one-stratum boundary before reading labels.

~~~bash
python -m pytest -q \
  tests/test_identity_checked_gain_content.py \
  tests/test_identity_checked_transport.py \
  tests/test_group_gain_content.py \
  tests/test_group_identity_gate.py \
  tests/test_managed_group_forecast_v1.py
~~~

The new dedicated workflow tests Python 3.10, 3.12 and 3.13. A GitHub
pull-request test is methods verification, not a prospective biological
experiment. The design was committed first in
docs/superpowers/specs/2026-11-22-identity-checked-content-design.md.
