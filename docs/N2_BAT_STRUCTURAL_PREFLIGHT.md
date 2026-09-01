# N2 bat lane — structural preflight boundary

Selected lane: European free-tailed bat (*Tadarida teniotis*)  
Movebank study ID: `312057662`  
Movebank Data Repository DOI: `10.5441/001/1.52nn82r9`

The architecture-only selection was frozen at ODSP merge `1ac712138b380a6451d1f0d05d32553ed7b9a20a` before any ODSP altitude distribution or thickness output was read.

## Purpose

This stage asks only whether the selected public measurement architecture can support a later N2 empirical test under frozen spatial and cluster rules. It does **not** ask whether the bat vertical niche is thick.

The preflight may inspect source/access/schema, event timestamps, individual identifiers, x-y finiteness, native GPS-height **presence/missingness**, outlier flags, timestamp interval structure, whole-individual split, and x-y-only cell support.

It may not output or summarize a numerical GPS-height value.

## Frozen structural design

- primary horizontal CRS: `EPSG:3035`;
- primary cell size: 5 km;
- whole-individual sealed fraction: 0.25;
- model cell: at least 30 joint x-y/native-height-present events from at least 3 model individuals;
- full lane: at least 5 estimable model cells;
- at least 8 public individuals with joint x-y/native-height presence;
- native height field is resolved from field names only, in frozen priority order: `height_above_mean_sea_level`, `height_above_ellipsoid`, `height_raw`;
- no interpolation across GPS gaps;
- retain source outlier/visible status in the denominator at this stage.

Timestamp interval summaries are structural effort checks only. The documented nominal schedule is approximately 30 s; the preflight may report counts inside 20–40 s, gaps >40 s, and duplicate/non-positive intervals. It does not use altitude values to define events or exclusions.

## Terminal rule

If source/schema/x-y/cluster/cell structure fails, record `bat_empirical_lane_structurally_unavailable` and stop. Do not change dataset, 5 km grain, split, event threshold or cell gate inside this lane.

If the structural preflight passes, the next step is a **separate prospective scientific contract**. Only that later contract may define whether the biological z-axis is native GPS altitude or a prospectively specified height-above-ground transform, the z discretization/support estimator, weighting, uncertainty, and held-out answer-check.

This separation prevents topography, a convenient z binning, or a visually interesting flight-height distribution from influencing dataset admission or structural feasibility.
