# ODSP — occurrence information layers

ODSP's **historical spatial-patch method remains superseded**. Its defensible support-topology work was migrated to [`zuizui0223/eog`](https://github.com/zuizui0223/eog) at EOG merge `023261f4cac6d70973d097634807472976df749b` (PR #61). Those spatial algorithms should not be reimplemented here.

ODSP now has one narrow active scope: **source-preserving information attached to biodiversity occurrences before any downstream niche, support, or connectivity model is fitted**.

## Active layer: observation time

Tracks issue [#8](https://github.com/zuizui0223/odsp/issues/8).

`odsp.temporal_information` standardizes the observation-time metadata already present in sources such as GBIF and iNaturalist while retaining the source fields and their actual precision.

Canonical output includes:

- source and source occurrence ID;
- observed date and/or datetime;
- source-provided UTC representation when available;
- time-zone name and UTC offset when supplied;
- explicit precision: year, month, day, minute, second, interval, or unknown;
- year/month/day/day-of-year and clock fields only when the source supports them;
- source-specific raw observation-time fields;
- fail-closed quality flags.

Key rules:

- upload/creation/update timestamps are **never** substituted for observation time;
- date-only records do not become ecological midnight observations;
- a timezone is not inferred from coordinates at ingestion;
- conflicting duplicate date/UTC fields are flagged rather than silently resolved;
- missing or partial time remains missing/partial instead of being fabricated.

See [`TEMPORAL_INFORMATION_LAYER.md`](TEMPORAL_INFORMATION_LAYER.md).

## Example

```python
from odsp import normalize_occurrence_time

row = normalize_occurrence_time(
    "gbif",
    {
        "key": 123,
        "eventDate": "2026-05-17T21:34:12+09:00",
        "year": 2026,
        "month": 5,
        "day": 17,
    },
)

print(row.observed_datetime)      # 2026-05-17T21:34:12+09:00
print(row.observed_datetime_utc)  # 2026-05-17T12:34:12Z
print(row.temporal_precision)     # second
```

## Scientific boundary

This layer does **not** modify SDMR Product A and is not a new environmental-variable selector, SDM objective, or validation endpoint. Product A remains scientifically closed.

Time is stored as an information layer so later work can ask questions such as season-aware occurrence support or diel use **only under a separate design that accounts for sampling effort and detectability**. Timestamp availability alone does not establish a temporal niche, phenology, coexistence mechanism, causal partition, or fundamental niche.

## Historical ODSP material

The former ODSP package, patch methods, ACSP adapters, case study and validation artifacts remain recoverable from Git history before the 2026-07-22 tombstone. Their active spatial successor is EOG. This repository should not grow a second support-topology or reachability implementation.
