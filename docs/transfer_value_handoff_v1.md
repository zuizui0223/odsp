# N2 -> N3 transfer-value handoff v1

This payload carries the **predictive value of adding information**, not a state
map and not a survey-priority map.

It complements the existing N2 -> N3 state-artifact handoff. The two payload
families have deliberately different semantics:

- `n2-to-n3-payload-v1`: whether an axis-resolved state object is scientifically
  allowed to enter N3;
- `n2-to-n3-transfer-value-payload-v1`: how much held-out predictive value was
  associated with adding declared information levels across independent groups.

The transfer-value payload never authorizes state promotion.

## Source

The builder consumes an existing serialized `population_result` from
`odsp transfer`.

Required source estimand:

```text
equal_weight_mean_gain_across_groups
```

The source must remain a descriptive population summary rather than a new
familywise confirmatory claim.

## Value carried downstream

For total transfer and each adjacent information step, the payload carries:

- expected population mean held-out gain;
- lower and upper bounds of the population mean interval;
- mean status: positive / uncertain / nonpositive;
- `conservative_mean_value = max(0, mean_interval_lower)`;
- observed positive-group fraction and its source-labelled lower bound;
- labelled new-group prediction interval when available;
- empirical p10 / p50 / p90.

The conservative value is intentionally zero when the population interval
crosses zero, even if the point estimate is positive.

This keeps the downstream value object from manufacturing certainty from a
descriptively positive mean.

## N3 role

N3 / EOG may combine these values with downstream distributional worlds,
reachability or transition constraints.

For example, N3 can retain that an information layer has:

```text
expected gain = +0.18
conservative mean value = +0.07
new-group prediction interval = [-0.10, +0.42]
```

while separately asking whether the states affected by that information are
reachable or unresolved.

The payload itself does **not** decide where to sample.

## N4 boundary

The payload explicitly sets all of the following to false:

```text
authorizes_state_promotion
authorizes_spatial_patch_ranking
authorizes_survey_site_selection
authorizes_n4_action
```

Survey-action ownership remains with **N4 / ACSP**.

N4 may eventually use an N3 product that combines transfer value with
reachability and spatial opportunity, but N2 does not emit a patch ranking
directly.

## Example

```python
from odsp import build_population_transfer_value_handoff

payload = build_population_transfer_value_handoff(
    evidence_id="example-transfer",
    population_result=receipt["population_result"],
    group_semantics="heldout site",
    population_cluster_semantics="region",
    source_receipt="endpoint.receipt.json",
).as_dict()
```

The payload contains both a canonical fingerprint of the source
`population_result` and a fingerprint of the handoff envelope.

## Relationship to esdm

An esdm adapter should export held-out score levels into the existing
`odsp transfer` contract first.

The sequence is:

```text
esdm held-out scores
    -> odsp transfer
    -> population_result
    -> N2->N3 transfer-value payload
    -> EOG reachability/world integration
    -> ACSP survey action
```

This keeps prediction, attribution, reachability and action as separate
interfaces rather than one expanding framework.
