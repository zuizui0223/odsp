# N2 reference-to-claim alignment manuscript spine v2

## Working title

**Claim-aligned reference models isolate transferable predictive information in hierarchical ecological data**

## Scientific object

This paper is not about a software framework and is not organized as a catalogue of failure modes.

Its object is a constructive inferential rule:

> **A predictive gain is defined relative to a reference. Therefore, the scientific meaning of that gain is defined by what information the reference already contains.**

When the claim is “context transfers beyond species identity”, species belongs in the reference. When the claim is “species identity transfers”, species must not be conditioned away. The same predictive model can therefore support different scientifically valid score contrasts, but those contrasts answer different questions.

We call this **reference-to-claim alignment**.

## Why this is more than baseline selection

Forecasting work already shows that baseline choice changes relative skill and model ranking. Structured cross-validation work shows that ecological dependence must be respected in train/test partitioning. The present problem is orthogonal to both.

The issue is not merely whether a baseline is difficult or fair, and not merely whether validation units are independent. The issue is **which predictive information increment a score contrast represents**.

For nested information sets,

```text
pool ⊂ layer ⊂ layer + context
```

the same held-out full-model score admits

```text
S(full) - S(pool)
  = [S(layer) - S(pool)]
  + [S(full) - S(layer)].
```

The total contrast asks whether the joint bundle transfers beyond pooling. The second contrast asks whether context transfers after layer identity is already known. Neither is universally “correct”; the claim determines the estimand.

With log score and oracle conditional distributions, this has an information-theoretic analogue in conditional information. In finite ecological data we keep the operational interpretation narrower: realized held-out predictive increments under explicit references.

## Evidence architecture

### Stage 1 — identification, not failure hunting

Use the already frozen known-truth experiment as an identification test of the principle.

Three null cases:

1. **Layer information enters explicitly.** A full learner sees layer + context, true context information is zero, and a pooled reference lacks the layer.
2. **Context proxies layer identity.** A context-only learner can recover stable layer information because context and layer are correlated, while true within-layer context information is zero.
3. **Negative control.** Layer is omitted and context is uncorrelated with layer.

The reference-alignment prediction is precise:

- pooled score gain can be positive in cases 1–2;
- a layer-conditioned context increment should remain null;
- both should remain null in case 3.

The frozen results match these predictions. At the BOP-scale layer effect, cases 1 and 2 have pooled positive-declaration rate 1.000 with Wilson lower bound 0.996, while the conditioned context rate is 0.000. The negative control is 0.000 pooled and 0.001 conditioned.

### Stage 1 power — alignment still detects real information

A constructive method must not “work” by suppressing all positive results.

When context truly carries within-layer information, the conditioned increment has power 0.959 under correlated context and 1.000 under uncorrelated context. High-information bias is tiny.

This is one of the strongest positive results in the paper: claim alignment is selective rather than merely conservative.

### Metric diagnostic

Groupwise AUC is largely insensitive to this intercept-like layer signal: positive-declaration rates 0.062 and 0.041 at the two primary null anchors, while log score and accuracy declare improvement in 1.000.

Do not frame AUC as the solution. Use this result to show that **metric choice and information attribution are distinct design decisions**. A ranking metric can be blind to one kind of reference mismatch without resolving the scientific contrast.

### Stage 2 — fresh sign reversal

Palmer Penguins is the empirical centerpiece.

Naive question:

> Does morphology predict island better than a pooled island distribution?

Answer: yes. Mean held-out log-score gain +0.38946, CR1+t(2) interval [0.27893, 0.49998].

Claim-aligned question:

> Does morphology add transferable island information after species identity is already known?

Species alone contributes +0.53601 against pooling. The morphology increment beyond species is -0.08375, interval [-0.09022, -0.07727].

The result is not “a model failed”. The result is that **two valid score contrasts answer two different claims and have opposite signs**.

Keep the limitation explicit: three collection years imply df=2. This constrains superpopulation certainty, but the observed sign separation is not hidden.

### Buteo — motivating decomposition

Keep *Buteo buteo* as a descriptive opening example, not confirmatory evidence.

+0.23031 total pooled gain =
+0.27362 species component +
-0.04331 within-species context component.

Its function is to make the estimand problem intuitive before the known-truth test.

### Serengeti — semantic boundary control

Snapshot Serengeti prevents the paper from becoming “condition everything”.

Its claim was species identity itself. Therefore the species-blind time distribution is the correct lower-information reference. The three positive held-out gains remain valid evidence for that declared information transfer.

This boundary control is central to the positive paper because it shows the rule is **alignment**, not conditioning.

## Proposed Introduction

1. Predictive evaluation is increasingly central to ecology, and held-out scoring is an important discipline.
2. Every skill measure is a contrast against a reference; the reference is usually treated as a technical baseline.
3. For hierarchical ecological questions, the reference also defines the **scientific information increment**. A pooled reference and a species-conditioned reference answer different questions.
4. Existing structured-CV work addresses data dependence, while baseline-selection work addresses fairness/ranking. Neither by itself specifies which information must already be in the reference for a named transfer claim.
5. Introduce reference-to-claim alignment and three falsifiable predictions.
6. State the evidence architecture: known truth, power, fresh Penguins reversal, Serengeti semantic boundary.

Do not open with “prediction can be misleading”. Open with the positive idea that prediction can be decomposed into scientifically interpretable increments.

## Proposed Methods order

### 2.1 Reference-to-claim alignment

Define the scientific claim as the focal information block X beyond already-assumed information Z.

The operational estimand is

```text
G(X | Z) = S(q(Y | Z, X)) - S(q(Y | Z)).
```

For a pooled reference,

```text
G(Z, X) = S(q(Y | Z, X)) - S(q(Y)),
```

which is a joint information claim, not an X-beyond-Z claim.

### 2.2 Nested held-out score accounting

Show exact finite-sample additivity when the same full predictor and nested references are scored on the same held-out rows.

Keep proper-scoring-rule interpretation separate from causal interpretation.

### 2.3 Known-truth identification experiment

Describe the already frozen Stage 1 design without leading with “false positive”. Call the null anchors **identification controls** and the positive-context anchors **sensitivity controls**.

### 2.4 Fresh empirical test

Penguins as a predeclared sign-discrimination test between pooled and claim-aligned contrasts.

### 2.5 Semantic boundary control

Serengeti.

### 2.6 Implementation

One short paragraph. ODSP is the implementation, not the novelty.

## Proposed Results order

### Result 1 — claim-aligned increments recover the correct information source under known truth

Lead with the paired 1.000→0.000 contrast and negative control.

### Result 2 — the aligned increment retains power for genuine context

Lead with 0.959–1.000 power and small bias.

### Result 3 — the naive and aligned questions can differ across a broad parameter region

Use the 162-cell / BOP-realistic summaries.

### Result 4 — empirical sign reversal in Palmer Penguins

Make this the main real-data figure.

### Result 5 — score metric and reference semantics are not interchangeable

AUC diagnostic.

### Result 6 — pooling is correct when identity itself is the claim

Serengeti.

## Proposed Discussion

### Predictive validation versus predictive attribution

Cross-validation answers whether prediction generalizes under the chosen data split. Reference alignment determines what the score gain is **about**.

### A reference is part of the estimand

Treat reference choice like target definition, not like a plotting baseline.

### A practical workflow

Before fitting or scoring:

1. state the focal information claim;
2. list information assumed as already known;
3. build the reference using exactly that assumed information;
4. score the richer predictor on the same held-out rows;
5. if information sets are nested, report all adjacent increments plus the total;
6. if the hierarchy is scientifically ambiguous, report multiple declared contrasts rather than silently selecting one.

### Scope

The method is useful when models combine multiple information layers: species, site, region, traits, movement, activity time, interactions, spatial history.

### Limits

No claim about prevalence in published ecology. No causal attribution. Three Penguins clusters. Four BOP species clusters. Scientific hierarchy is declared, not inferred by software.

## Figures

### Figure 1 — One prediction, different claims

A simple information ladder:

```text
pooled → identity → identity + context
```

Show which subtraction corresponds to which scientific sentence.

### Figure 2 — Identification and power under known truth

A/B/C null controls, factorial scope, true-context power, AUC diagnostic.

### Figure 3 — Real-data discrimination and boundary

Penguins sign reversal, Buteo descriptive decomposition, Serengeti identity-as-claim control.

## Table 1

**Scientific claim determines the lower-information reference**

Columns:

- system;
- outcome;
- information already assumed;
- focal information;
- lower-information reference;
- richer predictor;
- held-out increment;
- interpretation.

## Manuscript endpoint

The paper does not need a literature-prevalence Stage 4 to support its core claim.

A published-study audit could later estimate how often ecological papers use references misaligned with their verbal claim, but that would answer a different question: prevalence rather than identification.

The present paper is complete when the constructive principle, known-truth identification, power preservation, fresh sign reversal and semantic boundary are all visible in one coherent narrative.
