import math

import pytest

from odsp.gate_d_contract import (
    DEPTH_BIN_EDGES_M,
    PRIMARY_GRID_M,
    SENSITIVITY_GRIDS_M,
    SEALED_FRACTION,
    cell_eligibility,
    depth_bin_index,
    deterministic_bird_split,
    temporal_bin_index,
    validate_columns,
)


def test_frozen_gate_d_constants():
    assert DEPTH_BIN_EDGES_M[:-1] == (
        0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0
    )
    assert math.isinf(DEPTH_BIN_EDGES_M[-1])
    assert PRIMARY_GRID_M == 5000
    assert SENSITIVITY_GRIDS_M == (2500, 10000)
    assert SEALED_FRACTION == pytest.approx(0.25)


def test_depth_bins_are_fixed_and_not_quantile_based():
    assert depth_bin_index(0.49) is None
    assert depth_bin_index(0.5) == 0
    assert depth_bin_index(0.999) == 0
    assert depth_bin_index(1.0) == 1
    assert depth_bin_index(31.9) == 5
    assert depth_bin_index(128.0) == 8
    assert depth_bin_index(float("nan")) is None


def test_two_hour_temporal_bins_cover_local_day():
    assert temporal_bin_index(0.0) == 0
    assert temporal_bin_index(1.999) == 0
    assert temporal_bin_index(2.0) == 1
    assert temporal_bin_index(23.999) == 11
    with pytest.raises(ValueError):
        temporal_bin_index(24.0)


def test_schema_validation_accepts_source_like_headers():
    validate_columns(
        [
            "birdID",
            "Year",
            "Colony",
            "TripNumber",
            "EvtMaxDepth",
            "Lat",
            "Lon",
            "DateTimeUTC",
        ],
        table="linked",
    )
    validate_columns(
        [
            "birdID",
            "TripNumber",
            "Site",
            "Year",
            "Depth",
            "Duration",
            "TimeNZ",
        ],
        table="dives",
    )


def test_schema_validation_fails_closed():
    with pytest.raises(ValueError, match="missing required columns"):
        validate_columns(["birdID", "Year", "Colony"], table="linked")
    with pytest.raises(ValueError, match="requires a biological event-time"):
        validate_columns(
            [
                "birdID",
                "Year",
                "Colony",
                "TripNumber",
                "EvtMaxDepth",
                "Lat",
                "Lon",
            ],
            table="linked",
        )


def test_bird_split_is_clustered_stratified_and_order_invariant():
    records = []
    for site in ("Harrison Cove", "Moraine"):
        for year in (2019, 2020):
            for bird in ("A", "B", "C", "D", "E", "F", "G", "H"):
                records.append({"Site": site, "Year": year, "birdID": bird})

    forward = deterministic_bird_split(records)
    reverse = deterministic_bird_split(reversed(records))
    assert forward == reverse

    for site in ("Harrison Cove", "Moraine"):
        for year in (2019, 2020):
            labels = [
                forward[(site, str(year), bird)]
                for bird in ("A", "B", "C", "D", "E", "F", "G", "H")
            ]
            assert labels.count("sealed") == 2
            assert labels.count("model") == 6


def test_bird_split_refuses_tiny_strata():
    records = [
        {"Site": "Harrison Cove", "Year": 2019, "birdID": bird}
        for bird in ("A", "B", "C")
    ]
    with pytest.raises(ValueError, match="fewer than four birds"):
        deterministic_bird_split(records)


def test_cell_estimability_thresholds_are_frozen():
    assert cell_eligibility(
        n_events=30,
        bird_trip_ids=["A1", "A2", "B1"],
        bird_ids=["A", "A", "B"],
    ).estimable
    assert not cell_eligibility(
        n_events=29,
        bird_trip_ids=["A1", "A2", "B1"],
        bird_ids=["A", "A", "B"],
    ).estimable
    assert not cell_eligibility(
        n_events=100,
        bird_trip_ids=["A1", "B1"],
        bird_ids=["A", "B"],
    ).estimable
