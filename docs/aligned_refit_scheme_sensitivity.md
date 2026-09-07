# Row-aligned refit-scheme sensitivity

`audit_aligned_refit_scheme_sensitivity` composes two already-separated ODSP concerns: machine-checkable held-out row provenance and the frozen refit-scheme sensitivity audit.

The caller supplies one canonical `validation_row_ids` sequence matching `groups`, `blocks`, and optional validation weights. Every refit scheme also supplies the row-key sequence corresponding to its gain-matrix columns.

If every scheme contains the same unique row set, the alignment layer establishes the exact source-to-base permutation. Schemes already in canonical order are left untouched; reordered schemes have only their validation-row columns permuted. The existing `audit_refit_scheme_sensitivity` decision rule then runs on the aligned matrices without modification.

If any scheme has a missing, extra, or duplicate row key, the result is `status="row_mismatch"`, `statistical_audit_run=false`, and `scheme_audit=null`. ODSP does not drop, impute, nearest-match, or infer rows from gain values.

This composition does not strengthen the underlying statistical guarantee. Matching declared row keys does not prove that validation rows were untouched, that refits are independent or training-only, that the block definition is correct, or that any refit scheme is scientifically correct. The existing scheme categories retain exactly their original interpretation, and no aggregate confidence score is created.
