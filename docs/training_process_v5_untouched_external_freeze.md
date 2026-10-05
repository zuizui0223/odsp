# Untouched-external freeze for the qualified training-process v5 route

The training-process route needs a distinct external endpoint because its
inferential target is the mean over a frozen training-resampling process, not
the fixed-set claim that every supplied refit passes.

The **active** external process route is qualified only for an independent,
ordered two-contrast filtration and is registered under confirmatory route
registry **v6**.

The external freeze binds three axes before any external outcome is opened:

1. the validation sampling design;
2. the frozen upstream training process and the model bytes actually generated
   by managed execution; and
3. the exact qualified provenance-verifying v5 wrapper.

The outcome-free external roster contains exactly four fields: row ID,
validation group, validation block and sample weight. All four are frozen.
Thus group assignment, block definition and weights cannot be changed after
external scores are visible.

The canonical internal method surface is
`odsp.training_process_confirmatory_v5.certify_predeclared_training_process_positive_information_v5`.
The canonical external surface is
`odsp.training_process_untouched_external_v5.run_untouched_external_training_process_v5`.

The freeze carries the exact implementation source closure, runtime dependency
snapshot, active internal-v5 qualification evidence chain, process manifest,
managed-generation receipt, generated model identities, refit identities and
the predeclared managed-scoring specification.

After outcome access, ODSP-managed scoring re-verifies the generated model bytes,
runs one frozen scoring command per refit with shell execution disabled, requires
exact row × level coverage, hashes the score-output bytes, and constructs the
canonical refit × row × level score tensor. The external endpoint accepts that
managed score bundle rather than an arbitrary caller-supplied score matrix.

At runtime the outcome-bearing external data must reproduce the frozen
row/group/block/weight design exactly. The entire frozen training source frame
must remain disjoint from the external row IDs in the declared identity
namespace. Managed scores are explicitly re-aligned by frozen row ID before the
unchanged internal v5 wrapper is invoked.

The freeze timestamp must strictly precede the declared first external-outcome
access timestamp. This provides a machine-checked declared chronology, but a
local repository cannot prove that nobody inspected outcomes before the declared
first access.

The endpoint proves content and semantic consistency. It does not claim
robustness to external distribution shift.

### Registration chronology

The first external registry-v5 activation was found to precede completion of the
official independent external-evidence hash replay by 103 seconds. That event is
retained as historical provenance rather than rewritten.

The active registry is **ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json**.
Registry v6 was created after the official hash replay and content-locks the
external activation correction contract, hash receipt and promotion contract.

For the full internal-to-external workflow, see
`docs/training_process_v5_confirmatory_chain.md`.
