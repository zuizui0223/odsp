# Shared-validation future-refit success probability: e-value + Markov v0

Status: NEW experimental numerical candidate, NOT qualified, NOT registered,
and NOT retrospective reinterpretation of failed v1/v2 or independent
validation v3. This document describes a distinct validation design.

## The ecological question and the estimand

Fix a prospectively specified training-resampling process and a single
ecological validation-block population. Let a newly generated model refit r
have a population mean information-score gain mu[r,g,c] for each declared
independent validation group g and ordered filtration contrast c.

The true target is

    p = P_r(all mu[r,g,c] > tau).

In this v0, each population mean is the expectation over a randomly drawn
VALIDATION BLOCK of the within-block weighted average gain, not the
event-weighted population mean used in other ODSP routes. Unequal block
sizes may change the target. It must not silently inherit an old claim.

This is a probability over NEW model refits from the same frozen process,
conditional on the original empirical training source, not an assertion about
all future models or a new natural ecological source superpopulation.

## What is deliberately reused?

ALL R independent training-process refits are scored against the SAME frozen
held-out validation block sample V, as in the v1/v2 architecture. There is no
requirement for R separate validation datasets, unlike the independent
validation v3 candidate.

Yet the R observed certificates Y_r are NOT unconditionally independent:
their scores are correlated via V. Replacing their unconditional law with an
iid binomial distribution is invalid, as the shared-shock counterexample in
PR #216 demonstrates.

The valid conditional statement is:

    K | V  ~  Binomial(R, theta(V)),
    theta(V) = P_r(certificate(r,V)=1 | V).

This is exact if the R refits really are iid frozen-process draws,
independent of the held-out validation sample, and the certification rule is
frozen rather than selected using the observed V.

## Step 1: Finite-sample component tests for bounded scores

A row-level gain must have a prospectively guaranteed common bound
L <= gain <= U for the ENTIRE frozen training and validation process.

The defaults L=-1, U=1 are appropriate ONLY if the chosen score difference
is known a priori to satisfy those bounds, e.g. the difference of two
normalized [0,1] Brier-based scores. Ordinary log-score differences are
unbounded unless a frozen probability clipping rule supplies valid limits.
The raw API rejects observed finite values outside the declared limits,
but observed in-range values do NOT verify the process-wide bound.

For each g,c, let X_b be the within-block weighted mean gain from iid
validation blocks b=1,...,B. The block-uniform null is E[X_b] <= tau,
with L < tau < U. The code fixes four betting fractions before outcomes:

    lambda = 0.25, 0.50, 0.75, 1.00.

For each lambda, define a nonnegative test martingale terminal value

    E_lambda = product_b [1 + lambda*(X_b-tau)/(tau-L)].

When X_b >= L and the validation blocks are iid conditional on a fixed
model r, each factor has expectation <=1 under the null; the product has
expectation <=1. Average the E_lambda values into an e-value E_mix,
which also has null expectation <=1. Markov then gives

    P_V(E_mix > 1/a | fixed unsuccessful component) <= a.

The code uses a=0.002 and compares in log space. The upper bound U is
needed for a predeclared finite-range score contract and inspection,
though the betting supermartingale itself uses the lower bound L.

Certify refit r only when ALL group x contrast e-values exceed 1/a.
This intersection-union test has false-certification probability <=a
for any fixed truly unsuccessful refit because at least one component
null is true. No independence across groups/contrasts is needed.

This is a finite-sample test under the stated bounded iid-block model.
It is not based on a small-B Student-t approximation. It may still be
extremely underpowered for small ecological score gains.

## Step 2: Explicitly control the common-validation shock

Write S(r)=1 for true all-cell success and Y(r,V)=1 for certification.
Let p=P_r(S=1). For p<1 define

    h(V) = P_r(Y=1 | S=0, V).

The component-size guarantee gives E_V h(V) <= a.
By Markov's inequality,

    P_V(h(V) > a/delta) <= delta.

On the complementary event set c=a/delta<1. Then

    theta(V) <= p + (1-p)*h(V) <= p+(1-p)*c.

Thus p >= max(0,(theta(V)-c)/(1-c)). With R iid refits
CONDITIONALLY on V, the exact one-sided Clopper-Pearson lower confidence
bound L_CP(K,R;alpha_p) covers theta(V) with probability >=1-alpha_p.

Consequently,

    L_p = max(0, (L_CP(K,R;alpha_p)-c)/(1-c))

is a lower confidence bound for the true future-refit success probability p
with overstatement probability <= delta+alpha_p.

Frozen experimental defaults:

    component a          = 0.002
    validation delta      = 0.025
    process alpha_p       = 0.025
    common-shock cap c    = 0.08
    total confidence tail <=0.05

Crucially, the component test level does NOT decrease with R.
The validation sample is shared across refits, but its shared-failure
possibility is explicitly paid for through c and delta.

The mathematical ingredients (e-values/test martingales,
intersection-union tests, exact binomial intervals, Markov and union
bounds) are classical. The combination is a narrowly scoped candidate
for ODSP and is NOT represented as a newly proven general theorem.

## Exact feasibility (not inferential qualification)

With the defaults, minimum certificates to REPORT lower p>0.8:

| R iid refits | Required K | Best possible corrected bound | Distinct validation blocks if 2 groups x 12 blocks |
|---:|---:|---:|---:|
| 8  | impossible | 0.598 | 24 |
| 15 | impossible | 0.763 | 24 |
| 20 | 20 | 0.817 | 24 |
| 30 | 29 | 0.874 | 24 |
| 36 | 35 | 0.894 | 24 |
| 50 | 47 | 0.923 | 24 |
| 72 | 66 | 0.946 | 24 |
| 100 | 90 | 0.961 | 24 |

The number of score computations grows with R; the number of DISTINCT
validation blocks does not. This is a mathematical budget comparison with
the iid-validation v3 requirement (20 x 2 x 12 = 480 distinct blocks).
It does not guarantee that 12 blocks can actually certify anything.

If the true future-refit reliability is 0.9 and the certification rule were
perfectly sensitive and specific, R=20 would still require all 20 observed
refits to succeed. The chance of this is only 0.9^20 ~= 12.2 percent.
The problem is not solved by a nicer p-value.

Because the validation sample is shared, K has a MIXTURE OF BINOMIALS
unconditionally. Thus it is invalid to calculate unconditional decision
power as a simple Binomial(R, marginal certificate probability), even when
the inference bound itself is valid. A prospective joint simulation of the
shared validation sample and training process is needed to measure power.

## Required assumptions and fail-closed boundary

The mathematical proof needs ALL of:

- iid frozen training-process refits, independent of the held-out V;
- iid validation *blocks* within each group, conditional on any fixed refit;
- group, contrast, block, weight and scoring boundaries fixed pre-outcome;
- score bounds guaranteed for every possible process model/validation draw;
- model selection, hyperparameter tuning and process changes never using V;
- no post-result selection of a, delta, R, B, tau, or score representation.

The module checks shapes, block counts, positive weights, finite observed
support bounds, manifest ID syntax and the alpha budget. It cannot
attest to iid sampling, prospective timeline or the full score bounds;
those verification flags remain false.

A GROUP with spatially autocorrelated sites or repeatedly sampled
individuals does not satisfy iid-block sampling merely because its blocks
have different IDs. If the validation support is a fixed finite census and
no iid target distribution is defensible, this route is inappropriate.

This route does not replace qualified v5 process-mean or source-process-v0
inference; nor can it convert their existing endpoint scores to this new
block-uniform population estimand without explicit justification.

## Next prospective gate

Before any attempt to register:

1. Freeze a scientifically interpretable score scale, bounds L/U, ecological
   group/block sampling process, training/process ID and gain tolerance.
2. Freeze at least six known-p simulation worlds: two/three true-success
   probabilities, normal versus heavy-tailed within allowed bounds,
   one exactly-null contrast with other strongly positive contrasts,
   and a common-shock negative control. Freeze null-calibration size,
   coverage and DECISION POWER gates before running any outcomes.
3. Measure the joint R x validation-block/B tradeoff and compare against
   iid-validation v3; unlike iid v3, simulate V once per world and
   reuse across refits.
4. Introduce ODSP-managed model-to-score provenance, untouched validation
   access receipts, independent-process evidence and implementation identity
   before any primary confirmatory claim.
5. If a frozen gate fails, retain the failed version. Do not tune its alpha
   split or positive-effect strength retrospectively.

This is currently an unqualified raw evaluator plus proofs and unit tests,
not a reported success-probability claim for an ecological population.


## Small-signal feasibility: the important negative result

The strong +0.95 synthetic test is only a numerical positive control.
It should never be confused with the magnitude of genuine ecological
predictive gains. The deterministic helper constant_block_gain_example
asks how many independent blocks per group would make the FROZEN mixture
e-test reject when every block, implausibly, produces exactly the same
positive gain. This is an illustrative extreme, not a power forecast.

For a lower score-gain bound L=-1, tau=0, and a=0.002:

| Same positive gain in every block | Blocks per group for e > 1/a | Two-group distinct block count |
|---:|---:|---:|
| +0.02 | 376 | 752 |
| +0.045 | 169 | 338 |
| +0.05 | 153 | 306 |
| +0.10 | 78 | 156 |
| +0.20 | 41 | 82 |
| +0.50 | 19 | 38 |
| +0.95 | 11 | 22 |

These gains must be on the SAME bounded score-difference scale; the +0.045
number is not a conversion from the Serengeti observed LOG-score gain.
Any such conversion would be invalid without original per-event scores.

**Consequence:** with small, bounded information gains, requiring 300+
independent validation blocks remains possible even after eliminating
the refit-by-refit multiplicity penalty. The 24-block illustration above
is therefore not a practical success claim. One can certify a small
positive expected gain much more readily than high process reliability
of positive gains in ALL components. This route must meet a realistic
effect-size and block-budget gate before being considered for use.


## First prospectively frozen known-p statistical panel: completed 2026-10-08

The plan was committed as
ODSP_FUTURE_REFIT_SHARED_EVALUE_V0_SIMULATION_PLAN.json
at commit 0060a038, BEFORE the first output was generated. The
implementation and workflow were then frozen at 2c8700df. The first
official GitHub Actions run was 37715294839 (job 113110265206);
the immutable artifact is 11523267832. Its after-outcome copy is
FUTURE_REFIT_SHARED_EVALUE_V0_FIRST_STATISTICAL_PANEL_RECEIPT.json.
The receipt records the original plan hash, original code SHA, artifact
ZIP SHA256 and the fact that it is POST-OUTCOME.

All 11 predeclared synthetic scenarios passed their FROZEN gates.
Each scenario used 1,000 worlds and did not change the core method
or gate after exposure.

| Known true process p | Validation design | Reported overstatement frequency |
|---:|---|---:|
| 0.00 | symmetric, 12 blocks/group | 0.001 |
| 0.50 | symmetric, 12 blocks/group | 0.004 |
| 0.80 | symmetric, 12 blocks/group | 0.009 |
| 0.80 | rare-negative, 12 blocks/group | 0.007 |
| 0.95 | rare-negative, 12 blocks/group | 0.000 |
| 0.80 | small gain, 12 blocks/group | 0.000 |
| 0.80 | small gain, 200 blocks/group | 0.008 |

The preregistered coverage threshold was <=0.063784 and the
any-false-refit-certificate panel threshold was <=0.009.
All seven coverage scenarios met both.

Decision power to certify p>0.8 in the two required p=1 worlds:
strong normalized gain +0.9 at 12 blocks/group, 1.000;
small gain +0.05 at 200 blocks/group, 1.000.
But the separately frozen small-gain/12-block diagnostic was 0.000.
These strong and small-gain simulations are SIMPLE synthetic bounded
score generators; they are not representative evidence of performance
on real ecological validation samples.

The invalid-design sentinel, which intentionally made all validation
blocks perfectly correlated while keeping block IDs distinct, returned
overstatement frequency 0.498. This is a FAILED validity setting as
expected, NOT evidence that the method works without iid blocks. It
makes the physical independent-block assumption indispensable.

This panel establishes *calibration in the frozen known-truth worlds*,
not universal finite-sample empirical validity. The theoretical proof
is conditional on its explicit bounded iid-block and process assumptions.
No claim of real-data untouched external success probability is allowed.
The numerical evaluator stays experimental_unqualified; the active
route registry and all previously failed and qualified endpoints remain
unchanged.

First-run evidence:
https://github.com/zuizui0223/odsp/actions/runs/37715294839
