# N2 failure-mode manuscript spine v1

## Working title

**Predictive skill can misidentify information transfer in hierarchical ecological data**

## One-sentence paper

A model can predict held-out data better than a pooled reference for the wrong
informational reason: layer identity can be credited to contextual information,
and matching the reference to the claim separates those contributions.

This is not an ODSP-framework paper. ODSP is the implementation used to make the
score accounting explicit and reproducible.

## Opening example

Open with the already observed *Buteo buteo* decomposition, but label it
immediately as a post-outcome motivating example.

The frozen pooled-reference mean gain is +0.23031 nats/event. Replacing the
pooled state marginal with the training-fold species marginal contributes
+0.27362, whereas the residual within-species context contribution is -0.04331.

The point is not that this one species proves a general failure. The point is
that a perfectly valid held-out improvement can answer a broader question than
the biological interpretation attached to it.

That motivates the known-truth experiment.

## Introduction logic

### Paragraph 1 — predictive validity is not information attribution

Independent validation is designed to ask whether a model predicts new data.
Ecological papers frequently go one step further and interpret the improvement
from adding a variable or context as evidence that the added information itself
transfers.

Those are different claims.

### Paragraph 2 — the comparator creates the failure mode

Suppose observations are nested within species, regions, populations or other
layers. A full model can exploit both layer identity and within-layer context.
If its held-out score is compared with a pooled reference that knows neither,
the resulting gain contains both sources:

```text
Delta_total
    = S(full) - S(pool)
    = [S(layer) - S(pool)]
      + [S(full) - S(layer)]
    = Delta_layer + Delta_context.
```

A positive total gain therefore does not imply a positive context gain.

### Paragraph 3 — two routes to the same mistake

There are two practically different failures.

1. **Explicit-layer failure.** The model directly contains species/region/etc.,
   but the reference is pooled. Its identity contribution is then automatically
   included in the reported improvement.

2. **Proxy-layer failure.** The model omits layer identity, but the purported
   context covariate is correlated with that layer. Context then predicts the
   layer and inherits part of its signal even when true within-layer context
   information is zero.

Independent-group cross-validation does not remove either problem because both
can generalize perfectly to held-out observations. The error is in what the
score contrast means, not in reuse of observations.

### Paragraph 4 — tests and falsification

State that Stage 1 was frozen before execution and was allowed to kill or narrow
the claim. It varied layer effect, true within-layer context effect, number of
groups, observations, number of layers, layer-context correlation and whether
the learner saw the layer.

Stage 2 was frozen after Stage 1 and before opening the fresh Palmer Penguins
result. BOP was read-only motivating evidence; Penguins was the fresh proxy test;
Snapshot Serengeti was a semantic negative control where identity itself was the
claim.

## Methods

### 1. Claim-aligned references

The reference distribution is determined by the information claim, not by the
most convenient null model.

If the claim is “context transfers beyond species”, the lower-information
reference must already know species.

If the claim is “species identity transfers”, an identity-blind pooled reference
is exactly the relevant comparator.

This distinction is the conceptual method.

### 2. Additive decomposition

For the same full predictor, report all three held-out quantities:

```text
Delta_layer   = S(layer) - S(pool)
Delta_context = S(full)  - S(layer)
Delta_total   = S(full)  - S(pool)
```

and verify

```text
Delta_total = Delta_layer + Delta_context.
```

The score is held-out mean log predictive probability.

For proxy cases the naive context-only learner and the layer-aware audit learner
are different fitted models, so do not call their contrast an algebraic
decomposition. Treat it as a predeclared audit of whether the original context
claim survives once layer identity is made explicit.

### 3. Stage 1 — known truth

Use the frozen contract verbatim. The primary mechanistic results are the
confirmatory anchors; the 864-cell factorial map describes scope.

Do not foreground the historical ODSP certification machinery.

The decision is based on the mean group gain and its predeclared interval, never
on the old all-group unanimity rule.

### 4. Stage 2 — real-data triangulation

#### BOP_RODENT

No refit and no raw-data re-access.

Use the frozen decomposition and corrected four-species uncertainty.

At the population level, total mean +0.57091 has corrected 95% interval
[-0.29300, 1.43482], so it is **uncertain**, not a positive result.

Use *B. buteo* only as the motivating descriptive point decomposition.

#### Palmer Penguins

Fresh result, opened once after the Stage-2 contract was merged.

Naive question:
“Does morphology predict island better than a pooled island marginal?”

Audit question:
“Does morphology add island information after species is already known?”

Year is the held-out fold and the dependence cluster. There are only three
years, so intervals use CR1 cluster-robust SE with t(2).

#### Snapshot Serengeti

Do not reanalyse it as a failure candidate.

Its declared question is whether species identity predicts detected time.
Therefore species-blind pooled time is the scientifically correct
lower-information reference.

Its three held-out gains remain positive. This is the boundary case that stops
the paper from becoming “always condition everything”.

### 5. Implementation

One short subsection only.

ODSP receives held-out scores or runs explicit prediction contracts, records the
information filtration and produces pooled versus conditioned score components.
The software is supporting infrastructure rather than the scientific novelty.

## Results

### Result 1 — pooled references create false transfer at realistic layer effects

Lead with the confirmatory anchors.

At the BOP-calibrated layer effect:

- explicit-layer null-context anchor A: pooled false-transfer rate = **1.000**;
- proxy-layer null-context anchor B: pooled false-transfer rate = **1.000**;
- both Wilson 95% lower bounds = **0.996**;
- conditioned context false-transfer rate = **0.000** in both.

Negative control C, where the layer is omitted and context is not correlated with
it:

- pooled false-transfer rate = **0.000**;
- conditioned false-transfer rate = **0.001**.

This triangulates the mechanism cleanly.

### Result 2 — the failure occupies a broad parameter region

Among 162 failure-relevant null cells:

- mean pooled positive-declaration rate = **0.896**;
- median = **1.000**;
- **89.5%** of cells have false-transfer rate > 0.5;
- mean conditioned-context false-transfer rate = **0.00106**;
- maximum conditioned rate = **0.03125**.

Among the 54 cells whose oracle layer gain lies in the preregistered BOP-realistic
0.20–0.35 nats window:

- mean pooled false-transfer rate = **0.951**;
- **94.4%** of cells exceed 0.5;
- mean conditioned false-transfer rate = **0.000289**.

### Result 3 — conditioning does not destroy sensitivity to true context

For true within-layer context effect 0.5:

- correlated context power = **0.959**;
- uncorrelated context power = **1.000**.

At high information, absolute mean context bias is approximately 5e-5 nats in
the correlated anchor and 2e-5 in the uncorrelated anchor.

The correction therefore does not work merely by becoming unable to declare
transfer.

### Result 4 — a fresh real dataset reverses exactly as predicted

This is the empirical centerpiece.

For 342 complete Palmer Penguins observations across three years:

**Naive morphology vs pooled island reference**

```text
mean gain = +0.38946
95% CR1+t2 interval = [0.27893, 0.49998]
status = positive
```

**Layer component: species vs pooled**

```text
mean gain = +0.53601
95% interval = [0.47989, 0.59214]
status = positive
```

**Corrected context: species+morphology vs species**

```text
mean gain = -0.08375
95% CR1+t2 interval = [-0.09022, -0.07727]
status = nonpositive
```

So the predeclared outcomes all fire:

- point sign reversal: yes;
- inferential downgrade: yes;
- >50% attenuation: yes.

The result is stronger than merely “the effect got smaller”: the biological
interpretation changes sign.

### Result 5 — the rule is claim-dependent, not anti-pooling

Snapshot Serengeti remains a positive semantic control.

The claimed information was species identity itself, so comparing
P(time | species) with species-blind P(time) is the correct contrast. Its three
held-out gains were +0.05724, +0.04516 and +0.04514.

Thus the prescription is not “never pool”. It is:

> **The reference must already contain every information layer that is not part
> of the transfer claim being tested.**

## Discussion

### 1. Cross-validation can validate the wrong interpretation

The key distinction is between predictive generalization and attribution of that
generalization to a named information source.

Both explicit layer identity and a stable proxy for layer identity can
generalize to new groups. Group CV therefore does not solve a comparator
mismatch.

### 2. The failure can be large

In Stage 1 the false-transfer rate was effectively certain at BOP-scale layer
effects. In Penguins, the real-data correction crossed all the way from positive
to negative.

This makes the issue more than a technical choice of baseline.

### 3. But conditioning is not universally preferable

Serengeti is essential here.

If species identity is itself the scientific information of interest, removing
it from the contrast destroys the question rather than improving it.

The method is therefore **claim-aligned reference selection**.

### 4. Implication for ecological prediction and esdm

Whenever a richer model adds multiple information sources—species identity,
movement capacity, activity time, interaction structure, spatial history—the
reported held-out gain cannot automatically be attributed to the focal addition.

For esdm, candidate information layers such as environment, traits, movement,
activity time and interactions should be scored as explicit information
contrasts. When no natural order exists, order sensitivity can be audited, but
that is downstream of the present paper and should not expand N2.

### 5. Limits

- Stage 2 is empirical triangulation, not an estimate of literature prevalence.
- BOP has only four species clusters, so its population-level intervals remain
  broad.
- Penguins has only three year clusters, although the sign reversal is stable
  across their CR1+t2 contrast.
- Conditioning separates score contributions; it does not identify biological
  causality.
- Observation and detection processes remain system-specific.

## Figures

### Figure 1 — How predictive skill acquires the wrong label

Three-panel conceptual figure:

A. explicit layer in model + pooled reference;
B. context as proxy for omitted layer;
C. claim-aligned reference.

This should be visually simple enough to understand before equations.

### Figure 2 — Known-truth failure map

A. Anchor A/B/C paired false-positive rates.
B. Factorial pooled-reference null failure surface.
C. Same surface after layer-conditioned decomposition.
D. Power/bias under true context effects.

### Figure 3 — Real-data triangulation

A. Penguins naive, layer, corrected-context and audit-total gains with intervals.
B. *Buteo buteo* descriptive point decomposition.
C. Serengeti as semantic control, labelled explicitly as a different claim.

## Table 1 — Comparator semantics

Columns:

- system;
- prediction target;
- layer;
- focal claimed information;
- naive reference;
- claim-aligned reference;
- role in paper;
- outcome.

## What stays out of the main paper

Tawaki, bat, MH Antwerpen, lattice certification history, provenance machinery
and the superseded framework manuscript stay in supplement/repository history.

They must not be used to make the new paper look broader at the cost of a less
precise central claim.

## Manuscript endpoint

The paper succeeds without Stage 4.

Published-study reanalysis may later strengthen scope, but it cannot change the
core conclusion already established by preregistered known truth plus a fresh
real-data reversal and a semantic negative control.
