# Managed nested generation for training-source process v0

The v0 source-process estimand has two upstream stochastic levels:

```text
outer source draw
    -> inner model refit
        -> validation score
```

A flat generation receipt would lose that nesting. The managed v0 generation
route therefore reconstructs both membership levels before every fit.

For each outer source ID, ODSP recreates the frozen stratified bootstrap
membership on the original source roster and verifies its semantic digest.

For each inner refit under that source, ODSP expands the outer membership into a
deterministic slot list, resamples those slots using the frozen inner seed,
reduces the result back to original-roster counts and verifies the frozen inner
membership digest.

Only then does ODSP invoke the predeclared fit argv. The command receives both
the outer and inner membership files, source ID, inner-refit ID, fit seed and
output directory. Shell execution is disabled.

The receipt is nested by source and records:

- outer membership digest;
- every inner membership digest;
- exact argv;
- stdout/stderr digests;
- model artifact digests;
- Python/distribution/runtime snapshot;
- frozen command artifact digests.

This establishes the operational hierarchy needed by the v0 statistical
estimator. It still cannot cryptographically prove that arbitrary frozen fit
code semantically used every argument correctly; source review remains necessary.

No validation row or validation outcome is an input to this generation stage.
