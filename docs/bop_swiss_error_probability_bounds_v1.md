# Swiss red-kite: aggregate bounds on high-confidence errors

## Result and evidence status

The [proper-score audit](bop_swiss_proper_score_discordance_v1.md) found positive
Brier improvement but negative log-score improvement in both 2022 home-range
(HR) panels. Their accuracy and log loss also force a quantitative statement
about wrongly assigned probabilities, without reopening individual predictions.

Each 2022 panel contains **256 model-record predictions: eight models applied
to the same 32 source seasons**, with 32 source bird-ID strings. The rounded
87.5% accuracy uniquely implies **224 correct and 32 incorrect predictions**
across those repeated models. These are not 256 independent animals.

| 2022 HR training mode | Mean log loss among errors, lower bound | Geometric mean true-class probability among errors, upper bound | Minimum predictions with true-class probability <1% |
|---|---:|---:|---:|
| Full forward | 5.374969 | 0.004632 (0.4632%) | **3 of 256** |
| Bird-purged forward | 6.281137 | 0.001872 (0.1872%) | **6 of 256** |

All displayed bounds are rounded outward. At least one erroneous prediction
in each panel has true-class probability no greater than its geometric-mean
bound. A geometric mean is not an arithmetic mean or a median. The severe-error
counts may repeatedly refer to the same season under different model seeds.

This is an **exploratory deterministic implication of already inspected
aggregates**. The anomaly, candidate inequalities and approximate 2022 bounds
were known before specification commit
[`ebb5931`](https://github.com/zuizui0223/odsp/commit/ebb5931a687569299e0a353e9b856e485a03317d).
The specification fixes implementation and replay, including the post-result
1% threshold; it is not a first-look or confirmatory validation. The contribution
is an auditable diagnostic, not a claim of a new general scoring-rule theorem.

## Derivation

Let `z` be the clipped probability assigned to the observed binary class, and
let its logarithmic loss be `-ln(z)`. With a 0.5 classification threshold, a
correct prediction has loss at most `b = ln(2)`; an incorrect prediction has
loss at least `b`. Ties at 0.5 are included in these inequalities.

For `N` equally weighted predictions, `K` correct predictions, `E=N-K>0`
incorrect predictions, and mean log loss `L`, summing the correct-prediction
cap gives

\[
\overline{\ell}_{\rm error}
\geq \max\left\{\ln 2,\frac{NL-K\ln 2}{E}\right\}.
\]

Since the geometric mean probability among errors equals
`exp(-mean_error_log_loss)`,

\[
\min_{i\in\mathrm{errors}}z_i
\leq \operatorname{GM}_{i\in\mathrm{errors}}z_i
\leq \exp\left[-\max\left\{\ln 2,\frac{NL-K\ln 2}{E}\right\}\right].
\]

This is an existence bound. It does not identify a seed, season or bird, and
does not assert that every erroneous prediction or every seed meets the bound.
When `E=0`, these conditional quantities are undefined; the code returns null.

For a fixed threshold `tau=0.01`, write `T=-ln(tau)` and let
`M=-ln(epsilon)` be an upper loss cap from the scored probability floor.
If `J` predictions have `z<tau`, the remaining errors have loss at most `T`, so

\[
NL\leq K\ln 2+ET+J(M-T).
\]

Therefore a nonnegative integer lower bound is

\[
J\geq\max\left\{0,\left\lceil
\frac{NL-K\ln 2-ET}{M-T}
\right\rceil\right\}.
\]

The inequality applies to **strictly below** the threshold: a true-class
probability exactly equal to 0.01 belongs to the non-tail group. A zero lower
bound means that these summaries force no positive count; it does not show
that no such errors occurred.

## Why the existing source metrics satisfy the assumptions

The pinned [R scorer](../scripts/bop_swiss_ranger_focal_prior_year_v1.R) clips the
positive-class probability to `[1e-6,1-1e-6]`, predicts positive on `p>=0.5`,
and computes equal-row mean accuracy and negative natural-log probability of
the observed class. Its Git blob is `f80b1d3d40b0203506b16cbfa783c4096c9f23a8`.
The [temporal wrapper](../scripts/bop_swiss_temporal_bird_purge_ranger_v1.R),
blob `66a9b0652e0e3005a7a167635b73cf9f011899b9`, uses identical test rows for
eight equally weighted seeds within a cell. The source contract and receipt
record 292, 117 and 32 test rows at the three cutoffs.

Each seed metric and its eight-seed mean are rounded to six decimal places.
The replay therefore uses an uncertainty radius of **0.000001000001**: two
half-unit rounding errors plus numerical slack of `1e-12`. Multiplying the
accuracy interval by `N` must admit exactly one integer correct count. Every
source cell passes this requirement; missing or ambiguous counts are rejected.
The lower endpoint of the log-loss interval is used in both lower bounds.

The nominal source probability floor is `1e-6`. A conservative floor of
**0.000000999999** also allows the numerical slack in clipping/complement
arithmetic. Decimal calculations enclose logarithms and exponentials, round
arithmetic in the conservative direction and serialize bounds outward as
decimal strings. These are deterministic uncertainty envelopes for recorded
rounding, not statistical confidence intervals.

## All twelve fixed cells

`N` counts model-seed x source-season predictions. Source bird-ID strings are
194, 92 and 32 at the 2020, 2021 and 2022 cutoffs, respectively. Test cohorts
overlap across cutoffs. Purging established disjointness of source ID strings;
it did not provide external canonical animal identity verification.

| Cutoff | Target | Training mode | N | Errors | Error geometric-mean probability, upper bound | Minimum z<1% count |
|---|---|---|---:|---:|---:|---:|
| 2020 | HR | Full | 2336 | 123 | 0.500000 | 0 |
| 2020 | HR | Purged | 2336 | 99 | 0.500000 | 0 |
| 2020 | Nest | Full | 2336 | 271 | 0.500000 | 0 |
| 2020 | Nest | Purged | 2336 | 283 | 0.500000 | 0 |
| **2021 primary** | HR | Full | 936 | 56 | 0.500000 | 0 |
| **2021 primary** | HR | Purged | 936 | 55 | 0.500000 | 0 |
| **2021 primary** | Nest | Full | 936 | 144 | 0.500000 | 0 |
| **2021 primary** | Nest | Purged | 936 | 156 | 0.500000 | 0 |
| 2022 | **HR** | Full | 256 | 32 | **0.004632** | **3** |
| 2022 | **HR** | Purged | 256 | 32 | **0.001872** | **6** |
| 2022 | Nest | Full | 256 | 54 | 0.500000 | 0 |
| 2022 | Nest | Purged | 256 | 64 | 0.329691 | 0 |

The generic 0.5 bound adds no information beyond knowing that predictions were
misclassified. In particular, the zero count bounds in the 2020/2021 panels
do not certify absence of severe errors or superior tail calibration.

## What this adds, and what remains unidentified

The earlier aggregate audit could not identify a particular erroneous bird or
calibration mechanism. That limit remains. The present calculation narrows
the remaining possibilities: both 2022 HR panels necessarily include extremely
small assigned probabilities for some observed outcomes. High accuracy and
positive Brier gain can coexist with these guaranteed high-confidence errors.

The bound does not recover individual probabilities, a calibration curve, an
error-class breakdown, the overlap of errors between modes, or an ecological
cause. The lower counts 3 and 6 do not prove the purged model actually has more
severe errors: two lower bounds do not order the unknown actual counts. Model
seeds and overlapping cutoffs are not independent biological replicates. The
original primary 2021 positive log-score findings are unchanged.

The historical BOP terminal remains `empirical_state_prediction_mixed`, the
real external red-kite route remains
`HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER`, and original Dryad
remains `NOT_ADMITTED`. No new source outcomes or future-animal coverage have
been established.

## Reproduce and audit

```bash
python -m pytest -q tests/test_bop_swiss_error_probability_bounds_v1.py tests/test_bop_swiss_proper_score_discordance_v1.py
python -m scripts.bop_swiss_error_probability_bounds_v1 --out /tmp/bop-swiss-error-bounds.json
```

The [replay contract](../research/BOP_SWISS_ERROR_PROBABILITY_BOUNDS_V1_CONTRACT.json)
pins the source receipt, previous rank receipt, previous proper-score contract
and implementation, original temporal contract and both R code files. The
new contract's Git blob is `903ce8f1998a5a1e55b3bb4b891475602601197c`.
The [implementation](../scripts/bop_swiss_error_probability_bounds_v1.py) reads
these aggregate/code bytes only; the R files are never executed. Output paths
aliasing any protected input or the executable are rejected, including relative
paths, symlinks and hard links.

Known-prediction tests cover sharp examples, strict-threshold ties, all-correct
and all-wrong cases, impossible metrics, integer-count ambiguity, two-stage
rounding, extreme numerical scales, input drift and protected outputs. The
dedicated workflow runs both diagnostic suites and the twelve-cell replay
under Python 3.10, 3.12 and 3.13 without biological source downloads.

### Qualification of both accuracy-rounding stages

A follow-up to [PR #301](https://github.com/zuizui0223/odsp/pull/301) replaces
six equivalent seed permutations with one representative and adds two distinct
seven-record x eight-model synthetic cases. Both use the source scorer's
clipping, class threshold and per-model-then-pooled six-decimal rounding.

| Correct predictions per model | Exact pooled accuracy | Recorded accuracy | Recorded minus exact |
|---|---:|---:|---:|
| 2, 2, 3, 3, 3, 3, 3, 7 | 26/56 | 0.464285 | -1/1,400,000 |
| 4, 4, 4, 4, 4, 5, 6, 6 | 37/56 | 0.660715 | +1/1,400,000 |

Each discrepancy exceeds a single six-decimal half-unit. The configured
two-stage allowance recovers the exact counts; an allowance of 0.000000500001
(one half-unit plus the same numerical slack) rejects both. Accuracy rounding
avoids midpoint ties, and the arrays include both labels at the classification
tie and probabilities clipped at both endpoints. An independent 80-digit
calculation from the known synthetic probabilities checks the log-loss interval,
conditional error bounds and nonzero severe-error count bounds.

The focused suite has 93 cases: 73 bound/replay cases and 20 prior proper-score
cases. Five duplicate permutations were removed and two substantive cases were
added. The production implementation and pinned inputs are unchanged; the full
twelve-cell replay is byte-for-byte identical to its pre-change output. This
qualifies the existing rounding envelope without adding biological evidence.
