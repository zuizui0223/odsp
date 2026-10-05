# Untouched-external freeze for the training-process route

The process route needs a distinct external endpoint because its inferential
target is not the fixed-set "all supplied refits pass" target.

The pre-outcome freeze must bind three axes at once:

1. the validation sampling design;
2. the frozen upstream training process and its actually generated model bytes;
3. the exact qualified v5 inferential implementation.

A key strengthening over the historical filtration external route is that the
external freeze does not hash row IDs alone. The outcome-free roster must contain
exactly four fields: row ID, validation group, validation block and sample
weight. All four are frozen before outcome access. Thus neither the block
definition nor weighting scheme can be changed after seeing external scores.

The freeze also records the training-process manifest digest, managed-generation
receipt digest, generated model artifacts, fit environment, v5 implementation
source closure, runtime environment and the complete qualification-evidence
content snapshot.

At runtime the outcome-bearing score table must match every frozen non-outcome
metadata field exactly before v5 is invoked.

Historical non-access to external outcomes is still not something a local hash
can prove. The endpoint proves semantic and content consistency, not a trusted
third-party timestamp history.

This contract does not open the route. Registration is forbidden until internal
v5 qualification, adversarial support, managed generation and source-frame
separation all pass.
