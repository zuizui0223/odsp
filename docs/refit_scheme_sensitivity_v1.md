# Refit-scheme sensitivity

`odsp.refit_scheme_sensitivity.audit_refit_scheme_sensitivity` compares model-refit-aware transfer conclusions across multiple caller-declared refitting or training-resampling schemes evaluated on the same untouched validation rows.

Examples of distinct schemes include block bootstrap refits, fold refits, or repeated seeded refits. ODSP does **not** infer which scheme is correct. Each scheme is first evaluated with the existing model-refit transfer uncertainty audit, retaining its own reference-fit category, refit-sign stability, nested max-t interval and availability state.

The cross-scheme result is fail-closed:

- every declared scheme `robust_generalizing` -> `scheme_robust_generalizing`;
- every declared scheme `robust_non_generalizing` -> `scheme_robust_non_generalizing`;
- any declared scheme `unavailable` -> `unavailable`;
- different available refit-aware categories -> `scheme_sensitive`;
- an identical non-robust category is reported with a `stable_` prefix.

A robust scheme cannot rescue a fragile or unavailable scheme. Scheme stability is a sensitivity statement over the declared designs, not a guarantee that those designs span the true training-process uncertainty. No automatic scheme selection or aggregate confidence score is emitted.
