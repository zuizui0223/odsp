"""Frozen pre-outcome rules for ODSP Chapter-2 Gate D.

This module deliberately contains only design/preflight machinery.  It must not
compute or inspect the Tawaki niche-thickness outcome before the contract is
merged.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import math
from typing import Iterable, Mapping, Sequence

DEPTH_BIN_EDGES_M: tuple[float, ...] = (
    0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, math.inf
)
TEMPORAL_BIN_EDGES_H: tuple[float, ...] = tuple(float(x) for x in range(0, 25, 2))
PRIMARY_GRID_M = 5000
SENSITIVITY_GRIDS_M = (2500, 10000)
SEALED_FRACTION = 0.25
SPLIT_NAMESPACE = "odsp-gate-d-tawaki-v1"

LINKED_REQUIRED_COLUMNS = frozenset(
    {
        "birdID",
        "Year",
        "TripNumber",
        "EvtMaxDepth",
        "Lat",
        "Lon",
    }
)
DIVE_REQUIRED_COLUMNS = frozenset(
    {"birdID", "TripNumber", "Year", "Depth", "Duration"}
)


@dataclass(frozen=True)
class CellEligibility:
    n_events: int
    n_bird_trips: int
    n_birds: int

    @property
    def estimable(self) -> bool:
        return (
            self.n_events >= 30
            and self.n_bird_trips >= 3
            and self.n_birds >= 2
        )


def validate_columns(columns: Iterable[str], *, table: str) -> None:
    """Fail closed when a Gate-D source table lacks frozen required fields."""

    found = set(columns)
    if table == "linked":
        required = LINKED_REQUIRED_COLUMNS
    elif table == "dives":
        required = DIVE_REQUIRED_COLUMNS
    else:
        raise ValueError("table must be 'linked' or 'dives'")

    missing = sorted(required - found)
    if missing:
        raise ValueError(f"{table} table missing required columns: {missing}")

    if table == "linked":
        if not ({"Colony", "Site"} & found):
            raise ValueError("linked table requires Colony or Site")
        if not ({"DateTimeUTC", "NZOnset", "TimeNZ", "Hour"} & found):
            raise ValueError("linked table requires a biological event-time field")
    else:
        if not ({"Site", "Colony"} & found):
            raise ValueError("dives table requires Site or Colony")
        if not ({"TimeNZ", "Hour", "Time"} & found):
            raise ValueError("dives table requires a biological event-time field")


def depth_bin_index(depth_m: float) -> int | None:
    """Return the frozen powers-of-two depth bin; shallow dives are excluded."""

    depth = float(depth_m)
    if not math.isfinite(depth) or depth < DEPTH_BIN_EDGES_M[0]:
        return None
    for index, (low, high) in enumerate(zip(DEPTH_BIN_EDGES_M[:-1], DEPTH_BIN_EDGES_M[1:])):
        if low <= depth < high:
            return index
    raise AssertionError("finite depth should match a terminal infinity bin")


def temporal_bin_index(local_hour: float) -> int:
    """Return the frozen two-hour local-time bin [0, 24)."""

    hour = float(local_hour)
    if not math.isfinite(hour) or not 0.0 <= hour < 24.0:
        raise ValueError("local_hour must be finite in [0, 24)")
    return min(int(hour // 2.0), 11)


def _site(record: Mapping[str, object]) -> str:
    value = record.get("Site", record.get("Colony"))
    if value is None or str(value).strip() == "":
        raise ValueError("record requires Site or Colony")
    return str(value).strip()


def deterministic_bird_split(
    records: Iterable[Mapping[str, object]],
) -> dict[tuple[str, str, str], str]:
    """Assign whole birds to model/sealed sets within site-year strata.

    Returns keys ``(site, year, birdID)``. Strata with fewer than four birds fail
    closed rather than leaking rows between model and sealed sets.
    """

    strata: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in records:
        bird = str(record.get("birdID", "")).strip()
        year = str(record.get("Year", "")).strip()
        if not bird or not year:
            raise ValueError("record requires birdID and Year")
        strata[(_site(record), year)].add(bird)

    assignment: dict[tuple[str, str, str], str] = {}
    for (site, year), birds in sorted(strata.items()):
        if len(birds) < 4:
            raise ValueError(
                f"site-year stratum {site!r}/{year} has fewer than four birds"
            )
        ranked = sorted(
            birds,
            key=lambda bird: hashlib.sha256(
                f"{SPLIT_NAMESPACE}|{site}|{year}|{bird}".encode("utf-8")
            ).hexdigest(),
        )
        n_sealed = int(math.ceil(SEALED_FRACTION * len(ranked)))
        sealed = set(ranked[:n_sealed])
        for bird in ranked:
            assignment[(site, year, bird)] = "sealed" if bird in sealed else "model"
    return assignment


def cell_eligibility(
    *,
    n_events: int,
    bird_trip_ids: Sequence[object],
    bird_ids: Sequence[object],
) -> CellEligibility:
    """Apply frozen cell-level empirical estimability thresholds."""

    if n_events < 0:
        raise ValueError("n_events must be non-negative")
    return CellEligibility(
        n_events=int(n_events),
        n_bird_trips=len({str(value) for value in bird_trip_ids}),
        n_birds=len({str(value) for value in bird_ids}),
    )
