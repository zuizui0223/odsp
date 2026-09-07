# Refit training/validation provenance

`odsp.refit_training_validation_provenance.audit_refit_training_validation_provenance` checks whether caller-declared training memberships for model refits contain any of the rows used for final validation.

The caller supplies one unique canonical `validation_row_ids` sequence and, for every named refit scheme, a mapping from stable refit IDs to the row IDs used to train that refit. Refit IDs follow the same string canonicalization used by ODSP's existing model-refit uncertainty layer.

The audit is intentionally simple and fail-closed:

- if every declared refit training membership is disjoint from validation, the category is `training_validation_disjoint`;
- if any declared training membership contains one or more validation rows, the category is `leakage_detected`;
- repeated training rows are allowed because bootstrap resampling can legitimately repeat observations;
- repeating the same leaked validation row many times does not multiply the unique leaked-row count, although duplicate training-row counts are retained;
- if expected scheme/refit IDs are supplied, provenance declarations must cover exactly those schemes and refits.

The result reports overlap counts by refit and scheme, the number of affected schemes/refits, and the maximum overlap in one refit. It deliberately does not emit the actual overlapping row IDs.

This layer does not reconstruct training membership from fitted models, prediction values, gain matrices, hashes, or row contents. A disjoint result therefore means only that the supplied memberships are internally consistent with train/validation separation. It does not prove that the declarations exhaust the true fitting history, that validation information was never used indirectly for tuning or selection, that refits are independent, or that the chosen resampling scheme is scientifically correct.

Use this provenance audit before interpreting model-refit or refit-scheme sensitivity when stable row identities are available. Statistical transfer categories remain separate evidence. No aggregate confidence score is emitted.
