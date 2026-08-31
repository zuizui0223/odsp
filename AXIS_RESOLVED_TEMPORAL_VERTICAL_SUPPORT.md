# Axis-resolved temporal and vertical support — successor routing note

ODSP remains a superseded tombstone. This document records a new scientific idea without reactivating ODSP as an independent package, method, or publication target.

## Idea

Two taxa may overlap strongly on the same horizontal raster cells while separating along axes that a planar map discards:

- activity time or season;
- height above ground or canopy stratum;
- water or soil depth;
- a joint height-by-time schedule.

For an axis-resolved support tensor

```text
S(x, y, z, t)
```

the ordinary map

```text
P(x, y) = sum_{z,t} S(x,y,z,t)
```

can make distinct states look identical. A hypothetical small grassland mammal and snake-like predator may use the same `x,y` cells but different z strata and/or time bins. Planar overlap therefore does not establish simultaneous co-use, encounter, competition, predation, or a shared realized niche.

## Active successor

The concept is tracked and prototyped in EOG:

- EOG issue: https://github.com/zuizui0223/eog/issues/323
- EOG draft PR: https://github.com/zuizui0223/eog/pull/324
- proposed internal module: `eog.v2.axis_resolved_support`
- design note: `docs/axis_resolved_temporal_vertical_support.md`

The first slice compares Schoener overlap in full `x × y × z × t` support and after projection to `x × y`, `x × y × z`, and `x × y × t`. It reports how much vertical, temporal, or joint partition is hidden by planar collapse.

## Scientific boundary

This extension does not reveal a literal fundamental niche from occurrence data. Exact truth is available only in known-truth simulation where the generating support tensor is hidden from selection. Empirical claims remain conditional axis-resolved realized support/use and require effort and detectability to be represented at the same time and vertical resolution.

No active implementation should be added to ODSP. Future development, validation, and any publication claim belong to EOG.
