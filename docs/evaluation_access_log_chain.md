# Evaluation-access log-chain provenance

This layer checks the internal append-only structure of a caller-supplied evaluation-access event log and binds that event sequence to caller-supplied stage-wise artifact-ID and SHA-256 digest ledgers.

Each event contains a zero-based sequence index, stage name, artifact ID, artifact digest, previous-event hash and event hash. The first event must point to a fixed genesis hash. Every event hash is recomputed from a canonical JSON payload, and every previous-event hash must equal the preceding event hash. A caller-supplied committed event count and committed terminal hash are also checked.

The audit additionally derives the stage-wise ID and digest sequences from the events and compares them with the supplied ledgers. Stage mapping order is irrelevant; within-stage event order is preserved. Duplicate accesses are legal and reported.

A clean result is `evaluation_access_log_chain_consistent`. Any chain, commitment or ledger mismatch is `evaluation_access_log_chain_mismatch`. The audit never repairs, drops or imputes events.

## What this does not prove

A consistent chain is only internally self-consistent. It does not prove that the chain was externally timestamped, that a third party committed to the terminal hash, that the supplied real-world access history is complete, or that the caller did not fabricate an entirely new self-consistent chain. It does not establish genuine predeclaration, prevent indirect information transfer, add statistical evidence, identify a correct candidate, or identify biological mechanism.

Artifact IDs, digests and event hashes are not emitted in the audit result. Frozen Forecast Assessment v9, N2-MEE v4 submission artifacts and closed empirical endpoints remain untouched.
