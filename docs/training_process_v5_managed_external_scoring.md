# Managed external scoring for training-process v5

The qualified internal v5 wrapper verifies how upstream refits were generated,
but an arbitrary caller-supplied external score tensor would still leave a
provenance gap: the tensor could have been produced by another model or scoring
program. The managed external scoring layer closes that operational gap.

## Pre-outcome scoring freeze

Before external outcomes are opened, the process-specific external freeze records

- the scoring argv array;
- the bytes of every scoring-code artifact;
- the scoring runtime environment;
- score semantics and the three ordered information levels;
- the external row/group/block/weight design; and
- the exact generated model artifacts that may be scored.

Shell execution is disabled. The scoring command must expose explicit
placeholders for refit ID, model manifest, validation-data path, scoring
specification and output path.

The validation outcome-bearing data file itself is not read or content-hashed
during this pre-outcome freeze.

## Managed execution after outcome access

ODSP re-verifies every frozen generated model artifact, writes a per-refit model
manifest, writes the frozen scoring specification, and invokes one scoring
process per refit.

Each scorer must emit a strict JSON object containing exactly one score for every
frozen row at every frozen information level. ODSP validates schema and row
coverage, hashes stdout, stderr and score-output bytes, and constructs the
canonical refit × row × level score matrices itself.

The scoring receipt binds those matrices to

- the external freeze manifest;
- the managed-generation receipt;
- validation-data bytes at scoring time;
- generated model artifacts;
- scoring implementation and runtime; and
- the canonical score-tensor digest.

The untouched-external endpoint consumes this managed score bundle and receipt;
the primary route does not accept an arbitrary caller-generated score tensor in
their place.

## Boundary

This establishes an operational chain from frozen training-process draw to
generated model bytes to managed external score tensor. As with managed model
fitting, it cannot cryptographically prove that arbitrary frozen scoring code
uses every argument semantically; that property remains auditable source
behavior.

The current pre-outcome freeze also does not content-lock arbitrary raw
non-outcome covariate values that may be embedded in the validation-data file
later supplied to the scorer. The complete validation-data bytes are hashed at
managed-scoring time after outcome access. Accordingly, the machine-verification
claim is outcome isolation plus frozen design/model/scoring provenance, not
immutability of every external predictor byte before outcome access.
