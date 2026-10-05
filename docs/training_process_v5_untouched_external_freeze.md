# Untouched-external freeze for the qualified training-process v5 route

The training-process route has a distinct external endpoint because its
inferential target is the mean over a frozen training-resampling process,
conditional on the frozen empirical training source, rather than the fixed-set
claim that every supplied refit passes.

The qualified external surface is

`odsp.training_process_untouched_external_v5.run_untouched_external_training_process_v5`.

## What is frozen before external outcomes

The pre-outcome freeze binds:

1. the external validation design: row ID, validation group, validation block
   and sample weight;
2. the frozen upstream training process, managed-generation receipt and exact
   generated model bytes;
3. the qualified internal v5 evidence snapshot;
4. the external scoring argv, scoring-code artifacts and scoring runtime
   environment;
5. score semantics and ordered information levels; and
6. the external endpoint implementation/runtime identity.

The external row/group/block/weight roster is outcome-free. These fields cannot
be changed after external scores become visible.

The freeze also records a declared first external-outcome access time. Runtime
verification requires the freeze timestamp to be strictly earlier than that
declared access time. A local manifest cannot independently prove the historical
truth of the declaration, and ODSP does not claim otherwise.

## Managed scoring after outcome access

The external endpoint does not treat an arbitrary caller-supplied score tensor
as the primary confirmatory input.

After outcome access, ODSP-managed scoring re-verifies all frozen generated model
artifacts, materializes per-refit model manifests and the frozen scoring
specification, invokes the frozen scoring command with `shell=False`, and
requires exact frozen row × level score coverage for every refit.

The managed scoring receipt hashes validation-data bytes, stdout/stderr,
individual score outputs and the canonical refit × row × level score bundle.
The endpoint realigns that managed bundle to the frozen external row IDs and
then calls the unchanged internal provenance-verifying v5 wrapper.

The full frozen training source frame must remain disjoint from external row IDs
in the declared identity namespace.

## Qualification and registry

The process-specific c2 independent-filtration external route is primary under

- `ODSP_CONFIRMATORY_ROUTE_EVIDENCE_REGISTRY_V6.json`, and
- `ODSP_CONFIRMATORY_EVIDENCE_CONTENT_LOCK_V4.json`.

Registry v5 is retained unchanged as historical provenance. Its external route
registration preceded completion of the independently replayed evidence-hash
gate by 103 seconds. The official replay subsequently matched the exact hashes
already embedded before registration, but the stricter ordering rule was not
met. Registry v6 was therefore created after the replay and is the active
registry.

The corrected external route evidence chain extends the internal v5 chain rather
than replacing it. Existing fixed-set evidence and routes are unchanged.

## Boundaries

The endpoint machine-verifies analysis/process/scoring content consistency. It
does not prove from a local timestamp that no person inspected outcomes before
the declared first-access time.

The complete validation-data bytes are hashed when managed scoring runs after
outcome access. Arbitrary non-outcome covariate bytes embedded in that later file
are not currently content-locked before outcome access, so ODSP does not claim
pre-outcome immutability of every raw external predictor byte.

The route also does not claim distribution-shift robustness, probability that an
individual future refit passes, positivity of all possible refits, or
generalization to repeated draws of the original ecological training source.

The process-specific external route is currently qualified only for independent
validation groups and an ordered filtration with exactly two contrasts.
