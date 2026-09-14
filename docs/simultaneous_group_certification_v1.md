# Simultaneous group certification — legacy v1

> **Version boundary.** This document describes the frozen v1 provenance method. V1 standardizes each outer bootstrap deviation by one fixed bootstrap standard deviation estimated across the outer draws. It is therefore a **fixed-scale standardized max-deviation bootstrap sensitivity interval**, not a classical replicate-studentized bootstrap-t interval. Historical field names containing `max_t` are retained for receipt/API compatibility only. Prospective confirmatory analyses should use the version-2 replicate-studentized bootstrap-t route documented in `simultaneous_group_bootstrap_t_v2.md`.

`odsp.simultaneous_group_certification` audits whether a transfer-gain sign statement is supportable **simultaneously across all declared independent validation groups** under this historical v1 procedure.

The ordinary block-aware audit reports a separate interval for each group. Those intervals remain useful marginal diagnostics, but a collection of separate 95% intervals is not itself a 95% familywise statement when many groups are inspected together.

This legacy layer reports three interval families from the same block-bootstrap samples:

- ordinary marginal percentile intervals for reference;
- Bonferroni-adjusted percentile intervals as a conservative sensitivity reference;
- the historical two-sided **fixed-scale standardized max-deviation** simultaneous interval.

For each bootstrap draw, v1 computes the largest absolute group-mean deviation standardized by a group-specific bootstrap standard deviation that is fixed across outer replicates. The requested familywise quantile of that maximum becomes one common critical value. A forecast is `robust_generalizing` only if **every** historical `max_t` lower bound remains above the gain tolerance. Any unestimable group blocks the global simultaneous claim.

This distinction from genuine bootstrap-t matters empirically. The prospective v2 method recomputes the cluster ratio studentizer inside every bootstrap replicate and has a separately frozen known-null operating-characteristics qualification. V1 numerical receipts are preserved for provenance and are not retroactively reclassified.

The frozen v1 known-truth benchmark includes a deliberate multiplicity trap: all 20 groups have individually positive 95% lower bounds, yet both the historical standardized-max interval and Bonferroni simultaneous intervals cross zero. This remains useful as a sensitivity demonstration, but it is not used to establish v2 calibration.

The v1 procedure is an empirical bootstrap sensitivity audit, not an exact finite-sample theorem. Its interpretation depends on scientifically defensible independent groups and resampling blocks. It does not refit the upstream learner, repair a bad block definition, infer biological mechanism, or guarantee future distribution-shift performance.
