# Simultaneous group certification

`odsp.simultaneous_group_certification` audits whether a transfer-gain sign statement is supportable **simultaneously across all declared independent validation groups**.

The ordinary block-aware audit reports a separate interval for each group. Those intervals remain useful marginal diagnostics, but a collection of separate 95% intervals is not itself a 95% familywise statement when many groups are inspected together.

This layer therefore reports three interval families from the same block-bootstrap samples:

- ordinary marginal percentile intervals for reference;
- Bonferroni-adjusted percentile intervals as a conservative sensitivity reference;
- a two-sided studentized bootstrap **max-t** interval as the primary simultaneous interval.

For each bootstrap draw, ODSP computes the largest absolute standardized group-mean deviation across all estimable groups. The requested familywise quantile of that maximum becomes one common critical value. A forecast is `robust_generalizing` only if **every** max-t lower bound remains above the gain tolerance. Any unestimable group blocks the global simultaneous claim.

The frozen known-truth benchmark includes a deliberate multiplicity trap: all 20 groups have individually positive 95% lower bounds, yet both max-t and Bonferroni simultaneous intervals cross zero. This is retained rather than allowing many marginal passes to masquerade as a simultaneous guarantee.

The procedure is an empirical bootstrap audit, not an exact finite-sample theorem. Its interpretation depends on scientifically defensible independent groups and resampling blocks. It does not refit the upstream learner, repair a bad block definition, infer biological mechanism, or guarantee future distribution-shift performance.
