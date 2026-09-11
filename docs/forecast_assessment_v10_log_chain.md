# Forecast Assessment v10: access-log-chain gate

Forecast Assessment v10 is a thin provenance composition layer over frozen Forecast Assessment v9.

When a caller supplies an evaluation-access event log, v10 first checks the frozen `EVALUATION_ACCESS_LOG_CHAIN_CONTRACT.json`: contiguous sequence indices, previous-hash chaining, recomputed SHA-256 event hashes, committed event count, committed terminal hash, and exact stage-wise ID/digest ledger agreement.

If the chain is consistent, the same stage-wise artifact-ID and digest ledgers audited by the chain are forwarded unchanged into v9. If the chain is inconsistent, the full v9 path is not run. The result is provenance-unavailable via `evaluation_access_log_chain_mismatch`; the mismatch is not converted into a weak statistical result.

The log-chain layer is optional. Omitting it preserves ordinary v9 behavior.

## Claim boundary

A consistent supplied chain proves internal consistency only. It does **not** prove external timestamping, third-party commitment, a complete real-world access history, absence of whole-chain fabrication, genuine predeclaration, absence of indirect information transfer, biological mechanism, or future predictive validity.
