# N2 generality proof — 2026-09-04

## Scope of the claim

The N2 core is not claimed to be a universal biological law. Its generality is narrower and testable:

> For any finite non-negative ecological support tensor with declared base axes `B` and added axes `A`, the N2 thickness, organization and conditional-versus-marginal transferability quantities depend on the normalized base-added distribution rather than on the biological names, array order, category labels or arbitrary total mass of those axes.

This statement covers discrete representations of height, depth, time, season, behaviour, substrate, microhabitat, life stage, sensor-defined state or any other declared axis. Whether a particular representation is biologically meaningful remains an observation-design question.

## 1. Positive-mass scaling invariance

Let a support field be `S` and let `c>0`. Normalization gives

`p_i(cS) = c S_i / sum_j c S_j = S_i / sum_j S_j = p_i(S)`.

Therefore every entropy, conditional entropy and mutual information computed from the normalized support is unchanged by positive scaling. The held-out score is also unchanged if model and held-out fields are independently multiplied by positive constants because the model probabilities and held-out evaluation weights are normalized separately.

This means the generic core is indifferent to whether equivalent support is represented as probability mass, relative weight, integer counts multiplied by a constant, or another positive rescaling.

## 2. Axis-permutation equivariance

Permuting tensor axes is a bijection of joint states. If the axis IDs supplied to the estimator are remapped with the same permutation, the probability assigned to every semantic state is unchanged. Shannon entropy is invariant to a bijection of state labels, so

`H(A|B)`, `I(A;B)` and `E[log P(A|B)-log P(A)]`

are invariant under tensor-axis order.

Thus the core does not privilege `x`, `y`, `z` or `t` by their numeric array position. The only privileged concept is the caller-declared distinction between base and added axes.

## 3. Category-label invariance

Within an axis, relabelling categories by any permutation is again a bijection of states. Entropy and mutual information depend on probability masses, not category names. When model and held-out representations use the same relabelling, the conditional and marginal log scores are also unchanged.

Consequently, the calculations do not depend on whether a time bin is encoded as `0..5`, named dawn/day/etc., or permuted arbitrarily; nor do they depend on arbitrary IDs for height strata, behaviours or habitat states.

## 4. Omitted-nuisance marginalization invariance

Suppose every state `(B,A)` is refined by an additional axis `U`, with non-negative submasses satisfying

`sum_u S(B,A,u) = S(B,A)`.

If `U` is not declared as a base or added axis, the N2 functions marginalize it before evaluating the base-added quantities. The resulting joint distribution over `(B,A)` is exactly the original distribution. Therefore thickness, organization and transferability are unchanged.

This property is important for data models that carry additional instrument, replicate, provenance or other axes that are not part of the ecological estimand.

## 5. Same-distribution identity

For a model distribution evaluated on the same generating distribution,

`G = E[log P(A|B) - log P(A)]`

can be rewritten as

`G = sum_{a,b} P(a,b) log [P(a,b)/(P(a)P(b))] = I(A;B)`.

Therefore the held-out transferability statistic has an exact reference value: under perfect distributional transfer its expectation equals the fitted base-added mutual information. This is not a heuristic analogy; it is the mutual-information identity itself.

The deterministic generality benchmark verifies this equality across randomly generated positive tensors with 2–6 dimensions, arbitrary axis placement and one or two axes in each of `B` and `A`.

## 6. Composition of conditionally independent added axes

If two added axes satisfy `A1 independent of A2 | B`, then the chain rule gives

`H(A1,A2|B) = H(A1|B) + H(A2|B)`.

Exponentiating both sides yields

`exp H(A1,A2|B) = exp H(A1|B) * exp H(A2|B)`.

Thus effective-state thickness composes multiplicatively for conditionally independent added dimensions. The benchmark generates random conditional distributions with 2–6 states per axis and verifies both the additive information identity and the multiplicative effective-state identity.

## 7. Independent-group mass invariance

Each held-out group is scored after normalizing that group's support. Multiplying one group's counts by a positive constant therefore cannot change its gain. Terminal grouped classification uses the vector of per-group gains rather than pooled observation mass:

- all gains > tolerance -> `generalizing`;
- all gains <= tolerance -> `non_generalizing`;
- otherwise -> `mixed`.

Hence a large group cannot rescue a conflicting small group merely by contributing more rows. The benchmark verifies this with group masses differing by up to 14 orders of magnitude and separately verifies the same-process identity for 1, 3 and 7 independent groups.

## 8. Cardinality bound

For an added state space containing `K` joint discrete states,

`0 <= H(A|B) <= log K`,

so

`1 <= exp(H(A|B)) <= K`.

The randomized benchmark checks this bound under changing dimensionality, cardinality and axis placement.

## Executable stress test

`odsp.generality_benchmark.run_n2_generality_benchmark()` converts the proof obligations above into deterministic property tests. The default configuration uses seed `20260904` and 128 heterogeneous random tensors, plus separate conditional-independence and grouped-transferability families. The test suite requires every proof obligation to pass and requires the maximum numerical error to remain within floating-point tolerance.

The CLI `scripts/run_n2_generality_benchmark.py` can emit the complete per-check audit receipt as JSON.

## Empirical portability already demonstrated

The mathematical core is paired with three prospectively bounded empirical architectures that differ in much more than taxon name:

| Lane | Organisms | Observation architecture | Added-axis semantics | Independent unit / gate | Terminal state |
|---|---|---|---|---|---|
| Tawaki | diving seabird | linked GPS + dive records | dive depth | full site-year structural denominator | unavailable |
| European free-tailed bat | volant mammal | same-event 3D GPS | native height above mean sea level | whole sealed individuals | thick, non-generalizing |
| Snapshot Serengeti | terrestrial mammal community | camera detections + explicit effort intervals | source local clock time | deterministic held-out camera-site folds | thick, species-partitioned, generalizing |

This heterogeneity demonstrates portability across observation architectures, added-axis meanings and replication units. It does not estimate how frequent each terminal state is in nature.

## What is and is not now established

### Established strongly

1. **Axis-agnostic mathematical form.** The core works on arbitrary finite discrete base/added axis partitions, not only `x-y-z` or site-time arrays.
2. **Representation invariance.** Total mass, array order and arbitrary category labels do not change the estimand.
3. **Exact information identity.** Same-distribution held-out gain equals `I(A;B)`.
4. **Composable multidimensionality.** Conditionally independent added dimensions obey additive information and multiplicative effective-state identities.
5. **Replication-unit protection.** Group sample mass cannot determine a grouped terminal state.
6. **Heterogeneous empirical portability.** The same inferential hierarchy has operated under three distinct ecological observation architectures and has produced three different legitimate terminal outcomes.

### Not established, and should not be claimed

1. that all ecological niches are thick;
2. that most thick niches have transferable organization;
3. that temporal axes generalize more often than vertical axes;
4. that discretization is optimal for every continuous ecological variable;
5. that observation effort/detectability problems disappear after using information theory;
6. that the quantities identify causal competition, habitat preference or a fundamental niche;
7. that success on three empirical architectures proves universal biological frequency or mechanism.

The defensible manuscript claim is therefore **generality of the inferential machinery plus heterogeneous empirical portability**, not universality of the biological outcomes.
