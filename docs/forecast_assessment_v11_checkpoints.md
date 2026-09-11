# Forecast Assessment v11: checkpoint-gated provenance composition

Forecast Assessment v11 adds one optional provenance gate above Forecast Assessment v10.

When `evaluation_access_checkpoints` are supplied, v11 extracts the `event_hash` values from the same supplied `evaluation_access_log_events` sequence that would be forwarded to v10 and checks the caller-supplied checkpoints first. If the checkpoints are inconsistent, the full v10 path is not run. If they are consistent, the existing v10 path runs unchanged.

The fail-closed order is therefore:

`checkpoint commitments -> access-log chain -> ledger binding -> exact content -> artifact ID -> selection -> training -> held-out row alignment -> refit-scheme statistics`.

Checkpoint mismatch is provenance failure, not statistical uncertainty. V11 adds no new statistical estimand and emits no aggregate confidence score.

A clean checkpoint audit proves only internal consistency between the supplied checkpoints and supplied event-hash sequence. It does **not** prove external timestamping, independent witnessing, checkpoint preexistence, real-world access-history completeness, or protection against co-fabricating an entire event chain and its checkpoints.
