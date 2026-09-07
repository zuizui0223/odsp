# Forecast Assessment v4

`odsp.forecast_assessment_v4.assess_state_forecast_v4` adds machine-checked held-out row provenance in front of the Forecast Assessment v3 refit-scheme gate.

Forecast Assessment v2 evidence is computed once and retained as `base_v2_assessment`. When no refit-scheme layer is requested, v4 requires no row identifiers and reconstructs the ordinary v3 omitted-scheme result exactly.

When refit schemes are declared, the caller must provide one canonical `validation_row_ids` sequence and row identifiers for every scheme's gain-matrix columns. The validated aligned refit-scheme layer checks those identifiers before scheme statistics are used.

If alignment is exact or reorderable, only verified column permutations are applied. V4 then combines the preserved v2 assessment with the existing aligned scheme audit through the existing v3 certification rule. The resulting `v3_assessment` is required by the frozen benchmark to be dictionary-identical to a direct Forecast Assessment v3 run on canonical rows.

If any declared scheme has missing, extra, or duplicated validation-row identifiers, v4 does not manufacture a weaker v3 result. The scheme-aware `v3_assessment` is withheld, `base_v2_assessment` remains available, and the v4 decision trace adds `heldout_row_mismatch`. An otherwise certifiable assessment becomes `unavailable`; an already blocked or not-certified v2 assessment cannot be rescued by the provenance failure.

Row-key agreement is provenance bookkeeping, not statistical evidence. It does not prove that validation rows were untouched, establish train/test separation, establish refit independence, identify the correct refit scheme or block definition, identify biological mechanism, or guarantee future distribution-shift performance. No aggregate confidence score is emitted.
