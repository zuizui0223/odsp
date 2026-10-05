# Managed external scoring for training-process v5

The qualified v5 wrapper verifies how the upstream refits were generated, but a
caller-supplied score tensor still leaves one provenance gap: the tensor could
have been produced by some other model or scoring program.

The managed external scoring layer closes that operational gap.

Before external outcomes are opened, the freeze records a scoring argv array,
the bytes of every scoring-code artifact, the scoring runtime environment,
the score semantics, the three ordered information levels, and the external row
roster. The validation outcome file itself is not read or hashed at freeze time.

After outcome access, ODSP re-verifies every generated model artifact, writes a
per-refit model manifest, writes the frozen scoring specification, and invokes
one scoring process per refit with shell execution disabled. Each scorer emits a
strict JSON object containing one score for every frozen row at every frozen
information level.

ODSP validates the output schema and row coverage, hashes stdout, stderr and
score-output bytes, and constructs the refit x row score matrices itself. The
receipt binds those matrices to the external freeze manifest, validation data
bytes, generated model artifacts, scoring implementation and runtime.

This establishes an operational chain from frozen training-process draw to
generated model bytes to external score tensor. As with managed model fitting,
it cannot cryptographically prove that arbitrary frozen scoring code uses every
argument semantically; that remaining property is auditable source behavior.
