# Training-process v5 templates

These templates instantiate the qualified c2 independent-filtration
training-process route without changing its statistical method.

Use them in this order:

1. `training-process-plan.template.json`
2. `managed-generation-plan.template.json`
3. `external-freeze-plan.template.json`
4. run managed external scoring through the CLI
5. `external-run.template.json`

The pre-outcome external roster must contain exactly:

```text
row_id,group_id,block_id,sample_weight
```

Do not place external outcomes or score columns in that roster. The outcome-bearing
validation data is supplied only after the external freeze is complete and the
first-access timestamp is recorded.

The minimum qualified scope is eight independent training-process refits and
eight positive-mass validation blocks per group. More are allowed; changing to
c4, paired/shared-block, or lattice process inference is not qualified by these
templates.
