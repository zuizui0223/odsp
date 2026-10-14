"""Regression tests for genuinely published Bukhansan 11-station clock-hour summaries.

Input derives ONLY from author-uploaded Tables 1/2 and cross-checks all 24
printed column totals plus Tables 3/4. Not independent event data, and no
valid animal population p-value when camera/animal dependence is unknown.
"""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"scripts"/"run_bukhansan_author_published_same_camera_windows_v1.py"
s=importlib.util.spec_from_file_location("published_camera",FILE)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
PLAN=json.loads((ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json").read_text())

def test_total_457_matches_author_published_hour_and_habitat_margins():
    x=m.analyze(PLAN)
    assert x["status"]==m.STATUS
    assert len(x["all_11_public_station_code_summaries_with_zeros"])==11
    assert x["both_species_detected_site_count"]==7
    assert sum(r["water_deer_all"] for r in x["all_11_public_station_code_summaries_with_zeros"])==184
    assert sum(r["wild_boar_all"] for r in x["all_11_public_station_code_summaries_with_zeros"])==273
    assert x["published_3_window_source_counts"]["water_deer"]=={"01to06":74,"07to18":26,"19to24":84}
    assert x["published_3_window_source_counts"]["wild_boar"]=={"01to06":92,"07to18":33,"19to24":148}
    assert not x["hour_exact_operating_camera_effort_verified"]
    assert not x["source_date_phase_recoverable"]

def test_within_camera_ungulate_timing_direction_weak_in_site_units():
    x=m.analyze(PLAN)
    assert abs(x["pooled_water_vs_boar_late_early_odds_ratio"]-1.417184265)<1e-7
    sign=x["site_direction_diagnostic"]
    assert sign["water_deer_later_count"]==5
    assert sign["boar_later_count"]==2
    assert sign["n_non_ties"]==7
    assert sign["exact_two_sided_sign_p_not_independent_site_validated"]==.453125

def test_site_stratified_event_count_diagnostic_fragile_to_M2():
    x=m.analyze(PLAN)
    allsites=x["all_site_MH_CMH_PHOTO_INDEPENDENCE_NOT_VALIDATED"]
    excluded=x["exclude_M2_MH_CMH_PHOTO_INDEPENDENCE_NOT_VALIDATED"]
    assert abs(allsites["mh_morning_to_evening_water_vs_boar_OR"]-1.615826474)<1e-7
    assert abs(allsites["UNVALIDATED_EVENT_INDEPENDENCE_p"]-.046616409)<1e-7
    assert abs(excluded["mh_morning_to_evening_water_vs_boar_OR"]-1.331580447)<1e-7
    assert abs(excluded["UNVALIDATED_EVENT_INDEPENDENCE_p"]-.356179423)<1e-7
    assert not allsites["cluster_robust_biological_significance"]
    assert abs(x["M2_share_of_water_deer_published_events"]-.5)<1e-9
    assert abs(x["M2_share_of_wild_boar_published_events"]-(49/273))<1e-8
    assert not x["genuine_site_cluster_independence_verified"]
    assert not x["causal_mechanism_or_original_Uljin_41_pair_claimed"]

def test_published_24_hour_totals_guard_against_manual_transcription_error():
    broken=json.loads(json.dumps(PLAN))
    broken["derived_publication_site_six_hour_window_counts"][10]["water_deer"]["01to06"]+=1
    with pytest.raises(ValueError,match="SITE_HOUR_MARGINS"):
        m.analyze(broken)
    broken=json.loads(json.dumps(PLAN))
    broken["published_table_independent_checks"]["species_by_habitat"]["wild_boar"]["Forest"]+=1
    with pytest.raises(ValueError,match="HABITAT_COUNTS"):
        m.analyze(broken)

def test_no_preregistered_or_solar_hour_operation_promotion():
    broken=json.loads(json.dumps(PLAN))
    broken["limitations"]["independent_hourly_camera_ON_OFF_logs_available"]=True
    with pytest.raises(ValueError,match="INFERENCE_CONTRACT"):
        m.analyze(broken)
    broken=json.loads(json.dumps(PLAN))
    broken["analysis"]["selected_postpublication_equal_six_row_windows"]["19to24"]=[18,19,20,21,22,23]
    with pytest.raises(ValueError,match="CLOCK_WINDOW"):
        m.analyze(broken)


def test_common_station_observed_clock_profile_vs_station_weights():
    x=m.analyze(PLAN)
    w=x["shared_site_symmetric_photo_composition_observation_only"]
    assert w["number_of_both_species_clock_window_sites"]==7
    assert abs(w["water_deer_late_photo_share_common_sites"]-.46835443)<1e-7
    assert abs(w["boar_late_photo_share_common_sites"]-.384210526)<1e-7
    assert abs(w["water_minus_boar_late_share_diff_pp"]-8.414390406)<1e-7
    assert abs(w["within_camera_detected_time_profile_component_pp"]-10.220464754)<1e-7
    assert abs(w["different_camera_weight_composition_component_pp"]-(-1.806074348))<1e-7
    assert w["component_sum_identity_verified"]
    assert w["conditional_on_posthoc_co_detected_sites"]
    assert w["different_camera_weight_component_is_NOT_caused_by_species"]
    assert not w["population_effect_or_true_activity_claimed"]
