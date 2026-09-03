# N2 → N3 handoff gate

ODSP can produce several different Chapter-2 objects. They are not interchangeable inputs to EOG:

- a descriptive niche-thickness summary;
- a structural state-space-capacity summary;
- a known-truth axis-resolved state used for method validation;
- an empirically supported axis-resolved species-state map.

The executable gate is `odsp.assess_n2_to_n3_handoff(...)`. The frozen interface contract is [`N2_TO_N3_HANDOFF_CONTRACT.json`](../N2_TO_N3_HANDOFF_CONTRACT.json), the versioned envelope is defined by [`N2_TO_N3_PAYLOAD_SCHEMA.json`](../N2_TO_N3_PAYLOAD_SCHEMA.json), and current completed-lane decisions are recorded in [`N2_CURRENT_HANDOFF_DECISIONS.json`](../N2_CURRENT_HANDOFF_DECISIONS.json).

## Empirical promotion rule

An empirical axis-resolved species-state map may be passed to N3 only when all of the following are true:

1. the added-axis semantics are explicit;
2. the empirical source/denominator boundary was prospectively frozen;
3. Chapter-2 thickness is estimable under that boundary;
4. the base-resolved added-axis organization generalizes to independent held-out support.

Descriptive thickness alone is not enough. Fitted `I(A;B)>0` alone is not enough. Structural capacity is not species use.

## Decision example

```python
from odsp import assess_n2_to_n3_handoff

bat = assess_n2_to_n3_handoff(
    evidence_scope="empirical",
    support_semantics="species_support",
    axis_semantics_declared=True,
    prospective_source_boundary_frozen=True,
    thickness_estimable=True,
    transferability_category="non_generalizing",
)

assert bat.handoff_category == "descriptive_projection_only"
assert bat.projection_summary_allowed
assert not bat.axis_resolved_species_state_allowed_for_empirical_n3
```

This matches the frozen European free-tailed bat endpoint: descriptive vertical thickness remains a valid N2 result, but the x-y-conditioned vertical distribution is not promoted to an empirical N3 state map.

## Standard payload

`odsp.build_n2_to_n3_payload(...)` serializes the decision together with:

- explicit base and added-axis semantics;
- projection/thickness summaries when they are allowed;
- independent transferability gains;
- source contract / decision receipt / source fingerprint provenance;
- an optional axis-resolved state artifact;
- a canonical SHA-256 payload fingerprint.

An axis-resolved artifact is only permitted when the handoff category itself allows one. Empirical N3 state artifacts must have semantics `empirical_species_support`, an explicit axis order and shape, and a SHA-256 integrity pin. A `descriptive_projection_only` payload is forbidden from carrying such an artifact, so serialization cannot rescue the completed bat endpoint.

```python
from odsp import AxisDescriptor, build_n2_to_n3_payload

payload = build_n2_to_n3_payload(
    evidence_id="tadarida-teniotis-n2-terminal",
    decision=bat,
    base_axes=(
        AxisDescriptor("x", "projected easting", "m", "EPSG:3035"),
        AxisDescriptor("y", "projected northing", "m", "EPSG:3035"),
    ),
    added_axes=(
        AxisDescriptor("z", "native GPS height above mean sea level", "m", "MSL"),
    ),
    projection_summary={
        "H_Z_given_XY_nats": 1.3918623004770097,
        "effective_vertical_states": 4.022333876564191,
    },
    transferability_gains=(-0.43541033813280833, -0.021938657402345435),
    decision_receipt="N2_BAT_THICKNESS_TERMINAL_DECISION.json",
)

assert payload.state_artifact is None
```

`odsp.validate_n2_to_n3_payload(...)` rebuilds the serialized envelope and verifies its fingerprint. `N2ToN3HandoffDecision` is also self-validating, so a serialized permission cannot contradict the upstream evidence fields.

## Categories

- `empirical_axis_resolved_supported`: empirical species state may enter N3 under the frozen semantics.
- `known_truth_method_state_only`: synthetic/known-truth state may enter N3 only for method testing.
- `descriptive_projection_only`: retain N2 thickness/projection summaries, but not an empirical local axis-resolved species-state map.
- `structural_capacity_only`: retain structural-capacity semantics; do not relabel as species support.
- `unavailable`: no supported axis-resolved handoff object.

## Non-retroactivity

This gate and payload classify already-defined evidence. They cannot be used to retune a completed N2 endpoint, swap datasets, alter bins/grids after outcome access, rescue a failed empirical lane, or authorize the currently blocked Gate-E habitat-complexity programme.
