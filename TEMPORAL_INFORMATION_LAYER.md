# ODSP temporal occurrence information layer

Tracks issue #8.

## Scope

This layer preserves **when an occurrence was observed** as a source-aware information field. It does not change SDMR Product A, does not introduce a new niche-selection objective, and does not reactivate ODSP's retired spatial-patch method.

The intended state of an occurrence is now allowed to contain

```text
(x, y) + observed time metadata
```

rather than only planar coordinates. Time is auxiliary evidence that downstream analyses may condition on; it is not automatically interpreted as a temporal niche, phenology, coexistence mechanism, or causal partition.

## Source mappings

### GBIF

Preserve the following Darwin Core event fields when present:

- `eventDate`
- `eventTime`
- `year`
- `month`
- `day`
- `startDayOfYear`
- `endDayOfYear`
- `verbatimEventDate`

`eventDate` / `eventTime` are observation-event fields. Publication, ingestion, or modification timestamps are not substitutes.

### iNaturalist

Preserve when present:

- `observed_on`
- `observed_on_string`
- `time_observed_at`
- `time_observed_at_utc`
- `time_zone`
- `zic_time_zone`

`created_at`, `updated_at`, `created_at_utc`, and `updated_at_utc` describe record management, not organism observation. They must never be silently substituted for observation time.

## Canonical fields

Each normalized record should expose:

- `source`
- `source_occurrence_id`
- `observed_date`
- `observed_datetime`
- `observed_datetime_utc`
- `timezone_name`
- `utc_offset_minutes`
- `temporal_precision`
- `year`, `month`, `day`, `day_of_year`
- `hour`, `minute`, `second`
- source-specific raw time fields
- `temporal_quality_flags`

Precision is explicit and monotonic. A year-only record remains year-only; a date-only record does not receive an invented clock time. An interval remains an interval unless a downstream analysis explicitly declares how intervals are handled.

## Fail-closed rules

1. Never infer observation time from upload / creation / modification time.
2. Never infer a timezone from coordinates in this ingestion layer.
3. Never convert date-only records to midnight and then treat midnight as ecological time.
4. Preserve source-provided UTC and local timestamps separately if both exist.
5. Flag incompatible duplicate date fields rather than choosing the favorable one silently.
6. Preserve unknown or partial time rather than dropping the occurrence by default.
7. Any future hour-of-day, seasonality, or phenology inference must model source/sampling effort separately.

## Intended downstream use

Examples that may be built later without changing this ingestion contract:

- season-aware support summaries;
- day-of-year occupancy/use layers;
- diel activity layers where true clock time and timezone are available;
- comparison of static `(x,y)` support with `(x,y,t)` support;
- source-stratified sensitivity analyses for GBIF versus iNaturalist temporal completeness.

The raw time layer itself makes no biological claim. It only prevents time already present in occurrence records from being discarded at ingestion.
