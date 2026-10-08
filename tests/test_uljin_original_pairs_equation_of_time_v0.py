"""Frozen original 41-pair equation-of-time sensitivity, no wildlife records."""
from __future__ import annotations
from datetime import date
import json
from pathlib import Path
import pytest

from odsp.uljin_original_pairs_equation_of_time_v0 import (
    civil_solar_geometry,
    compare_original_41_mirror_noons,
)

ROOT=Path(__file__).resolve().parents[1]
MAIN=json.loads(
    (ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text()
)
CONTRACT=json.loads(
    (ROOT/"ULJIN_ORIGINAL_41_EQUATION_OF_TIME_AUDIT_V0_CONTRACT.json").read_text()
)


def test_original_date_pairs_same_daylength_but_shifted_clock_sunrise_noon():
    result=compare_original_41_mirror_noons(MAIN,CONTRACT)
    assert result["fixed_original_calendar_pairs"]==41
    assert result["status"]=="SOLAR_NOON_CLOCK_OFFSET_DESIGN_CONTROL_ONLY"
    assert 5.0<result["min_abs_solar_noon_clock_shift_minutes"]<5.2
    assert 10.4<result["max_abs_solar_noon_clock_shift_minutes"]<10.6
    assert 8.8<result["mean_abs_solar_noon_clock_shift_minutes"]<9.1
    assert result["all_original_mirror_dates_unchanged"]
    assert result["noon_difference_independent_of_fixed_station_longitude"]
    assert len(result["date_pairs"])==41
    assert all(x["pair_has_matching_daylength_but_nonidentical_solar_noon"]
               for x in result["date_pairs"])
    assert all(x["daylength_difference_minutes"]<1.0
               for x in result["date_pairs"])
    assert all(x["sunrise_common_solar_phase_hour"]==6.
               and x["sunset_common_solar_phase_hour"]==18.
               for x in result["date_pairs"])
    assert not result["actual_station_sunrise_sunset_computed"]
    assert not result["original_hourly_operating_effort_verified"]
    assert not result["camera_or_ungulate_records_read"]
    assert not result["ecological_hysteresis_effect_measured"]
    assert not result["original_41_calendar_result_or_ODSP_inference_reclassified"]
    json.dumps(result,allow_nan=False)


def test_same_station_longitude_cancels_from_paired_solar_noon_difference():
    first,second=date(2022,5,1),date(2022,8,13)
    differences=[]
    for lon in (128.8,129.2,129.5):
        f=civil_solar_geometry(first,36.85,lon)
        s=civil_solar_geometry(second,36.85,lon)
        differences.append(s["solar_noon_clock_minute"]-f["solar_noon_clock_minute"])
        assert f["sunrise_clock_minute"]<f["solar_noon_clock_minute"]<f["sunset_clock_minute"]
    assert differences[0]==pytest.approx(differences[1],abs=1e-12)
    assert differences[2]==pytest.approx(differences[1],abs=1e-12)


def test_no_outcome_driven_rematching_or_altered_solar_basis():
    wrong=json.loads(json.dumps(CONTRACT))
    wrong["original_pair_count_required"]=20
    with pytest.raises(ValueError,match="frozen"):
        compare_original_41_mirror_noons(MAIN,wrong)
    changed=json.loads(json.dumps(MAIN))
    changed["preoutcome_structural_pairing"]["pair_min_calendar_separation_days"]=7
    with pytest.raises(ValueError,match="pairing rules"):
        compare_original_41_mirror_noons(changed,CONTRACT)


def test_never_infer_real_station_clock_or_camera_effort_from_representative_point():
    result=compare_original_41_mirror_noons(MAIN,CONTRACT)
    assert result["camera_or_ungulate_records_read"] is False
    assert result["actual_station_sunrise_sunset_computed"] is False
    assert result["ecological_hysteresis_effect_measured"] is False
