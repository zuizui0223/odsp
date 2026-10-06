# Qualified training-process v5 confirmatory chain

ODSP now has a separate confirmatory route for uncertainty induced by a
**prospectively frozen training-resampling process**. This route is distinct from
the historical fixed-set all-refit intersection.

The qualified claim is:

> the mean held-out directional gain over the frozen training-resampling process,
> conditional on the frozen empirical training source, is positive on the
> declared validation population.

It is **not** a claim that every possible refit is positive, not a probability
that one future refit passes, and not uncertainty over drawing an entirely new
ecological training dataset.

## Qualified statistical method

The active method is v5, a two-term two-way cluster-jackknife component test:

```text
V_CV3(2) = V_R^JK + V_B^JK
df       = min(R, B) - 1
```

Each group × ordered information-step component uses a one-sided Student-t lower
bound. The compound claim is an intersection-union test: every required
component must reject.

Prospective base qualification passed all six frozen scenarios:

- maximum component false-positive rate: **0.056**;
- accepted maximum: **0.06378404875209022**;
- minimum 5-oracle-SE terminal power: **0.859**;
- required minimum power: **0.80**.

A separately frozen adversarial support panel also passed all five stress worlds;
the largest component false-positive rate was **0.058**.

Versions v1-v4 remain frozen historical candidates with their original failures.
They are not reclassified.

## Canonical internal chain

The primary internal surface is:

```text
odsp.training_process_confirmatory_v5.
certify_predeclared_training_process_positive_information_v5
```

The canonical order is:

1. **Freeze the training process.**
   The source roster, resampling family, refit IDs, resampling seeds, fit seeds,
   fitting implementation and bootstrap-membership digests are frozen.

2. **Generate refits under managed execution.**
   ODSP reconstructs each frozen bootstrap membership, verifies its digest,
   invokes the predeclared argv with `shell=False`, records the fit environment,
   and content-hashes generated model artifacts.

3. **Verify full source-frame separation.**
   The entire frozen training-source roster—not only the realized bootstrap
   memberships—must be disjoint from validation row IDs in one declared identity
   namespace.

4. **Run the qualified v5 wrapper.**
   The wrapper verifies the process manifest, managed-generation receipt, exact
   refit schedule and source-frame separation before invoking the CV3(2) core.

The raw numerical v5 function is not itself the primary confirmatory surface.

## Canonical untouched-external chain

The primary untouched-external surface is:

```text
odsp.training_process_untouched_external_v5.
run_untouched_external_training_process_v5
```

Before external outcomes are opened:

1. freeze external row ID, validation group, validation block and sample weight;
2. bind the frozen training process and managed-generation receipt;
3. bind generated model bytes and fit environment;
4. bind the internal-v5 qualification evidence snapshot;
5. bind the external endpoint implementation/runtime identity;
6. freeze the scoring argv, scoring-code bytes, scoring runtime, score semantics
   and information levels.

After outcome access:

1. ODSP re-verifies every generated model artifact;
2. one frozen scoring process is run per refit with `shell=False`;
3. exact row × level coverage is required;
4. stdout, stderr and score-output bytes are content-hashed;
5. ODSP constructs the canonical refit × row × level score tensor;
6. the external endpoint verifies the managed score bundle;
7. rows are re-aligned only by frozen row ID;
8. the unchanged internal provenance-verifying v5 wrapper is called.

The external endpoint does not accept an arbitrary caller-supplied score tensor
as its primary input.

## Prospective chronology

The external freeze must strictly predate the declared first external-outcome
access timestamp.

A local repository cannot prove the historical truth of that declaration. ODSP
therefore records the declaration and verifies its chronology without claiming
third-party attestation of prior non-access.

An initial route-registry v5 activation occurred 103 seconds before the official
independent external-evidence hash replay completed. That ordering error is
preserved rather than rewritten. Registry v5 is historical. The active registry
is **v6**, created only after the official replay, with the correction contract
and hash receipt content-locked into the active evidence chain.

## Active scope

Primary confirmatory:

- alternative: `greater`;
- validation design: independent groups;
- information structure: ordered filtration;
- contrast count: exactly 2;
- upstream refits: predeclared training process;
- internal validation: qualified;
- untouched-frozen external validation: qualified.

Still unqualified for the training-process route:

- contrast count 4;
- paired/shared-block validation;
- complete information lattices;
- individual-future-refit success probability;
- all-future-refits-positive claims;
- repeated sampling of the original ecological training source;
- robustness to external distribution shift.

The fixed-set route remains unchanged and answers a different question.


## Operational CLI

The qualified chain can be executed without adding a new top-level ODSP command
through:

```text
odsp experimental training-process freeze
odsp experimental training-process generate
odsp experimental training-process external-freeze
odsp experimental training-process external-score
odsp experimental training-process external-run
```

These commands are operational wrappers only; they do not define a new
statistical method, primary surface or evidence registry. See
[`training_process_v5_operational_cli.md`](training_process_v5_operational_cli.md)
for the exact file contracts and chronology.
