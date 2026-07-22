# ODSP as environmental-support structure analysis

## Central question

ODSP asks:

> How is occurrence-conditioned environmental support connected in geographical space, where are its bottlenecks, and where does high support reappear as a detached component?

This is different from asking which cells have high suitability or which finite set of sites should be visited.

## Mathematical target

Let `s(v)` be a support value attached to geographical graph node `v`. For a node `v`, ODSP defines occurrence continuity as

```text
C(v) = max over paths from known-occurrence anchors to v
       of the minimum support encountered along the path.
```

`C(v)` is a maximum-bottleneck or widest-path quantity. It measures whether a candidate location can be reached from a known occurrence without crossing a low-support environmental neck.

The quantity is not interpreted as occurrence probability, occupancy, abundance, or dispersal probability.

## Structural classes

- `continuous_environmental_extension`: high-support connection to an occurrence anchor;
- `weak_neck_extension`: connected only through a lower-support bottleneck;
- `detached_environmental_analogue`: high local support but no supported connection to an occurrence anchor;
- `unsupported_or_low_support`: neither a supported extension nor a detached high-support component.

These labels describe the topology of the supplied support field under frozen graph settings. They do not prove genetic isolation, demographic independence, absence in the gap, or a causal barrier.

## Difference from species distribution models

| Dimension | SDM | ODSP |
|---|---|---|
| Primary target | Relative suitability, occurrence intensity, or occurrence probability depending on model | Connectivity structure of an occurrence-conditioned support field |
| Unit of inference | Cell or location | Path, bottleneck, and connected component |
| Main output | Suitability or occurrence surface | Continuity values, weak necks, detached components, re-emergent support patches |
| Role of a high local score | Directly ranks or predicts the location | Insufficient by itself; spatial connection to known occurrences is evaluated separately |
| Main validation | Discrimination, calibration, held-out occurrence prediction | Recovery attributable to structural classes; bottleneck and component stability; comparison against pointwise support and geographic distance |

ODSP can accept an SDM surface as one possible support input. In that case, ODSP is not another SDM layer: it performs a different downstream structural analysis of the surface. It can likewise accept environmental analogue scores, kernels, expert-derived support, or other frozen support fields.

## Difference from ACSP

ACSP is a decision tool:

> Select a finite set of survey sites under evidence, complementarity, accessibility, and budget constraints.

ODSP is a structural inference tool:

> Reconstruct how environmental support extends, narrows, breaks, and reappears around known occurrences.

ACSP may later select among ODSP-derived patches, but ODSP does not optimize Top-k site sets, route budgets, or evidence weights.

## Confirmatory comparisons

The minimum empirical comparison should include:

1. pointwise support alone;
2. geographic distance or occurrence buffers;
3. a conventional SDM surface when available;
4. ODSP continuity and detached-component classes.

The key test is not whether ODSP has a higher AUC. It is whether continuity structure distinguishes held-out populations that have similar local support or similar distance to known occurrences but differ in supported path structure.

Primary candidate endpoints include:

- held-out cluster recovery by continuity class;
- incremental recovery of detached analogues beyond continuous extensions;
- recovery after matching on local support value;
- recovery after matching on geographic distance;
- stability of bottleneck values and component labels across support thresholds, graph distances, occurrence subsampling, and support producers.
