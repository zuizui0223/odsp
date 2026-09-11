# Evaluation access checkpoint provenance

This audit checks whether multiple caller-supplied checkpoint commitments match selected SHA-256 event hashes from one supplied evaluation-access log.

A clean result means only that the supplied checkpoints are internally consistent with the supplied event-hash sequence, are presented in increasing event order, and include a terminal-event checkpoint. It does **not** establish when the checkpoints were created, whether a third party retained them, whether the whole chain and checkpoints were co-fabricated, or whether the real-world access history is complete.

The audit requires at least two checkpoints. Checkpoint indices must be unique, non-negative, in range, and the final event must be checkpointed. Hash mismatch, out-of-order checkpoint presentation, or a missing terminal checkpoint produces `evaluation_access_checkpoint_mismatch`. Invalid duplicate/out-of-range metadata is rejected rather than repaired.

No checkpoint index or hash is emitted in the result, and no aggregate confidence score is created.
