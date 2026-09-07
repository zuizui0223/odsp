# Forecast Assessment v4: provenance-aware scheme certification

`odsp.forecast_assessment_v4.assess_state_forecast_v4` is a thin composition layer over the frozen Forecast Assessment v3 result.

V4 first computes and preserves the complete v3 assessment with the v3 refit-scheme layer omitted. That base object is never rewritten. When caller-declared refit schemes are supplied, V4 additionally requires one canonical validation-row key sequence and a row-key sequence for every scheme's gain-matrix columns.

The row-key layer is evaluated before scheme statistics:

- exact row alignment leaves a scheme matrix untouched;
- the same unique row set in another order is restored to canonical order using the verified permutation;
- missing, extra, or duplicated row keys produce `row_mismatch`, and the refit-scheme statistical audit is not run.

After successful alignment, V4 reuses the existing frozen v3 scheme-certification summary on the aligned scheme audit. This means scheme-robust generalization, scheme sensitivity, non-generalization and unavailable scheme evidence retain the same decision semantics as Forecast Assessment v3.

A row mismatch is deliberately different. It is a provenance failure, not a weak or uncertain statistical result. For an otherwise admitted/certifiable base assessment, requested scheme evidence with mismatched rows makes V4 certification `unavailable` and records `heldout_row_mismatch` in `provenance_blocking_reasons`. It does not fabricate `refit_scheme_uncertain` or another statistical blocker. A v3 result that is already `not_certified` remains `not_certified`; provenance failure cannot rescue it.

If the scheme layer is omitted entirely, V4 preserves the base v3 certification. Block-definition sensitivity and environmental novelty remain warnings rather than provenance gates.

Row-key consistency does not prove that validation rows were truly untouched, establish train/test separation or independence, validate the row keys themselves, identify the correct refit scheme or block definition, establish biological mechanism, or provide a probability of correctness. No aggregate confidence score is emitted.
