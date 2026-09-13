# Predictive resolution decomposition

## Question

A positive held-out gain over a pooled comparator can arise for different reasons. A model may exploit a broad stratum shift (for example species identity), finer within-stratum context, or both. A single conditional-versus-marginal gain cannot distinguish those sources.

ODSP therefore permits an **ordered predictive resolution ladder** evaluated on the same held-out outcomes:

```text
q0(A | C0) -> q1(A | C1) -> ... -> qK(A | CK)
```

with nested information sets

```text
Ck = (C{k-1}, Zk).
```

Examples include

```text
pooled -> species -> site -> season -> full covariate model
pooled -> guild -> individual -> full movement model
pooled -> region -> species -> microclimate model
```

The levels are scientific comparators, not automatically selected model stages.

## Held-out decomposition

For a held-out row `i`, let `s_ik` be the predictive score supplied by level `k`, with larger values meaning better prediction. Define the adjacent increment

```text
delta_ik = s_ik - s_i{k-1}.
```

For any independent group `g`, using the same held-out rows and weights at every level,

```text
Delta_g(qK : q0)
  = mean_g(s_K - s_0)
  = sum_k mean_g(s_k - s_{k-1}).
```

This telescoping identity is exact. It does not require a particular learner or state geometry. Any commensurate row-wise proper score can be used. ODSP reports the total group gain, every adjacent increment, the numerical additivity error, the conservative sign category for total gain, and the sign category for each resolution increment.

The implementation is `odsp.predictive_resolution.decompose_predictive_resolution`.

## Log-score information identity

The logarithmic score has an additional population interpretation. Let `p_k(A|C_k)` be the true conditional distribution and `q_k(A|C_k)` the fitted predictor at resolution level `k`. Define

```text
D_k = E[ KL{ p_k(.|C_k) || q_k(.|C_k) } ].
```

Then the expected log-score increment is

```text
G_k
 = E[ log q_k(A|C_k) - log q_{k-1}(A|C_{k-1}) ]
 = I(A ; Z_k | C_{k-1}) - D_k + D_{k-1}.
```

Therefore:

1. **Oracle case.** If both adjacent predictive distributions equal the truth, `D_k = D_{k-1} = 0`, so

   ```text
   G_k = I(A ; Z_k | C_{k-1}) >= 0.
   ```

   The resolution increment is exactly the conditional mutual information added by `Z_k`.

2. **Fitted-model case.** A held-out increment is not conditional mutual information by itself. It combines the information available at the added resolution with the change in predictive approximation error.

3. **Negative increment.** Because oracle conditional mutual information cannot be negative, a negative held-out increment must not be described as “negative ecological information.” It means that the richer predictive representation performed worse than the lower-information comparator on the independent evaluation distribution. Under the population identity, this occurs when the increase in predictive approximation error exceeds the oracle information increment; finite-sample variation or transfer shift can produce the same empirical sign.

This distinction is central to interpreting a pattern such as

```text
total pooled-comparator gain > 0
species increment             > 0
within-species context gain   < 0.
```

The correct conclusion is that the broad species-level shift transferred, while the fitted finer context did not add transferable predictive utility. It is not evidence that within-species context contains intrinsically negative information.

## Known-truth benchmark

`run_predictive_resolution_benchmark()` uses an exactly enumerated binary system with a strong species effect and a weaker context effect.

With oracle predictors the two expected increments are positive:

```text
pooled -> species          0.14321854481691187 nats
species -> species+context 0.014032432883159807 nats
```

A deliberately misspecified richest predictor reverses the context effect while retaining the species effect. Its expected KL penalty relative to the oracle full predictor is

```text
0.07190509252064392 nats.
```

The realized context increment is therefore

```text
0.014032432883159807 - 0.07190509252064392
= -0.057872659637484114 nats,
```

while the total pooled-comparator gain remains positive:

```text
0.14321854481691187 - 0.057872659637484114
= 0.08534588517942776 nats.
```

Thus the positive-total / negative-fine-context pattern can arise under a fully known generating process for exactly the reason implied by the identity above.

## Design rules

The decomposition is valid only when the ladder is specified coherently.

- All levels must be scored on the **same realized held-out rows**.
- The same row weights and independent-group definition must be used across levels.
- Comparator levels should be declared before inspecting their held-out signs when the analysis is confirmatory.
- Every intermediate comparator must assign finite score to every positive-weight held-out row. ODSP fails closed if an intermediate log-score comparator assigns zero predictive density/mass. The richest final predictor may assign zero density/mass; that is retained as a predictive failure (`-inf`).
- A large pooled mean cannot rescue a conflicting independent group. Group sign classification remains separate from event-count pooling.
- Log-score increments may be interpreted as conditional information only in the oracle limit. Fitted held-out increments are **realized transfer increments**.
- Other proper scores retain the predictive telescoping decomposition but do not inherit the Shannon conditional-mutual-information interpretation.

## Relation to the fitted-classifier workflow

`odsp.workflow.cross_validate_state_events` remains a convenience layer that fits discrete-state reference learners and constructs pooled/stratum baselines from training data. The predictive-resolution layer is lower-level and model-agnostic: users may keep their own modelling stack and provide held-out score vectors directly.

The existing two-step decomposition

```text
pooled -> stratum -> model
```

is therefore a special case of the general resolution ladder, not a separate estimand.
