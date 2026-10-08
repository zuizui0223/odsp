"""Frozen 41 date-pair latitude sensitivity without wildlife observations."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.uljin_mirror_latitude_envelope_v0 import (
    original_pairs_latitude_sensitivity,
)

ROOT=Path(__file__).resolve().parents[1]
MAIN=json.loads(
    (ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text()
)
PLAN=json.loads(
    (ROOT/"ULJIN_MIRROR_LATITUDE_ENVELOPE_V0_CONTRACT.json").read_text()
)


def test_public_latitudes_preserve_all_original_mirror_dates_without_rematching():
    result=original_pairs_latitude_sensitivity(MAIN,PLAN)
    assert result["original_pair_count_retained_without_rematching"]==41
    assert result["all_matched_pairs_within_frozen_daylength_tolerance"]
    assert list(result["public_latitude_envelope"])==["36.60","36.85","37.10"]
    for row in result["public_latitude_envelope"].values():
        assert row["pair_count"]==41
        assert row["max_daylength_mismatch_minutes"]<.56
        assert row["number_over_original_nine_minute_ceiling"]==0
    assert result["individual_station_coordinates_inferred_or_read"] is False
    assert result["individual_camera_hourly_effort_verified"] is False
    assert result["animal_detection_rows_read"] is False
    assert result["source_operation_log_opened"] is False
    assert result["original_odsp_ecological_results_reclassified"] is False


def test_original_rule_or_sensitivity_cannot_change_to_rescue_outcome():
    plan=json.loads(json.dumps(PLAN))
    plan["fixed_public_area_latitudes"]=[36.6,36.85]
    with pytest.raises(ValueError,match="plan changed"):
        original_pairs_latitude_sensitivity(MAIN,plan)
    original=json.loads(json.dumps(MAIN))
    original["preoutcome_structural_pairing"]["ascending_window_start"]="2022-05-10"
    with pytest.raises(ValueError,match="pairing rules differ"):
        original_pairs_latitude_sensitivity(original,PLAN)
