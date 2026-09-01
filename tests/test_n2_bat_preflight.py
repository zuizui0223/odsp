from datetime import datetime, timedelta, timezone
import json

import pytest

from odsp.n2_bat_preflight import (
    deterministic_individual_split,
    resolve_native_height_field,
    summarize_bat_structural_preflight,
)


def test_height_field_resolution_uses_frozen_name_priority_only():
    assert (
        resolve_native_height_field(
            ["height_raw", "height_above_ellipsoid", "height_above_msl"]
        )
        == "height_above_msl"
    )
    with pytest.raises(ValueError, match="no frozen-priority"):
        resolve_native_height_field(["elevation", "bathymetry"])


def test_whole_individual_split_is_deterministic_and_not_row_level():
    ids = [f"bat-{index}" for index in range(8)]
    first = deterministic_individual_split(ids)
    second = deterministic_individual_split(reversed(ids))
    assert first == second
    assert list(first.values()).count("sealed") == 2
    assert list(first.values()).count("model") == 6


def _synthetic_events():
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    rows = []
    sequence = 0
    for bat in range(8):
        for cell in range(5):
            for replicate in range(30):
                timestamp = start + timedelta(seconds=30 * sequence)
                sequence += 1
                rows.append(
                    {
                        "individual_local_identifier": f"bat-{bat}",
                        "timestamp": timestamp.isoformat(),
                        "location_long": str(cell * 0.05 + 0.001 * bat),
                        "location_lat": "0.0",
                        # Deliberately dramatic strings: the preflight is allowed
                        # to test only presence, never parse or summarize them.
                        "height_above_msl": str(1000000 * bat + replicate),
                    }
                )
    return rows


def test_structural_preflight_can_pass_without_opening_height_distribution():
    result = summarize_bat_structural_preflight(
        _synthetic_events(),
        native_height_field="height_above_msl",
        projector=lambda lon, lat: (lon * 100000.0, lat * 100000.0),
    )
    assert result.structural_available
    assert result.individual_count == 8
    assert result.sealed_individual_count == 2
    assert result.model_individual_count == 6
    assert result.model_pool_estimable_cells >= 5
    payload = json.dumps(result.as_dict(), sort_keys=True)
    assert "1000000" not in payload
    for forbidden in ("height_min", "height_max", "height_mean", "H(Z|X,Y)"):
        assert forbidden not in payload


def test_too_few_joint_individuals_fails_closed_without_retuning():
    rows = [
        row
        for row in _synthetic_events()
        if row["individual_local_identifier"] in {"bat-0", "bat-1", "bat-2", "bat-3"}
    ]
    result = summarize_bat_structural_preflight(
        rows,
        native_height_field="height_above_msl",
        projector=lambda lon, lat: (lon * 100000.0, lat * 100000.0),
    )
    assert not result.structural_available
    assert "too_few_individuals_with_joint_xy_and_native_height_presence" in result.reasons


def test_contextual_elevation_cannot_be_substituted_for_native_height():
    with pytest.raises(ValueError, match="violates frozen priority"):
        summarize_bat_structural_preflight(
            _synthetic_events(),
            native_height_field="elevation",
            projector=lambda lon, lat: (lon, lat),
        )
