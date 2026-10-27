# BOP core methodology: outcome-blind canonical-animal admission gate v1

## Status and purpose

This is **method development**, not an additional BOP/Dryad empirical
endpoint. Earlier BOP methodological PRs #274–#278 have been merged into
ODSP main with the original biological BOP result unchanged:
**27/30** individuals with positive held-out RF log-score gain, **30/30**
Brier improvement and a conservative **mixed** overall terminal.

The current ODSP cross-source method freezes the training model, test
probabilities and independent groups. It uses source-prefixed identifiers
such as \`BOP:animal5\` and \`DRYAD:animal5\` to prevent software collisions.
That is **not enough** to guarantee the two names represent different
tagged biological individuals, different tag deployments, or independent
study populations.

The new generic \`odsp.group_identity_gate\` supplies an
**outcome-blind individual identity + group-rank sample-size gate**.
It does not read, fetch or compute altitude, timestamps, GPS tracks,
predictor scores or calibration/validation outcomes.

## Input contract

A *frozen* \`FrozenGroupForecastPlan\` plus **actual frozen predictor and
reference artifact bytes** are required. The existing
\`plan.assert_unchanged\` must pass before group admission begins.

Provide exactly one metadata record per intended training, target
calibration or untouched target validation **individual** with these
five fields and no others:

| Field | Meaning |
|---|---|
| \`group_id\` | Exact group name already frozen in the forecast plan |
| \`entity_key\` | Canonical animal identity **across** data sources and tag deployments, from an externally prepared identity crosswalk |
| \`stratum\` | Frozen taxon / inference population |
| \`source\` | Declared dataset/provider for each role |
| \`study_cluster\` | Study or sampling cluster label, useful for exposing shared sources |

Raw animal IDs and crosswalk source content are kept in the caller's
process only. **The public output contains aggregates, role source labels,
species/stratum names and the original forecast-plan SHA256—no group IDs,
animal identity keys, study-cluster strings, GPS or outcomes.** The
software cannot independently authenticate who generated an
\`entity_key\`. An incorrect crosswalk is still incorrect if software
reports a passing count.

The API rejects:
- any missing/duplicated/extra group or a source-role mismatch;
- any same canonical animal identity appearing in two frozen groups,
  including one animal with different source prefixes, reused tags
  or multiple deployments;
- changing the model, reference or frozen forecast probabilities;
- inconsistent species labels between metadata and forecast rows;
- any extra field, including altitude, timestamp, context, outcomes,
  scores, row weights, locations or hidden source identity mappings.

## Rank admissibility—necessary, not sufficient

For each independent taxon/population stratum, count training animals
\`n_train\`, calibration animals \`n_cal\` and separate untouched validation
animals \`n_val\`. The prespecified finite-sample one-sided rank is

\[
k=\lfloor (n_{\mathrm{cal}}+1)\alpha\rfloor.
\]

The minimum *nonvacuous* group rank requires \`k>=1\`,
\`n_val>=1\` and at least two training individuals within that
stratum for the transparent categorical model. For \`alpha=0.10\`,
therefore **9 independent calibration animals plus at least 1
different validation animal per stratum** are necessary. Pooling animals
over species cannot turn a stratum with eight groups into a passing
stratum.

The gate returns one of:

- \`HOLD_IDENTITY_EVIDENCE_UNVERIFIED\` — caller did not declare a
  defensible independently prepared cross-study identity crosswalk;
- \`HOLD_SOME_STRATA_HAVE_VACUOUS_RANK\` — at least one stratum has
  insufficient training/calibration/validation animals;
- \`COUNT_GATE_PASSED_EXCHANGEABILITY_NOT_PROVED\` — unique supplied
  canonical IDs and count conditions pass; **no outcome access or
  biological generalization claim is authorized**.

A passing count cannot establish independent ecological populations,
target-group calibration/validation exchangeability, observation
process compatibility, availability of model predictors, or a positive
future gain. Overlapping study clusters are reported as **counts** to
make clustering visible, not used to declare either validity or failure.

## Usage with an already frozen forecast plan

\`\`\`python
from odsp.group_identity_gate import audit_frozen_group_identity_support

audit = audit_frozen_group_identity_support(
    plan,
    training_metadata=training_individual_metadata,
    calibration_metadata=calibration_individual_metadata,
    validation_metadata=validation_individual_metadata,
    model_artifact=frozen_model_bytes,
    reference_artifact=frozen_reference_bytes,
    expected_source_by_role={
        "training": "BOP",
        "calibration": "DRYAD",
        "validation": "DRYAD",
    },
    group_identity_attestation="unverified",
)
print(audit.as_public_dict())
\`\`\`

The explicit attestation option is either
\`unverified\`, \`synthetic_known_truth\`, or
\`externally_attested_identity_crosswalk\`; **even the last option
is a caller statement, not evidence automatically checked by ODSP**.
A properly documented real-data workflow would need to link this
statement to an independently audited source/identity roster with
source checksums and a pre-outcome freeze.

## Scope of actual BOP / Dryad data

- Original BOP: 30 evaluated birds, mixed; no reanalysis.
- BOP 2026 same-study reference version: 10 newly seen ID candidates
  spread across species, largest six in one species. The already
  closed \`NO_WITHIN_STRATUM_NEW_GROUP_RANK_SUPPORT\` remains closed.
- Schaub 2026 Dryad: original RF temperature missing, rounded GPS,
  animal-identity overlap unknown. The source stays \`NOT_ADMITTED\`.
- The integrated 24-world synthetic common-input model was independently
  verified and does not claim observed Dryad transfer.

This new method answers a different, unavoidable preflight question:
**are there enough genuinely distinct candidate animals in the frozen
training/calibration/validation roles to even attempt the specified
inference?** It intentionally cannot answer whether real animal gains
will be positive or satisfy the exchangeability assumption.

The frozen method/source/biological receipts remain untouched. This
module is a small continuation of the merged ODSP BOP core, not another
standalone ecological paper or synthetic experiment.
