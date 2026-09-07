# Forecast Assessment v5: training/validation provenance gate

`odsp.forecast_assessment_v5.assess_state_forecast_v5` composes the frozen Forecast Assessment v4 with explicit per-refit training-row membership provenance.

V5 first computes and preserves a complete Forecast Assessment v4 result with the optional refit-scheme layer omitted. If no scheme layer is requested, no training-membership metadata is required and v5 preserves the base v4 certification.

When refit schemes are requested, callers must provide stable refit IDs, held-out validation-row IDs, per-scheme validation-column IDs, and the declared training-row membership for every scheme and every refit. V5 checks the declared training memberships against the held-out validation IDs before any row-alignment or refit-scheme statistics are allowed to run.

If every declared training membership is disjoint from the held-out validation target, v5 delegates unchanged to the existing Forecast Assessment v4 row-aligned scheme path. The resulting v4 certification, row-provenance result, statistical blockers, provenance blockers, and warnings are inherited without reinterpretation.

If any declared training membership directly contains a held-out validation-row ID, the provenance category is `leakage_detected`. V5 does not run the downstream v4 scheme assessment, row alignment, or refit-scheme statistics. The base v4 evidence remains available, and `training_validation_leakage` is added only as a provenance blocker. An otherwise certifiable case becomes `unavailable`; a base v4 case that was already `not_certified`, blocked, or unavailable cannot be rescued by the provenance result.

This audit validates only the caller-supplied row membership ledger. A clean ledger does not prove the complete training history, prove absence of indirect validation use through tuning or preprocessing, establish refit independence, identify the correct refit scheme, establish biological mechanism, or guarantee future distribution-shift performance. No aggregate confidence score is emitted.
