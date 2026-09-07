# Forecast Assessment v6: selection/final-validation provenance gate

`odsp.forecast_assessment_v6.assess_state_forecast_v6` composes the frozen Forecast Assessment v5 result with the selection/final-validation provenance audit.

V6 addresses a different leakage route from v5. V5 can check whether declared refit training rows directly overlap the final validation target. V6 checks whether the same final validation rows were consulted earlier during data-driven decision stages such as candidate ranking, hyperparameter tuning, early stopping, threshold choice, or another caller-declared selection stage.

The ordering is fail-closed:

1. compute and preserve the scheme-omitted v5 base evidence;
2. if a selection ledger is supplied, compare every declared selection-stage row identity with the canonical final-validation row IDs;
3. if any direct overlap is found, stop before the full v5 training-provenance, held-out alignment, and refit-scheme path;
4. only when selection provenance is clean may the ordinary v5 path run unchanged.

Selection leakage is reported as provenance failure, not model uncertainty. An otherwise certifiable result becomes provenance `unavailable`; a prior statistical `not_certified` result is not rescued. The downstream v5 assessment is absent when selection leakage blocks execution.

If the selection layer is omitted, V6 preserves the ordinary v5 result and certification. Clean selection provenance also preserves downstream v5 behavior: direct training leakage, held-out row mismatch, scheme sensitivity, strict extrapolation, and block-definition warnings retain their existing meanings.

A clean declared selection ledger proves only that the supplied row identities are disjoint from the declared final-validation rows. It does not establish complete selection history, indirect non-use of validation summaries, genuine predeclaration, correct candidate choice, correct hyperparameters, biological mechanism, or future distribution-shift performance. V6 adds no new statistical estimand and emits no aggregate confidence score.
