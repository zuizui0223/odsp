# External-score information transfer

## Purpose

`odsp transfer` applies the ODSP information-transfer rules **after** model fitting.
It does not require an ODSP learner. An upstream analysis may use `brms`, INLA,
Stan, `mgcv`, `glmmTMB`, `ranger`, scikit-learn, a neural network, or any other
system that can export one held-out row-wise predictive score for every declared
information level.

The separation is deliberate:

```text
upstream modelling stack
        |
        | held-out row scores
        v
explicit information filtration
        |
        v
independent-group transfer increments
        |
        v
joint group x step max-t certification
        |
        v
non-skippable transfer ceiling
```

ODSP therefore evaluates an inferential claim about **transfer of added
information**, not allegiance to a modelling framework.

## Input table

Every row represents the same held-out observation at every information level.
A minimal table is

```text
row_id,site_id,visit_day,score_pooled,score_species,score_full
r001,s01,d01,-1.31,-0.84,-0.75
r002,s01,d02,-0.93,-0.72,-0.81
...
```

`row_id` is mandatory and must be unique. The score columns are attached to the
same row, so a level cannot silently change the evaluation sample.

The contract template is
`examples/information_transfer_contract.template.json`.

## Score contract

ODSP uses the convention **larger score = better prediction**. Lower-is-better
quantities such as deviance or negative log loss must be transformed before they
are supplied. The contract refuses `lower_is_better` rather than guessing the
sign.

All levels must use the same scoring rule. For logarithmic scores, the contract
also requires `common_reference_measure=true`. This matters for continuous
states: log densities with different reference measures are not directly
comparable even when they were produced by valid models.

`score.kind="other_proper"` allows another proper scoring rule such as negative
Brier score. The held-out telescoping decomposition remains valid, but the
conditional-mutual-information interpretation is specific to log score.

## Evaluation declarations

Several conditions cannot be reconstructed from a finished score table, so the
contract makes them explicit instead of silently assuming them:

- the predictions are held out;
- every information level is evaluated on the same rows;
- the held-out outcome was not used to produce or select its prediction;
- for a confirmatory endpoint, the information filtration was frozen before
  outcome scoring;
- if no resampling block is supplied, row independence is explicitly asserted.

These are declarations, not facts that ODSP can empirically prove from the score
columns. The receipt therefore records
`contract_declarations_empirically_verified_by_odsp=false`.

A descriptive analysis may set `analysis_mode="descriptive"` and record that the
filtration was not prospectively frozen. It will then be marked as not
confirmatory-eligible rather than being disguised as a prospective endpoint.

## Information filtration

Each score level declares the information available to its predictor. For
example:

```text
pooled          {}
species         {species}
species_context {species, temperature, moonlight, ndvi}
```

The sets must be strictly nested. ODSP rejects

```text
{species} -> {site}
```

because information was discarded, and it rejects two different algorithms with
identical information sets because that is a model comparison rather than an
information-addition step.

This nesting condition is not claimed as a new scoring-rule theorem. Proper-score
chain decompositions over nested information sets already exist in the scoring
literature. ODSP uses strict nesting as a prerequisite for the stronger ecological
transfer interpretation.

## Point and certified results

For each independent group, ODSP returns adjacent held-out score gains and total
gain. It then reports a point transfer ceiling: the finest level reached by a
consecutive run of positive increments.

The certification layer resamples caller-declared blocks within groups. The same
bootstrap draw is used for every step within a group, preserving cross-step
covariance. One studentized max-t critical value is then formed across the full
estimable **group x step** family.

The certified ceiling advances only while each successive step is
`robust_generalizing` across every independent group. A positive total gain, or a
later positive step, cannot jump over a failed or uncertain earlier step.

## CLI

```bash
odsp transfer --contract endpoint.json --out endpoint.receipt.json
```

Expected input/configuration failures produce a one-line error and exit code 2.
Use `--debug` only when a Python traceback is needed.

## R workflow

The model can remain entirely in R. After generating out-of-fold or otherwise
independently held-out predictive scores, write one CSV containing the row ID,
independence unit, resampling block, optional weight and one score column per
information level. Then call the installed ODSP CLI through `system2()` or
`reticulate`.

For example:

```r
write.csv(score_table, "heldout_scores.csv", row.names = FALSE)
status <- system2(
  "odsp",
  c("transfer", "--contract", "endpoint.json", "--out", "receipt.json")
)
stopifnot(status == 0L)
receipt <- jsonlite::read_json("receipt.json", simplifyVector = FALSE)
receipt$certified_result$certification$certified_transfer_ceiling
```

No R model object is imported into ODSP and no model is refitted by ODSP.

## Claim boundary

The transfer receipt certifies validation-sample uncertainty conditional on the
supplied predictive scores. It does **not** automatically include uncertainty due
to refitting or selecting the upstream learner. If learner-refit uncertainty is
scientifically material, it must be propagated separately rather than inferred
from the block bootstrap.
