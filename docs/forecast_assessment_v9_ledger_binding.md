# Forecast Assessment v9: evaluation-ledger binding

Forecast Assessment v9 is a provenance composition layer over the frozen Forecast Assessment v8 path. It adds no statistical estimand and changes no v8 decision rule.

## Why this layer exists

V8 can separately audit a final-evaluation artifact ID and a SHA-256 content digest. Those two ledgers are useful only if they describe the same accessed artifacts. V9 optionally requires a caller-supplied artifact-ID → SHA-256 manifest and checks the two ledgers against that manifest before the full v8 path is allowed to run.

The fail-closed order is therefore:

1. ID↔digest ledger binding,
2. exact-content provenance,
3. final-artifact-ID access provenance,
4. selection/final-validation provenance,
5. training/final-validation provenance,
6. held-out row alignment,
7. refit-scheme statistical sensitivity.

A binding mismatch produces provenance reason `evaluation_ledger_binding_mismatch` and suppresses the full downstream v8 assessment. It is not represented as weak statistical evidence.

## Inputs

Binding is optional. When `artifact_digest_by_id` is omitted, ordinary v8 behavior is preserved. When it is supplied, the caller must also supply the final artifact ID, final digest, stage-wise artifact-ID access ledger and stage-wise digest access ledger. Optional expected binding stage names can require exact stage coverage.

The binding audit checks only internal consistency of supplied declarations. It does not hash files automatically, reconstruct missing ledgers, or infer unlogged accesses.

## Important consequence

Under a consistent binding, direct access to the final artifact ID also implies access to its exact final digest. Because content provenance is evaluated before artifact-ID provenance in v8, a direct final-ID reuse is normally intercepted first as exact-content leakage. This is expected precedence, not loss of information.

## Claim boundary

A clean binding does not prove that the manifest is true or complete, that access history is complete, that predeclaration was genuine, or that differently encoded but semantically equivalent copies were not consulted. It does not identify the correct model, add confidence, establish biological mechanism, or guarantee performance under future distribution shift.

Frozen N2-MEE v4 submission artifacts and closed empirical endpoints remain untouched.
