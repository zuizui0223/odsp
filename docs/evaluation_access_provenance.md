# Final-evaluation access provenance

`audit_evaluation_access_provenance` checks a caller-supplied ledger of evaluation artifacts consulted during pre-final decision stages. This closes a different gap from row-overlap provenance: selection can reuse a final-validation score, ranking, threshold result, or other evaluation artifact even when the rows used by the selection procedure are not themselves listed as final-validation rows.

The caller names one canonical final-evaluation artifact and declares the artifacts accessed by each pre-final stage. If the final artifact appears in any declared stage, the audit reports `final_evaluation_access_leakage`. If it does not appear, the result is `final_evaluation_not_accessed_in_declared_pre_final_stages`.

Repeated accesses are legal to represent and are counted. The serialized result never emits artifact identities, never infers unlogged accesses, never assumes that the ledger is complete, never chooses a candidate, and emits no aggregate confidence score. Optional expected stage names can require exact declared stage coverage.

A clean result is deliberately narrow: it proves only that the supplied ledger contains no direct reuse of the supplied final-evaluation artifact. It does not prove complete access history, absence of indirect information transfer, genuine predeclaration, statistical validity, or biological mechanism.
