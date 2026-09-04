# State-resolved ecological prediction — v1

ODSP v0.10 extends the Chapter-2 evidence framework from projection-loss diagnosis to **state-resolved prediction**.

A conventional SDM or habitat model often returns one value per map cell, such as suitability or occurrence probability. The state-resolved ODSP layer instead predicts a probability distribution over one or more declared ecological states:

```text
P(A | B)
```

where `B` is a base/reference state and `A` is an added ecological state. Examples include:

```text
P(layer | spatial cell)
P(time bin | site, species)
P(depth | ocean cell, season)
P(behaviour | habitat state)
P(layer, time | spatial cell)
```

The output is therefore not only “how suitable is this place?” but also “which layer/time/state is expected here, how concentrated is that prediction, and does that state structure transfer to independent data?”

## 1. Native reference learner

For a non-negative support tensor, fit a conditional state model:

```python
from odsp import fit_state_resolved_model

model = fit_state_resolved_model(
    support,
    base_axes=(0, 1),       # e.g. x, y
    added_axes=(2, 3),      # e.g. layer, time
    alpha=0.5,
)
```

For one base state:

```python
summary = model.summarize((x_index, y_index))
```

The summary includes:

- the full `P(A|B)` probability vector;
- the dominant added-state combination;
- dominant-state probability;
- predicted-state entropy;
- effective number of predicted states;
- training support mass;
- whether the base state was observed or predicted through a declared backoff.

The native learner is deliberately a transparent reference model, not a claim that a Dirichlet histogram is the universally best ecological learner.

## 2. Event-table workflow for public data

For already discretized public records, no tensor construction is required:

```python
from odsp import fit_state_resolved_events

model = fit_state_resolved_events(
    base_states=[
        ("cell-1", "species-a"),
        ("cell-1", "species-a"),
        ("cell-2", "species-a"),
    ],
    added_states=[
        ("50-100m", "20-24"),
        ("50-100m", "20-24"),
        ("0-50m", "16-20"),
    ],
    alpha=0.5,
)

prediction = model.summarize(("cell-1", "species-a"))
```

This is appropriate for sources such as tracking archives, camera traps, acoustic monitoring, phenology observations or other public event data after source-specific state semantics and discretization have been declared.

## 3. Held-out prediction metrics

Independent support is evaluated with multiple metrics rather than a single information-loss value:

```python
score = model.model.score(heldout_support)
```

Primary metrics:

- **mean log score** of `P(A|B)`;
- **Δ log score** relative to the lower-information marginal `P(A)`.

Secondary metrics:

- multiclass Brier score;
- Brier improvement over `P(A)`;
- top-1 state accuracy;
- top-1 improvement over the marginal prediction;
- mean probability assigned to the realized state;
- fraction of held-out mass occurring in base states seen during training.

Positive Δ log score means that retaining the state-resolved organization improves independent probabilistic prediction over discarding the base-conditioned structure.

## 4. Independent groups remain separate

```python
from odsp import score_state_prediction_groups

grouped = score_state_prediction_groups(
    model,
    {
        "individual-1": heldout_1,
        "individual-2": heldout_2,
        "individual-3": heldout_3,
    },
)
```

The existing ODSP rule is retained:

- all gains positive → `generalizing`;
- all gains non-positive → `non_generalizing`;
- conflicting signs → `mixed`.

A large group cannot rescue an independent group with a conflicting result.

## 5. RF, boosting, Bayesian and other learners

ODSP is not restricted to the native reference learner. Any upstream algorithm that returns a normalized state-probability field can be evaluated through the same interface:

```python
from odsp import score_state_probability_field

score = score_state_probability_field(
    conditional_probability=rf_state_probabilities,
    heldout_support=heldout_state_counts,
    base_ndim=2,
    marginal_probability=training_state_marginal,
)
```

This enables direct comparison of learners using the same ecological prediction target and scoring rules.

Conceptually:

```text
public observations / covariates
        |
        +--> native ODSP reference learner
        |
        +--> RF / boosting / GAM / Bayesian / neural model
                          |
                          v
                     P(A | B)
                          |
                          v
              ODSP predictive audit
      log score / delta / Brier / top-1
                          |
                          v
       state-resolved ecological prediction
```

## 6. Current boundary

The v1 native predictor operates over finite discrete state spaces. It can predict unobserved combinations of **known discrete base-state levels** using explicit backoff, but it does not yet learn a smooth function from continuous environmental covariates to previously unsampled geographic locations.

That next layer will require an upstream covariate learner or a future ODSP learner interface such as:

```text
X(environment, space, season) -> P(layer, time, behaviour | X)
```

The current release establishes the common state representation, native reference model, scoring system and independent validation architecture needed to compare such learners without changing the ODSP inferential logic.
