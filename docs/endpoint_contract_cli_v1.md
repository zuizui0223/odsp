# Endpoint contract CLI

ODSP can run the generic event-table workflow from a JSON contract instead of an endpoint-specific Python script.

The command is:

```text
odsp run --contract endpoint.json --out endpoint.receipt.json
```

A contract explicitly declares the state column, feature columns, independent group, optional stratum and fold, model, baseline, and training-weight policy. Start from `examples/endpoint_contract.template.json`.

Version 1 accepts CSV files or JSON arrays of row objects. The CLI intentionally exposes only two bundled reference learners: random forest and multinomial logistic regression. These are convenience models, not a replacement for a user's modelling stack. Custom probabilistic learners should use the Python API and retain ODSP as the explicit comparator, decomposition and grouped-scoring layer.

The supported baselines are pooled and stratum-specific training marginals. The receipt records the contract and data SHA256 values, input row count, declared scientific roles, model specification, independent-group scores, additive baseline decomposition when a stratum is declared, and the terminal sign category.

No scientific role is inferred from a column name. Unknown contract fields are rejected. The command does not choose a baseline, weighting policy, learner, fold, or independence unit after seeing the result, and running a contract does not reopen any frozen empirical endpoint.

Expected input and configuration failures are printed as a single `odsp: error: ...` line and return exit code 2. Add `--debug` to `odsp run` when a full Python traceback is needed during development.

R users can call this same contract runner through `reticulate`; see `docs/using_odsp_from_r.md`.
