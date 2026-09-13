# External refit-score information transfer

## Purpose

`odsp transfer-refits` is the operational route for information-transfer analyses
that must include both validation-sample uncertainty and sensitivity to an
explicit ensemble of upstream model refits.

ODSP still does not fit the models. The upstream workflow may be R, Stan, INLA,
`brms`, `mgcv`, Python or another modelling system. It exports a long table with
one record for every

```text
refit_id x held-out row_id
```

pair and one score column for every declared information level.

## Long-table layout

A minimal table looks like

```text
refit_id,row_id,site_id,visit_day,score_pooled,score_species,score_full
r000,e001,s01,d01,-1.22,-0.81,-0.70
r000,e002,s01,d02,-1.03,-0.74,-0.79
...
r001,e001,s01,d01,-1.22,-0.83,-0.91
r001,e002,s01,d02,-1.03,-0.72,-0.77
...
```

The same held-out `row_id` set must appear exactly once under every refit. ODSP
sorts refit IDs and row IDs canonically before constructing aligned score
matrices.

For a given `row_id`, the following metadata must be identical in every refit:

- independent group;
- resampling block;
- row weight.

A missing row, extra row, duplicate `(refit_id, row_id)` pair, or metadata
mismatch fails closed. This prevents a refit with a different validation sample
from being silently combined with the others.

## Contract

Start from

`examples/refit_information_transfer_contract.template.json`.

The contract declares the score semantics and strict information filtration in
the same way as `odsp transfer`, plus the refit-specific evaluation rules.

A confirmatory refit endpoint requires both

```text
filtration_frozen_before_outcome_scoring = true
refit_scheme_frozen_before_outcome_scoring = true
```

and an explicit `reference_refit_id` for traceability.

The contract deliberately requires

```text
refit_independence_assumed = false
refit_mixture_weighting = "uniform"
```

because the supplied refits are treated as an empirical sensitivity mixture, not
as independent replicates whose variance may be divided by `sqrt(R)`.

## Nested uncertainty calculation

For each Monte Carlo draw ODSP:

1. selects one supplied refit ID;
2. uses that same refit for every independent group and every information step;
3. resamples validation blocks separately within groups;
4. uses the same block draw for every information step within a group;
5. computes one global studentized max-t statistic across the full estimable
   `group x information-step` family.

The globally shared refit selection matters. Independently choosing a refit for
each group or each information step would create artificial hybrid predictors
that were never fitted upstream.

## Reported ceilings

The receipt keeps distinct:

- the point ceiling of the declared reference refit;
- the validation-block-certified ceiling of the reference refit;
- the point ceiling from every supplied refit;
- whether those refit ceilings are stable or refit-sensitive;
- the point ceiling of the uniform empirical refit mixture;
- the joint refit-aware familywise-certified ceiling.

The reference fit cannot rescue a refit-aware failure. For example, the receipt
may report

```text
reference-fit certified ceiling: species+context
refit-aware certified ceiling:   species
```

which means the fine context increment is not stable under the supplied refit
ensemble even though the named reference fit transferred it.

## CLI

```bash
odsp transfer-refits \
  --contract refit_endpoint.json \
  --out refit_endpoint.receipt.json
```

The route does not require the optional scikit-learn prediction extra.

## R workflow

Keep all model fitting in R. Generate one held-out score table per refit, add the
same stable `row_id` and the refit identifier, and concatenate the tables before
calling ODSP.

```r
refit_tables <- lapply(seq_along(fits), function(i) {
  out <- make_heldout_score_table(fits[[i]])
  out$refit_id <- sprintf("r%03d", i - 1L)
  out
})

scores <- do.call(rbind, refit_tables)
write.csv(scores, "heldout_refit_scores.csv", row.names = FALSE)

status <- system2(
  "odsp",
  c(
    "transfer-refits",
    "--contract", "refit_endpoint.json",
    "--out", "refit_endpoint.receipt.json"
  )
)
stopifnot(status == 0L)
```

ODSP checks row-set and metadata alignment after the files leave the modelling
stack, so a refit cannot silently drop difficult validation observations.

## Refit scheme boundary

The method does not prescribe how refits are generated. Depending on the
scientific design they might be repeated training resamples, prospectively
specified perturbations, repeated stochastic fits, posterior-draw-derived fitted
predictors, or another defensible ensemble.

The contract records that the scheme was frozen prospectively when a confirmatory
claim is requested, but ODSP cannot prove this provenance from the numeric score
table. The receipt therefore keeps provenance declarations separate from
properties it can validate directly.

## Claim boundary

The refit-aware interval is a conditional sensitivity statement for the supplied
empirical refit mixture plus validation-block sampling. It is not an exact
population guarantee, does not establish independence among refits, does not
claim that the ensemble spans every source of model uncertainty, and does not
turn predictive transfer into a causal effect.
