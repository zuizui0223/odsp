# Bootstrap inference version boundary

ODSP now has two historically distinct simultaneous-bootstrap families. They must not be described as the same inferential method.

## Version 1: frozen fixed-scale standardized max-deviation sensitivity

The original v1 modules compute outer bootstrap estimates and one bootstrap standard deviation per cell. Every outer deviation is then divided by that **same fixed cell standard deviation** before the maximum standardized deviation is formed.

That construction is useful as a multiplicity-aware sensitivity analysis, but the studentizer is not recomputed inside each outer bootstrap replicate. For that reason ODSP no longer describes v1 as a classical bootstrap-t procedure.

Historical APIs and receipts keep names such as `max_t_*` for provenance compatibility. Those names are not evidence that replicate-specific studentization was performed.

The v1 family includes the historical implementations underlying:

- `simultaneous_group_certification.py`;
- `predictive_resolution_certification.py`;
- `information_lattice.py` familywise certification;
- `shared_block_certification.py`;
- the validation-block component of the historical refit-sensitivity modules.

Frozen empirical endpoints are **not** rerun or reclassified because of this terminology correction.

## Version 2: prospective replicate-studentized cluster bootstrap-t

Version 2 recomputes both the ratio-of-sums estimate and its cluster influence standard error inside every bootstrap replicate. The simultaneous statistic is therefore based on

```text
max_j |theta*_bj - theta_hat_j| / SE*_bj
```

with one maximum over the full predeclared estimable family.

The v2 family includes:

- `audit_simultaneous_group_certification_v2` for independent groups and one gain;
- `certify_independent_group_contrasts_v2` for independent group × contrast families;
- v2 information-filtration and information-lattice wrappers;
- `certify_shared_block_gains_v2` for balanced groups paired on the same exchangeable validation blocks.

Known-global-null operating-characteristics panels are frozen separately for the relevant designs. Those simulations support only their declared sampling designs and do not establish arbitrary-dependence or model-refit guarantees.

## Refit ensembles remain sensitivity analyses

An empirical collection of upstream refits is not automatically an independent probability sample. Selecting one supplied refit per Monte Carlo draw is therefore retained as **refit sensitivity**, not relabelled as a 95% bootstrap-t confidence guarantee. The validation-sample component and the upstream-refit sensitivity component should be reported separately.

## Reporting rule

For new work:

1. declare whether validation groups are independent or paired on a common exchangeable block set;
2. use the corresponding v2 bootstrap-t route for validation-sample simultaneous inference;
3. state the exact simultaneous family (groups, steps, or lattice edges) before outcome inspection;
4. report upstream-refit analysis separately as sensitivity unless a defensible sampling model for fits has been predeclared;
5. never use positive pooled gain, a favorable path, a reference fit, or an order-averaged Shapley summary to override a failed predeclared cell.
