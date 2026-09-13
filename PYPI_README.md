# ODSP

ODSP is a Python toolkit for **state-resolved ecological prediction** and independent transfer evaluation.

It is designed for a specific layer of an ecological workflow: you bring a probabilistic model or use one of the reference learners, explicitly declare the ecological state, predictors, independent groups, folds, strata and baseline, and ODSP reports held-out predictive gain without silently pooling conflicting groups.

A central use case is separating a total gain into a lower-information stratum shift and a within-stratum contextual component:

```text
G_pooled = G_stratum_shift + G_context_within_stratum
```

This distinction prevents a positive pooled-comparator result from being misread as positive within-stratum contextual prediction.

## Install

For the executable event-table workflow and reference learners:

```bash
pip install "odsp-niche-geometry[predict]"
```

Core information-theoretic functionality without scikit-learn can be installed with:

```bash
pip install odsp-niche-geometry
```

Python 3.10–3.13 are tested.

## Run an endpoint contract

Start from the shipped contract template and declare the scientific roles explicitly:

```json
{
  "schema_version": 1,
  "endpoint_id": "my-endpoint",
  "data": {"path": "events.csv", "format": "csv"},
  "columns": {
    "state": "activity_state",
    "features": ["temperature", "moonlight", "ndvi"],
    "group": "site_id",
    "stratum": "species",
    "fold": "year",
    "weight": null
  },
  "model": {
    "kind": "random_forest",
    "random_state": 20260913,
    "parameters": {"n_estimators": 500, "min_samples_leaf": 10}
  },
  "baseline": "pooled",
  "training_weight_policy": "equal_stratum_equal_group",
  "gain_tolerance": 0.0
}
```

Then run:

```bash
odsp run --contract endpoint.json --out endpoint.receipt.json
```

The receipt records SHA256 hashes of the contract and input data, the declared scientific roles, model specification, group-level held-out gains, the pooled → stratum → model decomposition when available, and the conservative group-sign category (`generalizing`, `non_generalizing`, or `mixed`).

Contract violations fail closed. ODSP does not infer an independence unit, fold, stratum, baseline, weighting policy or learner from column names.

## What the CLI does and does not model

The contract CLI currently provides two reference learners:

- random forest;
- multinomial logistic regression.

These are convenience models, not the methodological contribution. If you already have a probabilistic learner, use the Python API to supply predicted state probabilities or log scores and retain ODSP as the baseline declaration, decomposition and independent-group scoring layer.

## Worked example

`examples/penguins/` contains a public-data portability vignette using the Palmer Penguins dataset. The example is deliberately separate from the empirical systems used in the associated manuscript and runs end-to-end through the same installed `odsp` command.

## R users

R users can install the Python package and call the contract runner through `reticulate`. See `docs/using_odsp_from_r.md` for a one-page setup and example.

## Scope

ODSP is **not** a replacement for a full SDM, movement-model or machine-learning stack. It is a model-agnostic evaluation layer for asking whether richer ecological-state information improves independent probabilistic prediction relative to a declared lower-information comparator.

The package also contains lower-level tools for multidimensional niche thickness, temporal/vertical state representations, distributional gain, prediction uncertainty and related validation analyses.

## License

MIT.
