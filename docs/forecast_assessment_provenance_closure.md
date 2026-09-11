# Forecast Assessment local provenance closure

Forecast Assessment v11 is the terminal layer of the currently identified **caller-supplied, locally machine-checkable** provenance stack.

The closure is recorded in `FORECAST_ASSESSMENT_PROVENANCE_CLOSURE.json` and is intentionally not called v12. A new version number would imply that another local wrapper had added a new evidential capability. At the present boundary, that would be misleading.

## What is closed locally

The composed stack can machine-check, under supplied inputs and frozen contracts:

- checkpoint commitments against event hashes from the same supplied evaluation-access sequence;
- access-log chain consistency;
- ledger-to-artifact binding consistency;
- exact final-evaluation content reuse;
- final-evaluation artifact-ID reuse;
- declared selection/validation overlap;
- declared training/validation overlap;
- held-out row alignment;
- refit-scheme sensitivity;
- separation of provenance failure from statistical uncertainty.

V11 therefore closes the identified **internal consistency** path from checkpoint commitments through the existing Forecast Assessment v10 provenance and statistical gates.

## What is not closed

No local self-consistency layer can by itself prove that the supplied history is the real-world history. In particular, v11 does not establish:

- external timestamping;
- independent witnessing;
- checkpoint preexistence before evaluation access;
- completeness of the real-world access history;
- prevention of whole-chain plus checkpoint co-fabrication;
- genuine predeclaration.

Those are external trust questions, not missing local hash-composition questions.

## Reopening rule

A future Forecast Assessment extension is justified only if at least one of the following is true:

1. a distinct, machine-checkable **local** provenance gap is identified that is not already covered by v11; or
2. a genuinely new **external evidence source or trust root** becomes available, such as an independently verifiable timestamp, append-only-log inclusion proof, independently controlled signed witness, or trusted access infrastructure.

Adding another caller-supplied digest, hash chain, checkpoint list, receipt, or commitment that is controlled by the same party is not sufficient to claim stronger external provenance.

Any future extension must preserve the frozen v11 contract and receipt, keep provenance failures separate from statistical uncertainty, emit no aggregate confidence score, and must not reopen the closed N2 empirical endpoints.

## Scientific boundary

This closure is an engineering/provenance boundary only. It adds no statistical estimand, empirical result, biological mechanism claim, or guarantee of future distribution-shift performance. It does not promote Gate E and does not reopen the scientifically closed Chapter-N2 empirical chain.
