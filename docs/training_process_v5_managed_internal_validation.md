# Managed internal validation for training-process v5

The qualified internal v5 wrapper verifies the frozen training process, managed
model generation, exact refit schedule, and whole-source-frame separation from
validation rows.  Its remaining provenance boundary is explicit: the held-out
score matrices can still be supplied by the caller.

This layer closes that gap without changing the statistical method.

Before validation outcomes are opened, ODSP freezes the validation row ID,
group, block and weight design, score semantics, ordered three-level filtration,
certification settings, generated model identities, scoring command/code/runtime
and the complete training-process provenance chain.

After declared validation-outcome access, ODSP re-verifies the generated model
bytes, runs one frozen scoring process per refit with shell execution disabled,
requires exact row x level coverage, hashes every score-output file, and builds
the canonical refit x row x level score tensor itself.

The candidate managed-internal endpoint then verifies that bundle and calls the
already-qualified internal provenance wrapper unchanged.  The CV3(2) estimator,
Student-t critical value, IUT composition, and process-mean estimand are not
modified.

This does not cryptographically prove that arbitrary scoring code is
semantically correct; it proves which frozen code was invoked on which frozen
model bytes and which validation data, and what score bytes it produced.

The existing internal primary route is not reclassified by this contract.  A
separate focused-test and implementation-identity gate is required before the
managed-internal surface can replace it as the preferred primary operational
surface.
