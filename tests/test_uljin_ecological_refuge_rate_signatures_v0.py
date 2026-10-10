"""Ecological mechanism discrimination, not a synthetic clock-method leaderboard."""
from datetime import date
import json
from pathlib import Path
import pytest

from odsp.uljin_ecological_refuge_rate_signatures_v0 import (
    CONTRAST_IDS,compute_matched_daylength_zone_signatures,
)
from odsp.uljin_ecological_temporal_refuge_v0 import (
    assert_frozen_ecology,solar_zone_bounds
)

ROOT=Path(__file__).resolve().parents[1]
HYPOTHESIS=json.loads(
    (ROOT/"ULJIN_FOUR_UNGULATE_TEMPORAL_REFUGE_ECOLOGY_V0_CONTRACT.json").read_text())
PLAN=json.loads((ROOT/"ULJIN_ECOLOGICAL_ZONE_SIGNATURE_V0_CONTRACT.json").read_text())
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def _events(day_text:str,station:str,taxon:str,core:int,edge:int,night:int):
    """Synthetic fixture-only time stamps, >30min apart within one zone."""
    zones=solar_zone_bounds(date.fromisoformat(day_text))
    observations=[]
    for z,number in (("daylight_core",core),("daylight_edge",edge),("night",night)):
        for i in range(number):
            bounds=zones[z]
            # Distinct trial positions. First/second of edge/night
            # use their two disconnected intervals when available.
            a,b=bounds[i%len(bounds)]
            minutes=a+(b-a)*(.35+(.2*(i//len(bounds))))
            h=int(minutes//60)
            m=int(minutes%60)
            seconds=round((minutes-h*60-m)*60)
            if seconds==60:
                m+=1;seconds=0
            observations.append({
                "Station":station,"Species":taxon,
                "Date":day_text,"Time":f"{h:02d}:{m:02d}:{seconds:02d}"
            })
    return observations


def _frame():
    source_days=assert_frozen_ecology(HYPOTHESIS,CAL)
    rows=[]
    operation={}
    for d,b in source_days.items():
        operation[("UJ1_test",d)]=[(0.,1440.)]
        if b=="rising":
            rows.extend(_events(d,"UJ1_test","Goral",2,1,1))
            rows.extend(_events(d,"UJ1_test","Roe deer",1,1,1))
        else:
            rows.extend(_events(d,"UJ1_test","Goral",1,2,1))
            rows.extend(_events(d,"UJ1_test","Roe deer",1,1,2))
        rows.extend(_events(d,"UJ1_test","Water deer",1,1,1))
    return rows,operation


def _run(rows,operation,verified=True):
    return compute_matched_daylength_zone_signatures(
        PLAN,HYPOTHESIS,CAL,rows,operation,
        independently_verified_v1p1_event_member=verified,
        independently_verified_original_operation_log=verified)


def test_original_ecological_h1_and_h2_independent_with_opportunity_denominator():
    rows,operation=_frame()
    out=_run(rows,operation)
    assert out["status"]=="VERIFIED_EFFORT_ADJUSTED_DETECTION_RATE_SIGNATURES_DESCRIPTIVE_ONLY"
    assert out["operation_only_selected_site_pair_cells"]==41
    assert out["excluded_site_pair_cells_based_only_on_operation_hours"]==0
    assert out["original_41_calendar_pairs_unchanged"]
    assert out["site_exposure_not_species_event_selection"]
    assert out["external_detector_q_NOT_calibrated_no_true_activity_zeitgeber_claim"]
    assert len(out["four_ungulate_ecological_detection_rate_signatures"])==4
    r={x["Species"]:x for x in out["four_ungulate_ecological_detection_rate_signatures"]}
    assert r["Goral"]["H1_core_vs_daylight_edge"][
        "falling_minus_rising_log_rate_ratio"]==pytest.approx(-2*__import__("math").log(2))
    assert r["Goral"]["H2_night_vs_all_daylight"][
        "falling_minus_rising_log_rate_ratio"]==pytest.approx(0,abs=1e-10)
    assert r["Roe deer"]["H1_core_vs_daylight_edge"][
        "falling_minus_rising_log_rate_ratio"]==pytest.approx(0,abs=1e-10)
    assert r["Roe deer"]["H2_night_vs_all_daylight"][
        "falling_minus_rising_log_rate_ratio"]==pytest.approx(__import__("math").log(2))
    assert r["Water deer"]["H1_core_vs_daylight_edge"][
        "falling_minus_rising_log_rate_ratio"]==pytest.approx(0,abs=1e-10)
    assert r["Wild boar"]["total_matched_pair_events"]==0
    assert r["Wild boar"]["H1_core_vs_daylight_edge"]["status"]==(
        "UNDEFINED_ZERO_EVENT_RATE_NO_PSEUDOCOUNT")
    assert r["Wild boar"]["H2_night_vs_all_daylight"][
        "falling_minus_rising_log_rate_ratio"] is None
    exposure={
        (z["branch"],z["zone"]):z["camera_hours"]
        for z in out["all_three_original_zone_camera_hours_by_branch"]
    }
    # The TWO daylight zones have equal real astronomical durations
    # only when camera operation is full-day. All zones sum 41*24h.
    for br in ("rising","falling"):
        assert exposure[(br,"daylight_core")]==pytest.approx(
            exposure[(br,"daylight_edge"),],rel=1e-10)
        assert sum(exposure[(br,z)] for z in (
            "daylight_core","daylight_edge","night"))==pytest.approx(41*24)


def test_source_event_outside_camera_operating_hours_fail_closed():
    rows,operation=_frame()
    first=next(iter(operation))
    operation[first]=[(0.,10.)]
    # One or more matched-date events now fall outside source camera's
    # attested operation hours: should never report source ecology.
    assert _run(rows,operation)["status"] in (
        "HOLD_SOURCE_EVENT_OUTSIDE_VERIFIED_CAMERA_OPERATION",
        "HOLD_NO_COMMON_SITE_PAIR_WITH_POSITIVE_SOURCE_HOURS_ALL_ZONES")
    # Real source member absent => never compute ecological effect.
    assert _run(rows,operation,verified=False)["rate_effect_computed"] is False


def test_source_incomplete_or_unmatched_camera_has_no_ecological_summary():
    rows,operation=_frame()
    removed=operation.pop(next(iter(operation)))
    assert _run(rows,operation)["status"]==(
        "HOLD_INCOMPLETE_INDEPENDENT_CAMERA_STATION_DATE_OPERATION")
    assert not _run(rows,operation)["rate_effect_computed"]
    rows,operation=_frame()
    rows.append({"Station":"UJ9_invalid","Species":"Goral",
                 "Date":next(iter(assert_frozen_ecology(HYPOTHESIS,CAL))),
                 "Time":"12:00:00"})
    assert _run(rows,operation)["status"]==(
        "HOLD_EVENT_STATION_NOT_IN_INDEPENDENT_CAMERA_OPERATION_ROSTER")


def test_no_species_specific_site_selection_and_zeros_remain_included():
    rows,operation=_frame()
    days=assert_frozen_ecology(HYPOTHESIS,CAL)
    # Extra physical camera observed only in one solar time zone
    # on each date; this station is excluded by OPERATION only.
    for d in days:
        bounds=solar_zone_bounds(date.fromisoformat(d))
        start,end=bounds["daylight_core"][0]
        operation[("UJ2_test",d)]=[(start+5,end-5)]
    out=_run(rows,operation)
    assert out["original_physical_camera_roster_size"]==2
    assert out["operation_only_selected_site_pair_cells"]==41
    assert out["excluded_site_pair_cells_based_only_on_operation_hours"]==41
    assert len(out["four_ungulate_ecological_detection_rate_signatures"])==4


def test_ecological_contrast_contract_redefinition_rejected():
    rows,operation=_frame()
    changed=json.loads(json.dumps(PLAN))
    changed["rate_contrasts"][1]["id"]="SOLAR_NOON_WINS"
    with pytest.raises(ValueError,match="modified"):
        compute_matched_daylength_zone_signatures(
            changed,HYPOTHESIS,CAL,rows,operation,
            independently_verified_v1p1_event_member=True,
            independently_verified_original_operation_log=True)
