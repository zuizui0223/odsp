# N2 stage 1 result — pooled-reference skill can impersonate context transfer

Stage 1 was executed once under
`N2_STRATIFIED_CONTEXT_TRANSFER_FAILURE_MODE_STAGE1_CONTRACT.json`.
The frozen one-shot result passed every predeclared success condition.

## Central result

When the true within-layer context effect was zero but layers differed at the
BOP-calibrated magnitude, a predictor evaluated against a pooled reference was
declared positively transferring in essentially every confirmatory replicate.

Two mechanisms produced the same error:

1. **explicit layer identity in the predictor** — the predictor legitimately knew
   the layer, but the pooled reference did not, so layer skill was credited to the
   richer representation as if it were context transfer;
2. **context as a proxy for omitted layer identity** — when context and layer were
   correlated, a context-only learner recovered part of the layer signal and again
   appeared to transfer relative to the pooled reference even though the true
   within-layer context effect was zero.

At the primary null anchors:

| Anchor | Pooled-reference positive rate | Layer-conditioned context positive rate |
| --- | ---: | ---: |
| explicit layer, context truth = 0 | 1.000 | 0.000 |
| correlated context proxy, context truth = 0 | 1.000 | 0.000 |
| omitted layer + uncorrelated context negative control | 0.000 | 0.001 |

The Wilson lower bound for the two 1000/1000 pooled-reference failure rates was
0.9962. Thus the failure was not a marginal threshold effect.

## The correction preserved real context signal

The additive score audit

```text
model - pooled
  = (layer - pooled)
  + (model - layer)
```

isolated within-layer context gain.

For a true context effect of 0.5, the layer-conditioned context component had
power 0.959 under correlated context and 1.000 when context was uncorrelated with
layer. At 300 events per group, mean bias relative to the oracle context
information gain was 5.18e-05 and 2.44e-05 nats/event, respectively.

Across all 576 positive-context factorial cells, the mean absolute context-gain
bias was 9.02e-04 nats/event and the maximum was 0.01173.

## The BOP-scale regime is not an extreme corner case

The deterministic BOP-like oracle layer gain was 0.266466 nats/event, inside the
predeclared 0.20–0.35 nats window.

Among the 54 null-context factorial cells in that layer-gain window that contained
one of the two failure mechanisms, the pooled-reference declaration rate averaged
0.9511; 94.4% of cells had a declaration rate above 0.5. The corrected context
declaration rate averaged 0.00029 and never exceeded 0.015625.

When layer was omitted **and** context was uncorrelated with it, the same
BOP-scale cells had a pooled-reference positive rate of only 0.00087. This
negative control localizes the failure to layer information or a proxy for layer,
rather than generic model flexibility.

## Group cross-validation does not solve the problem

The primary failure was present under independent-group cross-validation.
Random-row CV was not required to create it. At the confirmatory anchors,
random-row minus group-CV log-gain differences were small and slightly negative.

The problem is therefore not principally train/test leakage. It is a mismatch
between the **scientific claim** (“context transferred”) and the
**reference distribution** used to score the richer model.

## Metrics do not all fail in the same way

At both primary null failure anchors, group-CV log gain and accuracy declared
positive improvement in 100% of replicates. Groupwise AUC remained close to its
null behavior: 0.062 and 0.041 positive-declaration rates.

This does not make AUC a universal remedy. It shows that this particular
intercept-like layer failure affects calibration-sensitive scores and
classification thresholds differently from within-group ranking. Metric choice
cannot substitute for identifying the information source.

## Claim boundary

Stage 1 supports the methodological failure mode and its additive correction.
It does **not** establish how common the failure is in published ecological
models. Stage 2 must therefore ask how often pooled and layer-conditioned
references reverse the interpretation in real multi-layer datasets.

The old v6 framework manuscript remains superseded and must not be submitted.
ODSP is now implementation infrastructure for this test, not the scientific
center of N2.
