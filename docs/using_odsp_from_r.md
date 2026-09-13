# Use ODSP from R with reticulate

ODSP is implemented in Python, but R users can run the same endpoint-contract workflow without rewriting the method.

## 1. Install once

```r
install.packages(c("reticulate", "jsonlite"))
library(reticulate)

virtualenv_create("r-odsp")
py_install(
  packages = "odsp-niche-geometry[predict]",
  envname = "r-odsp",
  pip = TRUE
)
```

In a new R session, select the environment before importing Python modules:

```r
library(reticulate)
use_virtualenv("r-odsp", required = TRUE)
```

## 2. Write the same JSON contract

Use `examples/endpoint_contract.template.json` as the starting point. The contract must explicitly name the state, feature columns, independent group, optional stratum and fold, reference learner, comparator and training-weight policy.

For example, a camera-trap analysis might declare:

```json
{
  "schema_version": 1,
  "endpoint_id": "camera-activity-v1",
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

## 3. Run the installed contract engine from R

Calling the Python CLI entry point through `reticulate` is operating-system independent and produces the same receipt as the shell command.

```r
library(reticulate)
library(jsonlite)
use_virtualenv("r-odsp", required = TRUE)

odsp_cli <- import("odsp.cli", convert = TRUE)

status <- odsp_cli$main(c(
  "run",
  "--contract", normalizePath("endpoint.json"),
  "--out", normalizePath("endpoint.receipt.json", mustWork = FALSE)
))
stopifnot(status == 0L)

receipt <- fromJSON("endpoint.receipt.json", simplifyVector = FALSE)
receipt$result$gain_category
```

The receipt contains the group-level gains and, when a stratum is declared, the additive decomposition

```text
pooled gain = stratum shift + within-stratum context gain.
```

Switching `baseline` from `"pooled"` to `"stratum"` changes the reported comparator; it does not silently redefine the scientific roles.

## 4. Use your own model when needed

The JSON/CLI interface intentionally supports only the two bundled reference learners (`random_forest` and `multinomial_logit`). ODSP is not intended to replace an R modelling stack such as `mgcv`, `brms`, `glmmTMB`, `ranger` or a custom model.

If your R workflow already produces held-out state probabilities or log scores, keep your existing model and use the lower-level ODSP Python API for baseline comparison and independent-group scoring. The methodological requirement is that the richer and lower-information scores are evaluated on the same held-out observations under an explicitly declared independence unit.

## Troubleshooting

Check which Python R is using with:

```r
py_config()
```

For concise contract errors, use the normal runner. If you need a Python traceback while debugging, add `--debug` to the `odsp run` arguments.
