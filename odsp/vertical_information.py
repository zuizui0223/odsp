"""Source-preserving vertical/depth information for ODSP Chapter 2.

Vertical niche geometry requires a within-location ecological axis, not merely a
terrain elevation raster.  This module therefore normalizes vertical metadata
only under an explicit caller-declared semantic mapping.  It never guesses that
locality elevation, sensor height, canopy category, organism height, and water
depth are interchangeable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


VERTICAL_AXIS_KINDS = {
    "organism_height",
    "organism_depth",
    "canopy_stratum",
    "sensor_height",
    "sensor_depth",
    "locality_elevation",
    "other_declared_vertical_axis",
}
VERTICAL_PRECISIONS = {"unknown", "categorical", "point", "interval"}
NICHE_Z_AXIS_KINDS = {
    "organism_height",
    "organism_depth",
    "canopy_stratum",
    "other_declared_vertical_axis",
}


@dataclass(frozen=True)
class VerticalFieldMap:
    """Explicit mapping from a source schema into one declared vertical meaning."""

    axis_kind: str
    value_field: str | None = None
    minimum_field: str | None = None
    maximum_field: str | None = None
    stratum_field: str | None = None
    unit_field: str | None = None
    default_unit: str | None = None
    reference_field: str | None = None
    default_reference: str | None = None
    uncertainty_field: str | None = None
    sensor_minimum_field: str | None = None
    sensor_maximum_field: str | None = None
    sensor_unit_field: str | None = None
    source_id_field: str | None = None

    def __post_init__(self) -> None:
        if self.axis_kind not in VERTICAL_AXIS_KINDS:
            raise ValueError(f"unknown vertical axis kind: {self.axis_kind}")
        data_fields = (
            self.value_field,
            self.minimum_field,
            self.maximum_field,
            self.stratum_field,
        )
        if not any(data_fields):
            raise ValueError("at least one vertical data field must be declared")


@dataclass(frozen=True)
class VerticalObservation:
    source: str
    source_occurrence_id: str | None
    axis_kind: str
    value: float | None
    minimum: float | None
    maximum: float | None
    stratum_label: str | None
    unit: str | None
    reference: str | None
    uncertainty: float | None
    sensor_minimum: float | None
    sensor_maximum: float | None
    sensor_unit: str | None
    vertical_precision: str
    usable_as_niche_z: bool
    raw_vertical_fields: dict[str, Any]
    vertical_quality_flags: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.axis_kind not in VERTICAL_AXIS_KINDS:
            raise ValueError(f"unknown vertical axis kind: {self.axis_kind}")
        if self.vertical_precision not in VERTICAL_PRECISIONS:
            raise ValueError(f"unknown vertical precision: {self.vertical_precision}")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result or result in (float("inf"), float("-inf")):
        return None
    return result


def _field(record: Mapping[str, Any], name: str | None) -> Any:
    return None if name is None else record.get(name)


def _raw_fields(record: Mapping[str, Any], mapping: VerticalFieldMap) -> dict[str, Any]:
    names = (
        mapping.value_field,
        mapping.minimum_field,
        mapping.maximum_field,
        mapping.stratum_field,
        mapping.unit_field,
        mapping.reference_field,
        mapping.uncertainty_field,
        mapping.sensor_minimum_field,
        mapping.sensor_maximum_field,
        mapping.sensor_unit_field,
    )
    return {
        name: record[name]
        for name in names
        if name is not None and name in record and record[name] not in (None, "")
    }


def normalize_vertical_information(
    source: str,
    record: Mapping[str, Any],
    mapping: VerticalFieldMap,
) -> VerticalObservation:
    """Normalize one explicitly declared vertical information axis.

    No field is interpreted by name alone.  The caller must declare the semantic
    ``axis_kind`` and source fields through ``VerticalFieldMap``.
    """

    source_name = _text(source)
    if source_name is None:
        raise ValueError("source must be non-empty")

    flags: set[str] = set()
    raw = _raw_fields(record, mapping)
    value = _number(_field(record, mapping.value_field))
    minimum = _number(_field(record, mapping.minimum_field))
    maximum = _number(_field(record, mapping.maximum_field))
    stratum = _text(_field(record, mapping.stratum_field))
    uncertainty = _number(_field(record, mapping.uncertainty_field))
    sensor_minimum = _number(_field(record, mapping.sensor_minimum_field))
    sensor_maximum = _number(_field(record, mapping.sensor_maximum_field))

    unit = _text(_field(record, mapping.unit_field)) or _text(mapping.default_unit)
    reference = _text(_field(record, mapping.reference_field)) or _text(
        mapping.default_reference
    )
    sensor_unit = _text(_field(record, mapping.sensor_unit_field)) or unit

    if minimum is not None and maximum is not None and minimum > maximum:
        flags.add("vertical_interval_reversed")
        minimum = maximum = None
    if sensor_minimum is not None and sensor_maximum is not None and sensor_minimum > sensor_maximum:
        flags.add("sensor_vertical_interval_reversed")
        sensor_minimum = sensor_maximum = None
    if uncertainty is not None and uncertainty < 0:
        flags.add("invalid_negative_vertical_uncertainty")
        uncertainty = None

    numeric_present = value is not None or minimum is not None or maximum is not None
    if minimum is not None or maximum is not None:
        precision = "interval"
        if minimum is None or maximum is None:
            flags.add("open_vertical_interval")
    elif value is not None:
        precision = "point"
    elif stratum is not None:
        precision = "categorical"
    else:
        precision = "unknown"
        flags.add("missing_or_unparsed_vertical_information")

    if numeric_present and unit is None:
        flags.add("vertical_unit_missing")
    if mapping.axis_kind in {
        "organism_height",
        "organism_depth",
        "other_declared_vertical_axis",
    } and numeric_present and reference is None:
        flags.add("vertical_reference_missing")

    if mapping.axis_kind == "locality_elevation":
        flags.add("locality_elevation_is_not_within_cell_niche_z")
    if mapping.axis_kind in {"sensor_height", "sensor_depth"}:
        flags.add("sensor_position_is_observation_geometry_not_organism_z")

    biological_axis = mapping.axis_kind in NICHE_Z_AXIS_KINDS
    usable = bool(
        biological_axis
        and precision != "unknown"
        and "vertical_interval_reversed" not in flags
        and (
            precision == "categorical"
            or unit is not None
        )
    )

    if biological_axis and (sensor_minimum is not None or sensor_maximum is not None):
        flags.add("sensor_vertical_coverage_available")
    elif biological_axis:
        flags.add("sensor_vertical_coverage_not_supplied")

    return VerticalObservation(
        source=source_name,
        source_occurrence_id=_text(_field(record, mapping.source_id_field)),
        axis_kind=mapping.axis_kind,
        value=value,
        minimum=minimum,
        maximum=maximum,
        stratum_label=stratum,
        unit=unit,
        reference=reference,
        uncertainty=uncertainty,
        sensor_minimum=sensor_minimum,
        sensor_maximum=sensor_maximum,
        sensor_unit=sensor_unit,
        vertical_precision=precision,
        usable_as_niche_z=usable,
        raw_vertical_fields=raw,
        vertical_quality_flags=tuple(sorted(flags)),
    )


def gbif_locality_elevation_mapping() -> VerticalFieldMap:
    """Return a preservation-only GBIF locality-elevation mapping.

    Darwin Core locality elevation is contextual geography, not organism height
    within a canopy or other local vertical niche axis.  The normalized result is
    therefore explicitly marked unusable as niche-z.
    """

    return VerticalFieldMap(
        axis_kind="locality_elevation",
        minimum_field="minimumElevationInMeters",
        maximum_field="maximumElevationInMeters",
        unit_field=None,
        default_unit="m",
        reference_field=None,
        default_reference="sea_level",
        source_id_field="gbifID",
    )
