import hashlib

import pytest

from odsp.gate_d_preflight import (
    dive_row_qualifies,
    frozen_split_from_all_dives,
    git_blob_sha1,
    linked_row_qualifies,
    row_has_finite_xy,
    summarize_dive_strata,
    summarize_location_coverage,
)


def test_git_blob_sha_matches_git_object_rule():
    data = b"hello\n"
    expected = hashlib.sha1(b"blob 6\0hello\n").hexdigest()
    assert git_blob_sha1(data) == expected


def test_frozen_filters_only_apply_threshold_not_depth_bins():
    assert dive_row_qualifies({"Depth": "0.5", "Duration": "5"})
    assert not dive_row_qualifies({"Depth": "0.49", "Duration": "10"})
    assert not dive_row_qualifies({"Depth": "10", "Duration": "4.9"})
    assert linked_row_qualifies({"EvtMaxDepth": "0.5", "DiveTime": "5"})
    assert not linked_row_qualifies({"EvtMaxDepth": "", "DiveTime": "5"})


def test_finite_xy_is_structural_only():
    assert row_has_finite_xy({"Lat": "-44.7", "Lon": "167.9"})
    assert not row_has_finite_xy({"Lat": "", "Lon": "167.9"})
    assert not row_has_finite_xy({"Lat": "-91", "Lon": "167.9"})


def _dives():
    rows = []
    for bird in ("A", "B", "C", "D"):
        for trip in (1, 2):
            rows.append(
                {
                    "birdID": bird,
                    "TripNumber": str(trip),
                    "Site": "Harrison",
                    "Year": "2019",
                    "Depth": "4",
                    "Duration": "20",
                }
            )
    return rows


def test_stratum_summary_reports_denominators_without_depth_distribution():
    summaries = summarize_dive_strata(_dives())
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.rows == 8
    assert summary.qualifying_rows == 8
    assert summary.birds == 4
    assert summary.bird_trips == 8
    assert "depth" not in summary.as_dict()


def test_location_coverage_uses_all_dive_denominator():
    linked = [
        {
            "birdID": "A",
            "TripNumber": "1",
            "Colony": "source-label-may-differ",
            "Year": "2019",
            "EvtMaxDepth": "4",
            "DiveTime": "20",
            "Lat": "-44.7",
            "Lon": "167.9",
        },
        {
            "birdID": "B",
            "TripNumber": "1",
            "Colony": "source-label-may-differ",
            "Year": "2019",
            "EvtMaxDepth": "4",
            "DiveTime": "20",
            "Lat": "",
            "Lon": "",
        },
    ]
    coverage = summarize_location_coverage(_dives(), linked)[0]
    assert coverage.qualifying_dive_rows == 8
    assert coverage.location_resolved_rows == 1
    assert coverage.coverage_fraction == pytest.approx(1 / 8)


def test_frozen_split_uses_whole_birds_from_all_dive_source():
    split = frozen_split_from_all_dives(_dives())
    assert len(split) == 4
    assert list(split.values()).count("sealed") == 1
    assert list(split.values()).count("model") == 3
