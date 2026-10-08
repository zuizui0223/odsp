"""Strictly source-free synthetic censoring cases, original 41 pairs kept."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from odsp.uljin_operation_date_censored_support_v0 import (
    classify_date_censored_mirror_support,
)

ROOT=Path(__file__).resolve().parents[1]
CAL=json.loads((ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())
PLAN=json.loads((ROOT/"ULJIN_OPERATION_DATE_CENSORED_SUPPORT_V0_CONTRACT.json").read_text())

def deploy(site,a="2022-04-01",b="2022-10-01"):
    return {"Station":site,"DeploymentStartDate":a,"DeploymentEndDate":b}
def outage(site,a,b):
    return {"Station":site,"DowntimeStartDate":a,"DowntimeEndDate":b}
def run(dep,off=(),complete=True):
    return classify_date_censored_mirror_support(
       CAL,PLAN,dep,list(off),synthetic_complete_downtime_roster=complete)
def numbers(x,region="UJ1"):
    return x["region_only_counts"][region]


def test_original_41_full_interior_days_certifiably_operating_without_invented_time():
    r=run([deploy("UJ1_EXAMPLE_1"),deploy("UJ2_EXAMPLE_1")])
    assert r["status"]=="SYNTHETIC_INTERVAL_CENSORED_OPERATION_BOUNDS_ONLY"
    assert r["original_unchanged_date_pair_count"]==41
    for region in ("UJ1","UJ2"):
        assert numbers(r,region)["guaranteed_eligible_pairs"]==41
        assert numbers(r,region)["ambiguous_pairs"]==0
        assert numbers(r,region)["definitely_ineligible_pairs"]==0
    assert not r["animal_detection_rows_read"]
    assert not r["real_Uljin_pair_eligibility_claimed"]
    assert not r["original_hardware_source_independence_attested"]
    assert "UJ1_EXAMPLE_1" not in json.dumps(r)


def test_critical_deployment_boundary_date_never_imputed_as_complete_day():
    r=run([deploy("UJ1_EXAMPLE_1","2022-05-01","2022-10-01")])
    assert numbers(r)["guaranteed_eligible_pairs"]==40
    assert numbers(r)["ambiguous_pairs"]==1
    assert numbers(r)["definitely_ineligible_pairs"]==0


def test_unknown_within_day_outage_makes_one_pair_ambiguous():
    r=run([deploy("UJ1_EXAMPLE_1")],
          [outage("UJ1_EXAMPLE_1","2022-05-01","2022-05-01")])
    assert numbers(r)["guaranteed_eligible_pairs"]==40
    assert numbers(r)["ambiguous_pairs"]==1


def test_certain_full_day_outage_fails_one_pair_even_under_upper_bound():
    r=run([deploy("UJ1_EXAMPLE_1")],
          [outage("UJ1_EXAMPLE_1","2022-04-30","2022-05-02")])
    # May 1 is an interior fully stopped day. May 2 is the unknown
    # downtime end-date and is itself another frozen ascending mirror day.
    assert numbers(r)["guaranteed_eligible_pairs"]==39
    assert numbers(r)["definitely_ineligible_pairs"]==1
    assert numbers(r)["ambiguous_pairs"]==1


def test_single_calendar_day_deployment_cannot_supply_both_mirror_dates():
    r=run([deploy("UJ1_EXAMPLE_1","2022-05-01","2022-05-01")])
    assert numbers(r)["guaranteed_eligible_pairs"]==0
    assert numbers(r)["definitely_ineligible_pairs"]==41


def test_overlaps_union_and_no_double_count_of_camera_hours():
    one=run([deploy("UJ1_EXAMPLE_1")],
            [outage("UJ1_EXAMPLE_1","2022-05-01","2022-05-01")])
    two=run([deploy("UJ1_EXAMPLE_1"),deploy("UJ1_EXAMPLE_1","2022-04-20","2022-09-01")],
            [outage("UJ1_EXAMPLE_1","2022-05-01","2022-05-01"),
             outage("UJ1_EXAMPLE_1","2022-05-01","2022-05-01")])
    assert one["region_only_counts"]==two["region_only_counts"]


def test_missing_outage_completeness_holds_without_making_eligibility_claim():
    x=run([deploy("UJ1_EXAMPLE_1")],complete=False)
    assert x["status"]=="HOLD_DOWNTIME_COMPLETENESS_UNKNOWN"
    assert x["no_station_pair_eligibility_inferred"]
    assert "region_only_counts" not in x
    assert not x["real_source_archive_or_operations_read"]


@pytest.mark.parametrize("invalid_dep,invalid_down",[
   ([deploy("UJ1_EXAMPLE_1","2022-10-01","2022-04-01")],[]),
   ([deploy("UJ1_EXAMPLE_1","2022-04-01T12:00","2022-10-01")],[]),
   ([deploy("INVALID01")],[]),
   ([deploy("UJ1_EXAMPLE_1")],[outage("UJ2_NONDEPLOYED","2022-05-01","2022-05-02")]),
   ([deploy("UJ1_EXAMPLE_1")],[outage("UJ1_EXAMPLE_1","2022-03-01","2022-03-02")]),
])
def test_malformed_dates_and_outside_hardware_windows_fail_closed(invalid_dep,invalid_down):
    with pytest.raises(ValueError):
        run(invalid_dep,invalid_down)


def test_forbidden_original_data_mode_and_calendar_reoptimization_fail():
    with pytest.raises(ValueError,match="synthetic only"):
        classify_date_censored_mirror_support(
            CAL,PLAN,[deploy("UJ1_EXAMPLE_1")],[],
            synthetic_complete_downtime_roster=True,input_kind="actual_EcoBank")
    altered=json.loads(json.dumps(CAL))
    altered["preoutcome_structural_pairing"]["pair_min_calendar_separation_days"]=5
    with pytest.raises(ValueError):
        classify_date_censored_mirror_support(
            altered,PLAN,[deploy("UJ1_EXAMPLE_1")],[],
            synthetic_complete_downtime_roster=True)
    changed=json.loads(json.dumps(PLAN))
    changed["conservative_interval_bounds"][
        "minimum_guaranteed_or_possible_active_hours_per_bin"]=0
    with pytest.raises(ValueError,match="contract"):
        classify_date_censored_mirror_support(
            CAL,changed,[deploy("UJ1_EXAMPLE_1")],[],
            synthetic_complete_downtime_roster=True)
    changed_semantics=json.loads(json.dumps(PLAN))
    changed_semantics["conservative_interval_bounds"]["guaranteed_active"]=(
        "union(possible deployment) minus union(possible downtime)"
    )
    with pytest.raises(ValueError,match="contract"):
        classify_date_censored_mirror_support(
            CAL,changed_semantics,[deploy("UJ1_EXAMPLE_1")],[],
            synthetic_complete_downtime_roster=True)
