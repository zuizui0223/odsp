# Axis-resolved temporal/vertical idea — deferred

This earlier idea has been narrowed by the 2026-09-01 scope decision.

Do **not** add a new `x × y × z × t` niche/support algorithm to Product A or the active EOG-WF endpoint at this stage. EOG issue #323 and draft PR #324 were closed without merging that prototype.

The active ODSP work is instead the lower-level prerequisite: preserve source-provided observation time as an independent occurrence information layer. See:

- ODSP issue #8;
- `TEMPORAL_INFORMATION_LAYER.md`;
- `odsp.temporal_information`.

This means GBIF/iNaturalist observation dates and clock times can survive ingestion without being discarded or fabricated. Any later temporal niche, phenology, diel partition, or vertical-axis method must be designed separately and must account for observation effort/detectability before making biological claims.
