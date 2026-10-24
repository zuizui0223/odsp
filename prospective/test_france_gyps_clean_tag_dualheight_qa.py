"""Frozen historical cohort has one scored alias bird, not two new studies."""
import hashlib
import pytest
from prospective.france_gyps_clean_tag_dualheight_qa import (
   EXCLUDED,EXCLUDED_TAG,CLEAN_27_SHA,OLD_28_SHA,
   sha_ids,check_historical_result,compare_sensors,verify_preheight
)

MOST="2019-Causses-Ad-Mostuejouls-IIE-182008"
PEY="2018-Causses-Ad-Peycare-HTK-182208"

def fake_original():
    old={f"bird{i:02d}":{"gain":.03} for i in range(26)}
    old[MOST]={"gain":.04}
    return {"terminal":"paired_sensor_robust_individual_height_shape",
       "preheight_bird_roster_sha256":OLD_28_SHA,
       "sensor_results":{
         "GPS":{"observed":{"per_bird":old},"holm_p_upper":.002},
         "BAROMETRIC":{"observed":{"per_bird":old},"holm_p_upper":.002}
       }}

def test_frozen_source_quarantine_has_exactly_nonbird_and_two_tag_collision_aliases():
    assert EXCLUDED_TAG=="182208"
    assert EXCLUDED=={"Test géodésie ornitela",MOST,PEY}
    assert len(CLEAN_27_SHA)==64
    assert len(OLD_28_SHA)==64

def test_historical_27_scored_birds_26_overlap_with_27_clean_source():
    original=fake_original()
    clean=set(f"bird{i:02d}" for i in range(26))|{"new_clean_bird"}
    old=check_historical_result(original,clean)
    assert len(old)==27 and len(old&clean)==26

def test_one_scored_wrong_device_changes_original_source_validation():
    original=fake_original()
    original["sensor_results"]["GPS"]["observed"]["per_bird"]["bird00"]["gain"]=.10
    clean={f"bird{i:02d}" for i in range(26)}|{"clean_bird"}
    assert check_historical_result(original,clean)

def test_original_score_population_must_be_27():
    orig=fake_original()
    del orig["sensor_results"]["BAROMETRIC"]["observed"]["per_bird"]["bird00"]
    with pytest.raises(ValueError,match="not on same scored birds"):
        check_historical_result(orig,{f"bird{i:02d}" for i in range(26)}|{"new_clean_bird"})

def test_new_both_modality_scores_use_exact_biological_bird_intersection():
    orig=fake_original()
    clean={f"bird{i:02d}":{"gain":.04 if i%2 else -.02} for i in range(26)}
    sensors={"GPS":{"observed":{"per_bird":clean},"holm_p_upper":.002},
             "BAROMETRIC":{"observed":{"per_bird":clean},"holm_p_upper":.002}}
    r=compare_sensors(sensors,orig)
    assert r["final_clean_sensor_scored_birds"]==26
    assert r["old_scored_birds_retained_exact"]==26
    assert r["old_scored_birds_lost_exact"]==1
    assert r["GPS_positive_raw_gain_birds"]==13
    assert r["same_bird_positive_both"]==13
    assert r["historical_old_result_reinterpreted_as_clean"] is False

def test_source_independence_does_not_follow_from_literal_id_hash_alone():
    assert sha_ids({"a","b"})==hashlib.sha256("a\nb".encode()).hexdigest()
