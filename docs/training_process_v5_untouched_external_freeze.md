# Untouched-external freeze for the qualified training-process v5 route

The training-process route needs a distinct external endpoint because its
inferential target is the mean over a frozen training-resampling process, not
the fixed-set claim that every supplied refit passes.

The external freeze binds three axes before any external outcome is opened:

1. the validation sampling design;
2. the frozen upstream training process and the model bytes actually generated
   by managed execution; and
3. the exact qualified provenance-verifying v5 wrapper.

The outcome-free external roster contains exactly four fields: row ID,
validation group, validation block and sample weight. All four are frozen.
Thus group assignment, block definition and weights cannot be changed after
external scores are visible.

The canonical method surface is
`odsp.training_process_confirmatory_v5.certify_predeclared_training_process_positive_information_v5`,
not the raw CV3(2) numerical core. The freeze therefore carries the exact
implementation source closure, runtime dependency snapshot, active v4
qualification evidence chain, process manifest, managed-generation receipt and
refit identities.

At runtime the score-bearing external data must reproduce the frozen
row/group/block/weight design exactly before the v5 wrapper is invoked. The
entire frozen training source frame must also remain disjoint from the external
row IDs in the declared identity namespace.

The endpoint can prove content and semantic consistency. It cannot prove, from
a local hash alone, that nobody inspected external outcomes before the freeze,
and it does not claim robustness to distribution shift.

The external route remains unregistered until the endpoint implementation and
its freeze/runtime mismatch tests pass.
