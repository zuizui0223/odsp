# Four-chapter research program

Program ID: `niche-to-survey-four-chapter-v1`

The chapter order is fixed:

1. **SDMR — environmental niche-driver selection**: which environmental dimensions best define an interpretable realized niche, using model-pool occurrences for choice and sealed occurrences for answer-checking.
2. **ODSP — multidimensional niche geometry**: how much niche structure is hidden when support is projected onto a flat x-y map; quantify niche thickness in added axes such as vertical stratum/depth and time.
3. **EOG — distributional worlds and reachability**: given locally supported states, which transition/distribution worlds remain compatible with evidence and what states are possible, robust, unresolved or reachable.
4. **ACSP — survey action**: where field effort should be directed next; return bounded candidate survey patches/priorities rather than a niche or historical route.

## Chapter 2 scientific center

ODSP is the **niche geometry** chapter.

A conventional SDM collapses ecological use to a horizontal field `S(x,y)`. ODSP represents an axis-resolved support/use distribution such as:

```text
S(x, y, z, t, ...)
```

where `z` can be canopy stratum, height, depth or another explicit vertical state and `t` can be date, season or time-of-day when observation precision permits.

The central question is:

> **How much ecological state-space information is lost by a 2D x-y projection?**

### Primary Chapter-2 quantities

For a normalized non-negative support distribution `p`, define the Shannon entropy of retained axes and use entropy differences to measure information beyond the planar map.

- vertical information beyond the map: `H(Z | X,Y)`;
- temporal information beyond the map: `H(T | X,Y)`;
- joint added-axis information: `H(Z,T | X,Y)`;
- effective vertical states: `exp(H(Z | X,Y))`;
- effective temporal states: `exp(H(T | X,Y))`;
- effective joint added states: `exp(H(Z,T | X,Y))`.

An effective value near 1 means the added axis contributes little thickness after location is known. Larger values mean the same horizontal footprint contains multiple distinguishable ecological states.

This supports comparisons such as structurally simple grassland versus vertically layered forest without equating equal horizontal area with equal ecological state-space capacity.

### Observation boundary

Raw opportunistic record counts are not automatically biological use probabilities. GBIF/iNaturalist timestamps, vertical metadata, telemetry, camera/acoustic records and habitat structure must retain source precision, effort and detectability semantics. The existing `odsp.temporal_information` layer is the first input layer for the time axis; it does not itself establish temporal niche partition.

### Fixed Chapter-2 goal

Build and validate a model-agnostic framework for **niche thickness, added-axis information and projection loss**, first on known/synthetic state spaces and then on independent empirical data with defensible time/vertical effort semantics.

The retired ODSP spatial-patch/topology code remains superseded by EOG and must not be revived here.
