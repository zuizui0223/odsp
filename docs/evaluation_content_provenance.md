# Evaluation-content provenance audit

This layer checks a caller-supplied SHA-256 digest ledger for byte-identical reuse of the declared final-evaluation artifact during pre-final decision stages.

## Why it is separate from artifact-ID provenance

Artifact-ID provenance detects direct reuse when the same artifact identifier appears in a pre-final access ledger. A byte-for-byte copy can receive a different identifier. SHA-256 content provenance adds a distinct check: if a declared pre-final artifact digest equals the declared final-evaluation digest, the stage is marked `final_evaluation_content_leakage` regardless of artifact naming.

## Inputs and outputs

The audit accepts one final digest in `sha256:<64 hex>` form and a named mapping from pre-final stages to accessed artifact digests. Hexadecimal case is canonicalized. Duplicate non-final digests are legal and counted. Optional expected stage names require exact coverage.

The output reports stage counts, duplicate counts, leaking-stage counts, exact-match occurrence counts and the maximum number of final-content matches in one stage. It never emits the actual digest values.

## Decision boundary

One exact SHA-256 match is sufficient for `final_evaluation_content_leakage`. If no supplied pre-final digest matches, the category is `final_evaluation_content_not_accessed_in_declared_pre_final_stages`.

This is provenance evidence, not a statistical score.

## Claim boundary

A clean digest ledger does not prove complete access history. It also does not detect a re-encoded, reformatted, cropped, summarized, transcribed, screenshot, or otherwise semantically equivalent artifact whose bytes—and therefore SHA-256 digest—differ. The audit does not load files or compute hashes itself, infer missing access history, infer semantic equivalence, choose candidates, or emit an aggregate confidence score.

Forecast Assessment v7, frozen N2-MEE v4 submission artifacts, and closed empirical endpoints are not modified or reopened by this audit.
