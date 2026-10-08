"""No-source continuous solar-phase uptime change-of-measure tests."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import numpy as np
import pytest

from odsp.uljin_solar_phase_device_exposure_v0 import (
    solar_phase_operating_exposure,
    phase_to_clock,clock_to_phase,
    phase_exposure_first_known_truth_control,
)
from odsp.uljin_original_pairs_equation_of_time_v0 import civil_solar_geometry

ROOT=Path(__file__).resolve().parents[1]
CAL=json.loads(
    (ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text()
)
PLAN=json.loads(
    (ROOT/"ULJIN_SOLAR_PHASE_DEVICE_EXPOSURE_V0_CONTRACT.json").read_text()
)


def test_frozen_original_mirror_pair_and_source_free_cross_clock_bin_control():
    result=phase_exposure_first_known_truth_control(CAL,PLAN)
    assert result["status"]=="PASS_SOURCE_FREE_SOLAR_PHASE_DEVICE_MEASURE"
    assert result["original_unmodified_astronomy_pairs"]==41
    assert result["full_day_phase_hours_ascending"]==pytest.approx([4]*6)
    assert result["full_day_phase_hours_descending"]==pytest.approx([4]*6)
    assert result["daylight_only_phase_hours_ascending"]==pytest.approx(
        [0,2,4,4,2,0],abs=1e-9
    )
    assert result["rising_civil_clock_hour"]<8.
    assert result["falling_civil_clock_hour"]>=8.
    assert result["same_solar_phase_example"]==pytest.approx(
        clock_to_phase(result["falling_civil_clock_hour"],date(2022,8,13)),
        abs=1e-10
    )
    assert not result["real_camera_operation_intervals_read"]
    assert not result["real_animal_source_events_read"]
    assert not result["photoperiod_hysteresis_effect_estimated"]
    json.dumps(result,allow_nan=False)


def test_full_day_uptime_maps_to_four_phase_hours_per_bin_on_both_dates():
    for day in (date(2022,5,1),date(2022,8,13)):
        out=solar_phase_operating_exposure(day,[(0.,24.)])
        assert out==pytest.approx([4.]*6,abs=1e-10)
        assert sum(out)==pytest.approx(24.,abs=1e-10)


def test_source_interval_union_prevents_double_counting():
    day=date(2022,5,1)
    shared=solar_phase_operating_exposure(day,[(1,3),(2,4)])
    expected=solar_phase_operating_exposure(day,[(1,4)])
    assert shared==pytest.approx(expected,abs=1e-10)


def test_half_day_uptime_has_exact_solar_jacobian_exposure_not_just_clock_hours():
    day=date(2022,8,13)
    a=solar_phase_operating_exposure(day,[(0,12)])
    b=solar_phase_operating_exposure(day,[(12,24)])
    both=solar_phase_operating_exposure(day,[(0,24)])
    assert all(abs(a[i]+b[i]-both[i])<1e-10 for i in range(6))
    assert sum(a)!=pytest.approx(12,abs=1e-3)


def test_invalid_exposure_cannot_be_imputed_from_camera_nights_or_bad_timestamps():
    day=date(2022,5,1)
    for invalid in (
        [(-1.,4.)],[(18.,25.)],[(4.,4.)],[(13.,6.)],
        [("night",24.)],[(0.,float("nan"))],
    ):
        with pytest.raises(ValueError):
            solar_phase_operating_exposure(day,invalid)


def test_exact_phase_inverse_across_sunrise_sunset_and_midnight():
    day=date(2022,8,13)
    for t in np.linspace(0,23.999,24000):
        phase=clock_to_phase(float(t),day)
        recovered=phase_to_clock(phase,day)
        error=((recovered-t+12)%24)-12
        assert abs(error)<1e-10


def test_changing_original_after_freeze_rejected():
    frozen=json.loads(json.dumps(PLAN))
    frozen["original_pairs"]=40
    with pytest.raises(ValueError,match="frozen"):
        phase_exposure_first_known_truth_control(CAL,frozen)
