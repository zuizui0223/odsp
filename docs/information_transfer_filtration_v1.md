# Information-transfer filtration: interpretation and novelty boundary

## Why this layer exists

The low-level ODSP score ladder can compare any ordered predictive representations on the same held-out rows. That algebra alone does **not** make the order an information hierarchy.

An information interpretation requires declared nested information sets

```text
C0 ⊂ C1 ⊂ ... ⊂ CK.
```

`odsp.information_transfer` makes that assumption executable. Every level declares the variables available to it, and ODSP refuses to call a step an information-transfer step unless each information set is a strict superset of the preceding one.

Examples of valid filtrations are

```text
{} -> {species} -> {species, site} -> {species, site, season}
{} -> {region} -> {region, species} -> {region, species, microclimate}
```

An invalid sequence such as

```text
{species} -> {site}
```

fails because information was discarded rather than nested. Likewise

```text
RF(species, site) -> neural_net(species, site)
```

is a model comparison at the same information level, not an information refinement, and is rejected by the filtration wrapper.

## Relation to proper-score decomposition literature

The information-chain identity is not claimed as a new theorem of ODSP.

Classical proper-score work already decomposes forecast performance into concepts such as uncertainty, reliability/calibration and resolution/refinement; see, for example, Bröcker (2008/2009, arXiv:0806.0813) and the calibration-resolution treatment of Pohle (2020, arXiv:2005.01835). The term **resolution** is therefore overloaded in forecast evaluation and should not be confused with ODSP's implementation module name `predictive_resolution`.

Most directly, Charpentier & Fernandes-Machado (2026, arXiv:2603.15232) formulate proper-loss decompositions explicitly at nested information levels and derive chain identities for `A ⊂ B`. Their framework separates proper regret/reliability, information loss and residual uncertainty, with explicit log-loss and Brier forms.

ODSP uses that existing theoretical landscape as the justification for requiring an information filtration. Its methodological contribution is elsewhere:

1. evaluate **realized held-out score increments** rather than infer information gain from fitted-data association alone;
2. preserve explicitly declared independent biological groups so event-rich groups cannot rescue failures elsewhere;
3. fail closed when an intermediate comparator lacks support on a positive-weight held-out state;
4. distinguish total gain from each adjacent information increment;
5. define a transfer ceiling that cannot jump over a failed finer-information step;
6. certify that ceiling jointly over the full `group × information-step` family with aligned block bootstrap and one max-t familywise critical value.

The chain identity supplies the theoretical reference point; the independent-transfer and certification rules are the ODSP operational method.

## Log-score interpretation

For nested information sets `C_k = (C_{k-1}, Z_k)`, let `p_k` be the true conditional law and `q_k` the supplied predictor. For the logarithmic score, the expected adjacent gain can be written

```text
G_k = I(A ; Z_k | C_{k-1}) - D_k + D_{k-1},
```

where

```text
D_k = E KL{ p_k(.|C_k) || q_k(.|C_k) }.
```

Thus the oracle limit (`q_k = p_k`) reduces to conditional mutual information, while a fitted held-out increment also contains the change in predictive approximation error. A negative fitted increment is therefore a predictive-transfer failure relative to the lower-information comparator, not "negative ecological information."

For other proper scores, the score ladder and filtration remain valid, but the Shannon conditional-mutual-information reading is not used.

## Two APIs with different claim strength

### Predictive score ladder

```python
from odsp.predictive_resolution import decompose_predictive_resolution
```

Use this when the scientific question is simply whether a declared sequence of predictors improves held-out score. The predictors need not correspond to nested information sets. The output is a predictive comparison only.

### Information-transfer filtration

```python
from odsp.information_transfer import (
    InformationLevelScore,
    decompose_information_transfer,
)

levels = (
    InformationLevelScore("pooled", (), pooled_score),
    InformationLevelScore("species", ("species",), species_score),
    InformationLevelScore(
        "species+site",
        ("species", "site"),
        species_site_score,
    ),
)

result = decompose_information_transfer(levels, individual_id)
```

Use this when adjacent steps will be interpreted as added information. The strict nesting contract is then mandatory.

Familywise certification uses the same filtration:

```python
from odsp.information_transfer import certify_information_transfer

certified = certify_information_transfer(
    levels,
    individual_id,
    blocks=day_id,
    bootstrap_draws=4000,
)
```

## Claim discipline

A validated filtration does not prove that the fitted model has captured all biological information available at a level. It only makes the **declared information comparison coherent**. The held-out score determines whether the fitted representation transferred; the oracle information quantity remains a theoretical reference.

Similarly, a block-certified ceiling is conditional on the supplied predictive fits. Upstream learner-refit uncertainty remains a separate layer unless explicitly propagated.
