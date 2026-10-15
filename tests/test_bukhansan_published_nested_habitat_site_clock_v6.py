"""Real author-derived Bukhansan 11-site record scale ecology.

Exact source category counts, not animal encounter independence, random
habitat assignment, calibrated optical q or camera-hour exposure.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sp=importlib.util.spec_from_file_location(
    "habitat_site_clock_v6",
    ROOT/"scripts"/"run_bukhansan_published_nested_habitat_site_clock_v6.py")
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)
PLAN=json.loads((ROOT/"BUKHANSAN_NESTED_HABITAT_SITE_CLOCK_V6_CONTRACT.json").read_text())
SOURCE=json.loads((ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json").read_text())
V3PLAN=json.loads((ROOT/"BUKHANSAN_PUBLIC_JOINT_SPACE_CLOCK_OVERLAP_V3_CONTRACT.json").read_text())


def compute():
    return m.analyze(PLAN,SOURCE,V3PLAN)


def test_original_457_source_records_all_11_sites_and_exact_nested_tv_identity():
    out=compute()
    assert out["status"]==m.STATUS
    h=out["full_11_camera_nested_distribution"]
    assert h["source_total_species_records"]=={"water_deer":184,"wild_boar":273}
    assert h["number_of_public_source_camera_codes"]==11
    assert h["number_of_published_wetland_cameras"]==2
    assert h["habitat_level_record_TV"]==pytest.approx(.326763816,abs=1e-8)
    assert h["camera_level_record_TV"]==pytest.approx(.347885810,abs=1e-8)
    assert h["camera_x_clock_level_record_TV"]==pytest.approx(.384535754,abs=1e-8)
    assert (h["habitat_level_record_TV"]
            + h["additional_camera_given_habitat_TV"]
            + h["additional_clock_given_camera_TV"])==pytest.approx(
                h["camera_x_clock_level_record_TV"],abs=3e-9)
    assert h["tv_nested_source_marginalization_exact"]
    assert not h["source_camera_habitat_selection_mechanism_proved"]


def test_habitat_dominates_source_camera_record_mismatch_but_not_population_niche():
    h=compute()["full_11_camera_nested_distribution"]
    assert h["additional_camera_given_habitat_TV"]==pytest.approx(.021121994,abs=1e-8)
    assert h["additional_clock_given_camera_TV"]==pytest.approx(.036649944,abs=1e-8)
    assert h["fraction_of_camera_record_mismatch_at_habitat_level"]==pytest.approx(.939284692,abs=1e-8)
    assert h["fraction_of_joint_record_mismatch_at_first_habitat_level"]==pytest.approx(.849761855,abs=1e-8)
    assert h["fraction_of_joint_record_mismatch_from_additional_camera"]==pytest.approx(.054928557,abs=1e-8)
    assert h["fraction_of_joint_record_mismatch_from_additional_clock"]==pytest.approx(.095309588,abs=1e-8)
    assert h["period_widths_are_6_12_6_clock_labels_not_solar"]


def test_residual_extra_within_habitat_mismatch_forest_G19_only():
    h=compute()["full_11_camera_nested_distribution"]
    areas={x["habitat"]:x for x in h["per_habitat_source_station_locus"]}
    assert len(areas)==2
    forest,wet=areas["Forest"],areas["Wetland"]
    assert forest["source_water_records"]==74
    assert forest["source_boar_records"]==199
    assert wet["source_water_records"]==110
    assert wet["source_boar_records"]==74
    assert forest["additional_within_habitat_camera_TV"]==pytest.approx(.021121994,abs=1e-8)
    assert wet["additional_within_habitat_camera_TV"]==0
    assert forest["local_reversal_station_codes"]==["G19"]
    assert wet["local_reversal_station_codes"]==[]
    assert forest["SEPARATE_within_habitat_species_normalized_site_overlap"]==pytest.approx(
        .623455113,abs=1e-8)
    assert wet["SEPARATE_within_habitat_species_normalized_site_overlap"]==pytest.approx(
        .825798526,abs=1e-8)
    assert not forest["causal_habitat_preference_inferred"]


def test_M2_omission_reverses_what_scale_appears_primary_without_change_to_source():
    result=compute()
    bysite={x["omitted_original_published_camera"]:x for x in
            result["all_11_leave_single_camera_out_nested_TV"]}
    assert len(bysite)==11
    noM2=bysite["M2"]
    assert noM2["retained_water_record_count"]==92
    assert noM2["retained_boar_record_count"]==224
    assert noM2["retained_habitat_cameras"]==1
    assert noM2["habitat_TV"]==pytest.approx(.084045031,abs=1e-8)
    assert noM2["camera_TV"]==pytest.approx(.337927019,abs=1e-8)
    assert noM2["joint_camera_clock_TV"]==pytest.approx(.355590062,abs=1e-8)
    assert noM2["additional_camera_given_habitat_TV"]==pytest.approx(.253881988,abs=1e-8)
    assert noM2["additional_clock_given_camera_TV"]==pytest.approx(.017663043,abs=1e-8)
    assert noM2["fraction_of_camera_record_mismatch_at_habitat_level"]==pytest.approx(.248707639,abs=1e-8)
    assert noM2["fraction_of_joint_record_mismatch_at_habitat_level"]==pytest.approx(.236353712,abs=1e-8)
    assert not noM2["ecological_significance_claimed"]


def test_remove_G19_erases_within_habitat_resolution_and_all_Loo_preserve_margins():
    result=compute()
    loo=result["all_11_leave_single_camera_out_nested_TV"]
    assert [x["omitted_original_published_camera"] for x in loo]==list(m.SITES)
    assert all(x["retained_publication_11_sites_except_omitted"] for x in loo)
    assert all(x["species_record_totals_recomputed_for_omission"] for x in loo)
    g19=next(x for x in loo if x["omitted_original_published_camera"]=="G19")
    assert g19["additional_camera_given_habitat_TV"]==pytest.approx(0,abs=1e-8)
    assert g19["habitat_TV"]==pytest.approx(.442310303,abs=1e-8)
    assert g19["joint_camera_clock_TV"]==pytest.approx(.446314646,abs=1e-8)
    m1=next(x for x in loo if x["omitted_original_published_camera"]=="M1")
    assert m1["retained_habitat_cameras"]==1
    assert m1["fraction_of_camera_record_mismatch_at_habitat_level"]==pytest.approx(.934207177,abs=1e-8)
    assert not result["causal_habitat_or_interspecific_competition_test_performed"]


def test_corrupt_author_record_and_false_population_claim_fail_before_output():
    corrupt=json.loads(json.dumps(SOURCE))
    corrupt["derived_publication_site_six_hour_window_counts"][10]["water_deer"]["01to06"]+=1
    with pytest.raises(ValueError,match="SITE_HOUR_MARGINS"):
        m.analyze(PLAN,corrupt,V3PLAN)
    p=json.loads(json.dumps(PLAN))
    p["source_and_inference_holds"]["not_original_2022_Uljin_41_photoperiod_pairs_tested"]=False
    with pytest.raises(ValueError,match="UNJUSTIFIED_SOURCE_OR_CAUSAL"):
        m.analyze(p,SOURCE,V3PLAN)
    p=json.loads(json.dumps(PLAN))
    p["stage"]="PRE_DATA_PREREGISTERED"
    with pytest.raises(ValueError,match="AUTHOR_SOURCE_AND_POSTDATA"):
        m.analyze(p,SOURCE,V3PLAN)
    result=compute()
    assert not result["original_frozen_Uljin_2022_41_matched_pairs_tested"]
    assert not result["source_calendar_dates_and_camera_hourly_uptime_available"]
    assert result["source_assumptions_prior_clock_conditional_null_unaltered"]
