# Aggregate bounds on wrongly assigned probabilities

## Intent and scope

Continue ODSP BOP methodology after merged PR #300. Determine what the existing
accuracy and logarithmic-loss aggregates force about wrongly classified
predictions, while keeping every original empirical result and admission state.
This is an exploratory deterministic implication of already inspected results.
The 2022 HR anomaly, candidate inequality and approximate bounds were known
before this implementation specification. This is not a new confirmatory test.

## Approach

Use a standard-library Python diagnostic, synthetic tests and all twelve pinned
Swiss aggregate cells. Reopening prediction vectors would identify records but
is outside this route; refitting or calibration would ask a different question.
The chosen aggregate calculation can establish existence and a minimum number
of severe errors without identifying a bird, seed, mechanism or future cohort.
The user's standing instruction authorizes autonomous continuation. The choice
to implement directly with independent mathematical and source-code reviews is
the implementer's choice.

## Mathematical contract

For N equally weighted predictions, K correct classifications and E=N-K errors,
let L be average negative natural log of the clipped true-class probability z.
The original class threshold is p>=0.5; ties therefore allow loss ln(2) on either
side. Correct losses are at most b=ln(2), and erroneous losses are at least b.
Consequently, for E>0:

    mean_error_loss >= max(b, (N*L-K*b)/E)
    geometric_mean_error_probability <= exp(-mean_error_loss_lower_bound)

At least one erroneous prediction has true-class probability no greater than
that geometric-mean bound. This does not bound the arithmetic mean or median,
identify any record, apply separately to every seed or imply causation.

For the fixed threshold tau=0.01 and a true-class probability floor epsilon,
write T=-ln(tau), M=-ln(epsilon). If J predictions have z<tau, then:

    N*L <= K*b + E*T + J*(M-T)

The nonnegative ceiling of the resulting lower bound on J is a count of
seed-record predictions, never a count of independent birds.

## Source semantics and rounding

The same test rows are used for eight equally weighted seeds within each cell.
There are 292, 117 and 32 test seasons at cutoffs 2020, 2021 and 2022, so N is
2336, 936 and 256. Each seed metric and the subsequent seed mean are rounded to
six decimals. Allow radius 0.000001000001: the two half-unit rounding errors
plus 1e-12 numerical slack. Recover K only if exactly one integer lies in
N times the resulting accuracy interval; reject absent or ambiguous counts.
The source nominal clip is 1e-6. Use 0.000000999999 as the conservative floor
to allow the same numerical slack. Decimal arithmetic, outward log/exp bounds
and directional rounding must never strengthen a bound on serialization.

## Implementation boundaries

- Pin the new replay contract, prior aggregate receipts, prior replay code,
  source design and both original scoring-code blobs. Read R code as bytes;
  never execute R or contact source providers.
- Reuse the prior twelve-cell audit and validate the exact row, seed and cohort
  layout before interpreting aggregate accuracy as a count.
- Expose `binary_error_bounds(accuracy, log_loss, n_predictions, *,
  rounding_radius, clip_floor, probability_threshold)` in the new script.
  It returns counts and outward-rounded decimal strings. All-correct inputs
  return null conditional bounds. Reject invalid, nonfinite or infeasible input.
- CLI: `python -m scripts.bop_swiss_error_probability_bounds_v1`, optionally
  `--out PATH`; reject direct, relative, symbolic-link and hard-link aliases of
  every pinned input and of the executable itself.
- Report all twelve cells and unchanged terminals. Retain the primary 2021
  results and the limits of source bird-ID-string disjointness.

## Completion

Synthetic sharp examples, tie cases, all-correct/all-wrong cases, rounding,
feasibility, immutable-input and normal-output tests pass; every reported bound
is checked against known synthetic prediction arrays. Dedicated Python
3.10/3.12/3.13 CI and existing common CI pass. Independent final review precedes
integration. Scientific report, README and manuscript explain the new bound
without promoting the retrospective source to independent-animal validation.
