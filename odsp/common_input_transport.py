"""Prospectively declared BOP-to-Dryad *reduced-input* state model adapter.

NOT a repair or external validation of the historically frozen BOP random
forest: temperature is absent from the documented Dryad predictors and
coordinates were rounded. This adapter creates a separate, transparent,
training-only species x coarse-solar-clock state reference learner.

It consumes source-specific *projected rows* with strict schemas; for real
ecology, identity nonoverlap, source admission and calibration/test group
exchangeability remain external obligations. Current qualification uses
known-truth synthetic rows ONLY, never actual BOP/Dryad GPS outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import Mapping, Sequence

from .fixed_group_gain_protocol import FrozenGainCalibration, FrozenGainValidation
from .managed_group_forecast_v1 import (
    ManagedGroupForecast,
    calibrate_managed_group_gain,
    freeze_managed_group_forecasts,
    validate_managed_group_gain,
)

CLASSES = ("low_lt50", "lower_mid_50_200", "upper_mid_200_500", "high_ge500")
BOP_FIELDS = frozenset((
    "row_id", "individual-local-identifier", "individual-taxon-canonical-name",
    "timestamp", "location-long", "height-above-msl"
))
DRYAD_FIELDS = frozenset((
    "row_id", "individual.global.identifier", "individual.taxon.canonical.name",
    "timestamp", "location.long.rnd",
))
SOURCE_STRATA = frozenset((
    "Buteo buteo", "Circus aeruginosus",
    "Circus cyaneus", "Circus pygargus"
))
CLOCK_BOUNDARY_MARGIN_HOURS = 0.05 / 15.0


def _strict_float(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite numeric")
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name} must be finite numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite numeric")
    return result


def _identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be a non-empty stripped identifier")
    return value


def _utc_datetime(value: object) -> datetime:
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("timestamp must be explicit ISO8601 UTC with T separator")
    if not (value.endswith("Z") or value.endswith("+00:00")):
        raise ValueError("timestamp must declare UTC as Z or +00:00")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ValueError("timestamp is not valid ISO8601 UTC") from exc
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("timestamp must have zero UTC offset")
    return parsed.astimezone(timezone.utc)


def _solar_clock_context(timestamp: object, longitude: object, *, rounded: bool) -> int:
    dt = _utc_datetime(timestamp)
    lon = _strict_float(longitude, "longitude")
    if not -180.0 <= lon <= 180.0:
        raise ValueError("longitude outside [-180, 180]")
    if rounded and not math.isclose(lon * 10, round(lon * 10), abs_tol=1e-7, rel_tol=0):
        raise ValueError("Dryad longitude must be explicitly rounded to 0.1 degrees")
    utc_hour = dt.hour + dt.minute / 60 + dt.second / 3600 + dt.microsecond / 3.6e9
    local = (utc_hour + lon / 15.0) % 24.0
    distance = min(
        min(abs(local - boundary), 24.0 - abs(local - boundary))
        for boundary in (6.0, 18.0)
    )
    # A 0.1 degree rounded longitude has unknown error <=0.05 degrees,
    # equivalent to 12 seconds in local *mean solar clock* time.
    # Reject the same boundary region in both sources, pre-outcome.
    if distance <= CLOCK_BOUNDARY_MARGIN_HOURS + 1e-12:
        raise ValueError("mean-solar-clock phase ambiguous under 0.1 degree rounding")
    return int(6.0 < local < 18.0)


def altitude_state(altitude_amsl: object) -> str:
    """Frozen AMSL bins; not height above ground or corrected in-flight MSL."""
    alt = _strict_float(altitude_amsl, "height-above-msl")
    if not -100.0 <= alt <= 5000.0:
        raise ValueError("training AMSL altitude outside frozen admissible range")
    if alt < 50:
        return CLASSES[0]
    if alt < 200:
        return CLASSES[1]
    if alt < 500:
        return CLASSES[2]
    return CLASSES[3]


def _project(
    rows: Sequence[Mapping[str, object]], *, source: str, role: str,
) -> list[dict[str, object]]:
    if source not in ("BOP", "DRYAD"):
        raise ValueError("source not in frozen common feature crosswalk")
    if (source, role) not in (("BOP", "training"), ("DRYAD", "calibration"),
                             ("DRYAD", "validation")):
        raise ValueError("wrong source-to-role assignment")
    required = BOP_FIELDS if source == "BOP" else DRYAD_FIELDS
    if isinstance(rows, (str, bytes)) or not rows:
        raise ValueError("every predeclared source role needs non-empty rows")
    projected = []
    seen_rows: set[str] = set()
    assignment: dict[str, str] = {}
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise ValueError("source row must be a mapping")
        if set(raw) - (required | {"weight"}) or required.difference(raw):
            raise ValueError("source fields do not match frozen role schema; outcomes/leakage forbidden")
        native_id = _identity(raw["row_id"], "row_id")
        if native_id in seen_rows:
            raise ValueError("duplicate source row_id")
        seen_rows.add(native_id)
        group_key = (
            "individual-local-identifier" if source == "BOP"
            else "individual.global.identifier"
        )
        species_key = (
            "individual-taxon-canonical-name" if source == "BOP"
            else "individual.taxon.canonical.name"
        )
        group = _identity(raw[group_key], "individual_id")
        species = _identity(raw[species_key], "species")
        if species not in SOURCE_STRATA:
            raise ValueError("species is outside prespecified four BOP strata")
        if group in assignment and assignment[group] != species:
            raise ValueError("one individual ID crosses biological species")
        assignment[group] = species
        longitude = (
            raw["location-long"] if source == "BOP" else raw["location.long.rnd"]
        )
        context = _solar_clock_context(
            raw["timestamp"], longitude, rounded=(source == "DRYAD")
        )
        weight = _strict_float(raw.get("weight", 1.0), "weight")
        if weight <= 0:
            raise ValueError("row weight must be positive")
        row = {
            "row_id": f"{source}:{native_id}",
            "group_id": f"{source}:{group}",
            "stratum": species, "context": context, "weight": weight,
        }
        if source == "BOP":
            row["outcome"] = altitude_state(raw["height-above-msl"])
        projected.append(row)
    return projected


@dataclass(frozen=True)
class CommonInputTransport:
    """Adapter plus managed forecast; source IDs are only namespaced, not proven disjoint."""

    forecast: ManagedGroupForecast
    protocol: str = "synthetic_known_truth_only"
    training_source: str = "BOP"
    target_source: str = "DRYAD"

    def assert_replayed(self) -> None:
        self.forecast.assert_replayed()

    def public_manifest(self) -> dict[str, object]:
        out = self.forecast.public_manifest()
        return {
            **out,
            "protocol": self.protocol,
            "reduced_feature": "binary_mean_solar_clock_06_18",
            "original_RF_direct_transfer_admissible": False,
            "original_BOP_terminal": "empirical_state_prediction_mixed",
            "Dryad_external_candidate_admitted": False,
            "real_cross_source_individual_nonoverlap_verified": False,
            "real_target_group_exchangeability_verified": False,
            "historical_BOP_v2026_same_study_gate_reopened": False,
        }


def freeze_common_input_transport(
    *,
    training_BOP_rows: Sequence[Mapping[str, object]],
    calibration_Dryad_features: Sequence[Mapping[str, object]],
    validation_Dryad_features: Sequence[Mapping[str, object]],
    pseudocount: float = 0.1,
    miscoverage: float = 0.1,
) -> CommonInputTransport:
    """One new learner, not the historic RF: freeze before external labels open."""
    train = _project(training_BOP_rows, source="BOP", role="training")
    cal = _project(calibration_Dryad_features, source="DRYAD", role="calibration")
    test = _project(validation_Dryad_features, source="DRYAD", role="validation")
    # Cross-source group ID namespacing is necessary for software isolation,
    # but does NOT prove two distinct real tagged animals in different studies.
    frozen = freeze_managed_group_forecasts(
        training_rows=train,
        calibration_features=cal,
        validation_features=test,
        classes=CLASSES,
        pseudocount=pseudocount,
        miscoverage=miscoverage,
    )
    return CommonInputTransport(forecast=frozen)


def _label_rows(
    outcomes: Mapping[str, str], rows: tuple[object, ...],
) -> dict[str, str]:
    if not isinstance(outcomes, Mapping):
        raise ValueError("outcomes must map raw Dryad row_id to a frozen state")
    expected = {row.row_id.partition(":")[2] for row in rows}
    if set(outcomes) != expected:
        raise ValueError("only exact frozen Dryad role outcome IDs accepted")
    if any(v not in CLASSES for v in outcomes.values()):
        raise ValueError("outcomes must be declared four AMSL state labels")
    return {"DRYAD:" + k: v for k, v in outcomes.items()}


def calibrate_common_input_transport(
    fitted: CommonInputTransport, calibration_state_by_native_row: Mapping[str, str],
) -> FrozenGainCalibration:
    fitted.assert_replayed()
    return calibrate_managed_group_gain(
        fitted.forecast,
        _label_rows(
            calibration_state_by_native_row, fitted.forecast.plan.calibration_rows
        ),
    )


def validate_common_input_transport(
    fitted: CommonInputTransport,
    calibration: FrozenGainCalibration,
    validation_state_by_native_row: Mapping[str, str],
) -> FrozenGainValidation:
    fitted.assert_replayed()
    return validate_managed_group_gain(
        fitted.forecast, calibration,
        _label_rows(
            validation_state_by_native_row, fitted.forecast.plan.validation_rows
        ),
    )
