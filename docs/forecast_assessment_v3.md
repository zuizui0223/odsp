# Forecast Assessment v3

`odsp.forecast_assessment_v3.assess_state_forecast_v3` preserves the complete Forecast Assessment v2 result and optionally adds refit-scheme sensitivity as a further formal extended-certification gate.

The scheme layer compares multiple caller-declared refitting/training-resampling ensembles (for example block-bootstrap refits, fold refits, or repeated seeded refits) on the same untouched validation target. Each scheme is evaluated by the existing model-refit transfer uncertainty audit. V3 does not infer which scheme is correct.

Certification is fail-closed:

- v2 `not_certified` or `unavailable` cannot be rescued by the scheme layer;
- `scheme_robust_generalizing` passes the scheme gate;
- `scheme_sensitive`, stable uncertainty, mixed/non-generalizing results make v3 `not_certified`;
- a declared unavailable scheme makes v3 `unavailable`;
- if the v2 formal layers were omitted, a robust-generalizing scheme audit can itself provide the v3 formal certification;
- if the scheme layer is omitted, the v2 certification status is preserved exactly.

Block-definition sensitivity and environmental novelty remain warnings, not formal scheme gates. The full v2 result is retained as `base_v2_assessment`; scheme evidence cannot rewrite its validation or deployment history.

No scalar aggregate confidence score is emitted. Scheme stability is conditional on the declared refit designs, validation groups and blocks; it is not an exact population guarantee or evidence that the declared training-resampling schemes span the true training-process uncertainty.
