# Forecast Assessment v7: evaluation-access provenance gate

Forecast Assessment v7 composes the existing Forecast Assessment v6 result with the final-evaluation access ledger validated by `evaluation_access_provenance`.

## Why this layer exists

Row-level selection provenance can detect direct reuse of final-validation rows. It cannot detect a different but equally direct failure mode: a pre-final stage may read the already-produced final-evaluation artifact itself, even if the row identifiers exposed to that stage are different or absent.

V7 therefore accepts one caller-declared final-evaluation artifact ID plus a named ledger of artifacts consulted during pre-final decision stages. The ledger is audited before the full v6 path is allowed to run.

## Composition order

When evaluation-access provenance is supplied, the order is:

1. audit direct pre-final access to the declared final-evaluation artifact;
2. retain a v6 base assessment with selection and refit-scheme layers omitted;
3. if the access ledger is clean, run ordinary Forecast Assessment v6 unchanged;
4. if direct final-artifact reuse is declared, do not run the full downstream v6 selection/training/alignment/scheme path.

A final-artifact access leak is recorded as provenance failure `final_evaluation_access_leakage`, not as statistical uncertainty. On an otherwise certifiable base it yields v7 `unavailable` / `admitted_extended_unavailable`.

## Omitted access layer

If no evaluation-access ledger is supplied, V7 preserves ordinary Forecast Assessment v6 behavior. Supplying access-stage metadata without a ledger, or a ledger without a final-evaluation artifact ID, is rejected.

## Claim boundary

A clean declared ledger means only that the supplied ledger does not contain the supplied final-evaluation artifact ID. It does not prove that the ledger is complete, that no copy/re-encoding or summary of the final artifact was consulted, that selection was genuinely predeclared, that the statistical model is valid, or that the selected candidate is scientifically correct.

V7 adds provenance composition only. It creates no new statistical estimand or aggregate confidence score and does not modify frozen Forecast Assessment v6, frozen N2-MEE v4 submission artifacts, or closed empirical endpoints.
