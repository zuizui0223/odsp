# ODSP — Superseded research repository

> **Superseded on 2026-07-22.** The scientifically defensible support-field component work from ODSP has been integrated into [`zuizui0223/eog`](https://github.com/zuizui0223/eog) as the **spatial support topology** layer at EOG merge commit `023261f4cac6d70973d097634807472976df749b` (PR #61, “Integrate spatial support topology into EOG”).

ODSP is no longer an independent method, package, data source, or publication
target. New development should occur in EOG. The current default branch is a
tombstone only: the former package, tests, workflows, case-study data, and
validation artifacts remain recoverable from Git history but are absent from the
current tree so they cannot be mistaken for a second active implementation.

## What moved to EOG

EOG now provides a tested, model-agnostic raster support-topology layer for:

- frozen pointwise support fields;
- explicit multi-threshold superlevel sets;
- four- or eight-neighbour connected components;
- hard unavailable-cell masks such as sea;
- explicit occurrence-anchor assignment;
- deterministic component lineages and fingerprints;
- occurrence-anchored, persistent detached, transient detached, and unresolved classes;
- component summaries and held-out detection recovery;
- threshold and neighbourhood sensitivity audits.

The canonical implementation is `src/eog/support_topology.py`, with positioning and migration documentation in:

- `docs/sdm_support_topology_positioning.md`;
- `docs/odsp_migration_map.md`;
- `examples/support_topology/synthetic_islands.py`.

## Future concept routed to EOG

A new axis-resolved support idea asks whether apparent overlap on the same planar
raster cells is created by marginalizing activity time or a vertical/depth axis.
Two taxa can have nearly identical `x × y` projections while using different
`z`, `t`, or joint `z × t` states. Planar co-occurrence then does not imply
simultaneous co-use, encounter, competition, predation, or a shared realized
niche.

ODSP records the concept only in
[`AXIS_RESOLVED_TEMPORAL_VERTICAL_SUPPORT.md`](AXIS_RESOLVED_TEMPORAL_VERTICAL_SUPPORT.md).
Active design and code are routed to EOG issue
[`#323`](https://github.com/zuizui0223/eog/issues/323) and draft PR
[`#324`](https://github.com/zuizui0223/eog/pull/324). This does not reactivate
ODSP as a package or publication identity.

## What was deliberately not migrated

ODSP PR #5 proposed maximum-bottleneck environmental-continuity paths. EOG already implements cumulative-cost paths, minimax bottleneck paths, redundancy, sensitivity, hypothesis-family aggregation, and hypothesis-discriminating survey ranking. A second ODSP path implementation would be scientifically and technically duplicative, so it was not retained.

The following are retired as headline concepts:

- distance-only `occurrence_patch_extension`;
- `near_disconnected_occurrence_patch`;
- `remote_candidate_patch`;
- ODSP-specific widest-path or minimax continuity classes;
- duplicated ACSP export adapters;
- a second hypothesis-ranking workflow.

Historical ODSP outputs do not establish occupancy, colonisation probability, demographic or genetic isolation, causal barriers, or historical dispersal.

## Migration boundary

The layered workflow is now:

```text
SDM, environmental-similarity model, or expert support generator
    -> frozen pointwise support field
    -> EOG spatial support topology
    -> occurrence-anchored and detached support components
    -> existing EOG bridge and reachability inference
    -> existing EOG hypothesis-discrimination survey workflow
    -> optional external finite-site optimization by ACSP
```

The retired `Campanula microdonta` development case was exploratory because
outcomes were inspected during method development. Its duplicated locations file
is not retained here; the active field-planning source remains ACSP. Any future
confirmatory analysis must freeze historical anchors, training-only support,
thresholds, neighbourhood, mask, raster resolution, and held-out detections
before evaluation.

This repository is retained only as migration history. See `SUPERSEDED.json` for
the machine-readable successor and frozen migration commit.
