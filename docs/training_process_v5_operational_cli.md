# Training-process v5 operational CLI

The qualified training-process v5 method is now reachable through one
operational command namespace without adding a new top-level ODSP command.

The CLI is **not** a new statistical surface. It delegates to the same frozen
Python functions and preserves their non-overwriting and fail-closed behavior.

## 1. Freeze the training process

```bash
odsp experimental training-process freeze \
  --plan training-process-plan.json \
  --manifest-out training-process-freeze.json \
  --out training-process-freeze-receipt.json
```

This freezes the training roster, resampling family, refit IDs, resample/fit
seeds, implementation artifacts and bootstrap membership digests.

## 2. Generate the frozen refits

```bash
odsp experimental training-process generate \
  --plan managed-generation-plan.json \
  --output-root generated-refits \
  --receipt-out managed-generation-receipt.json \
  --out generation-command-receipt.json
```

ODSP reconstructs each frozen membership, verifies its digest, runs the frozen
argv with `shell=False`, and hashes all generated model artifacts.

## 3. Freeze untouched-external design before outcomes

```bash
odsp experimental training-process external-freeze \
  --plan external-freeze-plan.json \
  --manifest-out external-freeze.json \
  --receipt-out external-freeze-receipt.json \
  --out external-freeze-command-receipt.json
```

The freeze binds external row ID, group, block and weight metadata, the training
process and generated models, scoring code/runtime, information levels, score
semantics and the qualified endpoint identity. Outcome bytes are not part of
this freeze input.

## 4. After declared outcome access, derive scores through managed execution

```bash
odsp experimental training-process external-score \
  --freeze-manifest external-freeze.json \
  --freeze-receipt external-freeze-receipt.json \
  --external-roster external-roster.csv \
  --external-roster-format csv \
  --managed-generation-receipt managed-generation-receipt.json \
  --generated-model-root generated-refits \
  --validation-data external-data.csv \
  --output-root external-score-runs \
  --score-bundle-out external-score-bundle.json \
  --scoring-receipt-out managed-scoring-receipt.json \
  --out external-score-command-receipt.json
```

The score tensor is derived by ODSP-managed scoring. The primary external route
does not accept an arbitrary caller-supplied score tensor.

## 5. Run the qualified untouched-external endpoint

```bash
odsp experimental training-process external-run \
  --contract external-run.json \
  --out external-result.json
```

The external-run contract contains file locations plus the declared first
external-outcome access timestamp. It does not repeat row/group/block/weight or
refit IDs; those are reconstructed from frozen files before the canonical
endpoint is invoked.

A minimal contract has this shape:

```json
{
  "schema_version": 1,
  "external_freeze_manifest_path": "external-freeze.json",
  "external_freeze_receipt_path": "external-freeze-receipt.json",
  "managed_scoring_receipt_path": "managed-scoring-receipt.json",
  "score_bundle_path": "external-score-bundle.json",
  "validation_data_path": "external-data.csv",
  "external_roster": {
    "path": "external-roster.csv",
    "format": "csv"
  },
  "training_process_manifest_path": "training-process-freeze.json",
  "managed_generation_receipt_path": "managed-generation-receipt.json",
  "training_roster_path": "training-roster.csv",
  "external_outcomes_first_accessed_at_utc": "2026-10-06T00:00:00Z"
}
```

The canonical inference surface remains
`odsp.training_process_untouched_external_v5.run_untouched_external_training_process_v5`.
The active evidence registry and statistical qualification are unchanged by this
CLI layer.
