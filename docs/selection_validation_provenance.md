# Selection/final-validation provenance

ODSP has separate machinery for comparing candidate forecasts and for certifying a forecast on held-out validation rows. If the same final-validation rows are first used to choose a candidate, tune hyperparameters, select a threshold, or drive early stopping, the later final-validation result is no longer an untouched post-selection assessment.

`audit_selection_validation_provenance` provides an explicit row-identity check for that direct selection-on-validation failure mode. The caller supplies one canonical `final_validation_row_ids` sequence and a named row sequence for every declared data-driven selection stage. Typical stage names might represent candidate ranking, hyperparameter tuning, early stopping, threshold choice, or another decision that influenced the final model.

A stage whose declared rows are disjoint from final validation is `selection_validation_disjoint`. Any direct overlap makes that stage, and the overall audit, `selection_validation_leakage`. Repeated use of a development row is legal and reported; repeating one leaked final-validation row does not multiply the number of unique leaked validation rows.

Optional `expected_stage_names` can require exact declared stage coverage. The audit never emits the identities of leaked rows, never infers omitted selection history, never chooses a candidate, and never produces an aggregate confidence score.

This is a provenance check, not a statistical correction. A clean result proves only that the supplied stage memberships do not directly overlap the supplied final-validation IDs. It does not prove that the ledger is complete, that validation summaries were not consulted indirectly, that a candidate was genuinely predeclared, or that the chosen model or hyperparameters are scientifically correct.

A particularly important use is to keep ODSP's candidate-comparison outputs and final certification conceptually separate: a candidate recommendation produced from one row target should not silently be treated as if it had been selected before an independent final-validation target unless the relevant selection provenance supports that separation.
