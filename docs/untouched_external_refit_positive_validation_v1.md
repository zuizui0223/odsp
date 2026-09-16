# Untouched external refit-positive validation v1

## Purpose

`odsp transfer-refits-external` is the confirmatory route for a predeclared
one-sided positive-transfer question when the final evaluation dataset was kept
outside model fitting, refit generation, model/filtration selection, threshold
selection and score-rule selection.

It combines two different uncertainty statements without conflating them:

1. **validation-sample uncertainty within each fitted refit** — handled by the
   calibrated one-sided familywise bootstrap-t lower bound;
2. **upstream-refit uncertainty** — handled as an empirical sensitivity
   intersection: every supplied refit must support a step before the consensus
   ceiling advances.

The refit ensemble is not treated as an IID probability sample, and ODSP does not
emit a refit-population confidence interval.

## Pre-outcome freeze artifact

The runtime contract must point to a concrete freeze-manifest file and declare its
SHA256. ODSP recomputes that hash and rejects a mismatch. The contract also stores
`frozen_at_utc` and the declared first time external outcomes were accessed;
`frozen_at_utc` must be strictly earlier.

The freeze declarations require, before external-outcome access:

- upstream models frozen;
- supplied refit ensemble frozen;
- information filtration frozen;
- scoring rule frozen;
- gain tolerance frozen;
- directional alternative (`greater`) frozen.

The external rows must also be declared disjoint from development data and unused
for model fitting, refit generation, model selection or filtration selection.
External outcomes must be declared unused for threshold/score-rule selection or
any other development decision.

These are provenance declarations. ODSP verifies their internal consistency,
manifest hash and timestamp ordering; it cannot independently prove the historical
fact that a researcher never viewed an outcome earlier. The receipt states that
boundary explicitly.

## Input table

The score table is long-form with one row per `refit_id × row_id`. Every refit
must contain exactly the same external row IDs, and the same row must carry
identical group, block and weight metadata in every refit. Every information level
uses one row-wise score column on those same external outcomes.

## Decision rule

For each supplied refit, ODSP runs the one-sided positive-transfer certification.
A step passes the refit-sensitive external validation only if every supplied refit
is `robust_generalizing`. The ceiling is non-skippable: a later positive step
cannot rescue a failed earlier step. The declared reference refit cannot override
a consensus failure.

## Command

```bash
odsp transfer-refits-external --contract external_validation.json --out receipt.json
```

The receipt contains SHA256 hashes for the contract, external score table and
freeze manifest, the full normalized external-validation declarations, and the
refit-sensitive directional result.
