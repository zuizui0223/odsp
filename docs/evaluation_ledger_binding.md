# Evaluation ledger binding provenance

This audit checks whether two caller-supplied views of pre-final evaluation access are internally consistent with one caller-supplied artifact manifest:

- artifact IDs accessed by stage;
- SHA-256 digests accessed by stage.

The manifest maps artifact IDs to SHA-256 digests. The declared final-evaluation artifact ID must exist in that manifest, and its manifest digest must equal the separately declared final-evaluation digest. Every accessed artifact ID must also exist in the manifest.

Within each stage, the audit compares the multiset of digests implied by the accessed artifact IDs against the separately declared digest multiset. Digest ordering within a stage is irrelevant; repeated accesses are legal and reported. A mismatch in either the final ID-to-digest binding or any stage multiset produces `evaluation_ledger_binding_mismatch`. Fully consistent bindings produce `evaluation_ledgers_consistently_bound`.

If multiple artifact IDs map to the declared final digest, the number of alias IDs is reported. An alias is not itself treated as leakage: whether an alias was actually consulted is a separate access question handled by the existing artifact-ID/content provenance layers.

## Scope boundary

The audit does not open or hash files. It validates only the supplied manifest and ledgers. A consistent result does not prove that the manifest is true or complete, that all accesses were logged, that the ledger was genuinely predeclared, or that differently encoded content is semantically distinct. It adds no statistical evidence, chooses no candidate, and identifies no biological mechanism.

Forecast Assessment v8, frozen N2-MEE v4 artifacts and closed empirical endpoints are not modified or reopened.
