# ODSP — Occurrence-Defined Support Patterns

ODSP reconstructs how occurrence-conditioned environmental support extends, narrows, breaks, and reappears in geographical space.

The central question is not which raster cell has the highest suitability and not which finite set of sites should be visited. It is:

> Can a supported location be reached from a known occurrence through a continuously supported environmental path, only through a weak bottleneck, or only as a detached high-support component?

## Scientific scope

ODSP accepts a frozen geographical support field and known occurrences. It treats the support field as a weighted graph and calculates the strongest bottleneck path from occurrence anchors to every supported node.

```text
known occurrences -> occurrence anchors
support field -> geographical weighted graph
anchors x graph -> maximum-bottleneck continuity
continuity -> extensions, weak necks, detached analogues
held-out detections -> structural validation
```

Environmental continuity classes:

- `continuous_environmental_extension`
- `weak_neck_extension`
- `detached_environmental_analogue`
- `unsupported_or_low_support`

These are operational structural labels. They do not prove genetic isolation, demographic independence, absence between patches, dispersal barriers, or occupancy probability.

## Implemented workflow

The package provides:

- threshold-persistent candidate-patch construction;
- occurrence-conditioned maximum-bottleneck continuity;
- explicit weak-neck and detached-analogue classes;
- bottleneck-depth summaries;
- occurrence radius-graph utilities;
- observed-medoid clustering of field detections;
- nearest-member multi-radius recovery;
- pair-first confirmatory benchmark summaries;
- producer-agnostic benchmark inputs and provenance checks.

## Difference from species distribution models

Species distribution models generally estimate a pointwise quantity such as relative suitability, occurrence intensity, or occurrence probability, depending on the model and data. ODSP does not fit another pointwise predictor.

ODSP asks a structural question about an already frozen support field:

```text
SDM or analogue model: how high is support at location x?
ODSP: is x connected to known occurrences without crossing a low-support bottleneck?
```

Two locations with the same local support can therefore receive different ODSP labels: one may be a continuous environmental extension, while the other is a detached environmental analogue.

An SDM surface may be used as one possible input, alongside environmental-analogue scores, kernels, expert maps, or other support fields. ODSP remains a distinct downstream structural analysis. See `docs/SDM_POSITIONING.md`.

## Difference from ACSP

ACSP is a survey decision tool:

> Select a finite set of survey sites under evidence, complementarity, accessibility, and budget constraints.

ODSP is an environmental-structure tool:

> Reconstruct continuity, bottlenecks, breaks, and detached re-emergence in occurrence-conditioned support.

ODSP does not optimize Top-k site sets, route budgets, evidence weights, or geographical complementarity. ACSP may later choose among ODSP-derived patches, but the estimands are different.

## Core continuity quantity

For support value `s(v)` on graph node `v`, ODSP calculates

```text
C(v) = max over paths from occurrence anchors to v
       of the minimum support encountered along the path.
```

A high `C(v)` indicates a strongly supported extension. A large difference between local support and `C(v)` indicates that the node is locally suitable-looking but separated by a weak environmental neck or complete support break.

## Campanula microdonta development case

The corrected 2026 field GPS inventory remains a method-development illustration. Historical occurrences and a candidate-support field must be frozen before field detections are read.

The next case-study revision will compare:

1. local support alone;
2. geographic distance from known occurrences;
3. conventional SDM output when available;
4. ODSP continuity, weak-neck, and detached-component classes.

Because the method was motivated after inspection of the first field result, this case cannot by itself serve as untouched confirmation.

## Confirmatory target

The key empirical question is not whether ODSP has higher AUC than an SDM. It is whether environmental path structure distinguishes held-out populations after matching or controlling for local support and geographic distance.

Candidate endpoints include:

- held-out recovery by continuity class;
- incremental recovery of detached analogues beyond continuous extensions;
- recovery after matching on local support;
- recovery after matching on distance to known occurrences;
- stability across graph distances, support thresholds, occurrence subsampling, and support producers.

## Status

The first environmental-continuity implementation is under development. Earlier distance-only `extension / near-disconnected / remote` classes remain available for backward compatibility but are no longer the intended headline method.
