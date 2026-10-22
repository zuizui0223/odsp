"""Outcome-blind admission and paired sensor controls for new French Gyps cohort."""
from collections import defaultdict
import numpy as np
import pytest
from prospective.france_gyps_2019_dualsensor_identity import (
   paired_profiles,check_two_native_sensor_same_sessions,load_primary_gates,
   score_sensor,two_sensor_family,FRENCH5_SHA
)


def frozen_gates():
    birdids=[f"bird{i:02d}" for i in range(28)]
    import hashlib
    sha=hashlib.sha256("\n".join(sorted(birdids)).encode()).hexdigest()
    return {
     "numeric_native_GPS_height_values_read":False,
     "selected_native_GPS_five_minute_events":742423,
     "selected_biological_animals":30,
     "horizontal_day_eligibility_by_cell_m":{"5000":{
       "admitted_bird_ids":birdids,"source_bird_ID_sha256":sha
     }}
    },{"native_height_values_read":False,
       "source_independence_category":"DIFFERENT_STUDY_NAMES_AND_ZERO_EXACT_SOURCE_ANIMAL_IDS",
       "exact_bird_id_overlap_across_both_2026_Gyps_parents":0},birdids,sha


def test_source_parent_overlap_blocks_numeric_height_access(monkeypatch):
    import prospective.france_gyps_2019_dualsensor_identity as d
    a,b,birds,sha=frozen_gates()
    monkeypatch.setattr(d,"FRENCH5_SHA",sha)
    assert load_primary_gates(a,b)==set(birds)
    b["exact_bird_id_overlap_across_both_2026_Gyps_parents"]=1
    with pytest.raises(ValueError,match="overlap"):
        load_primary_gates(a,b)


def mkfirst(valid=True,secondsensor=True):
    z={}
    for bird in [f"B{i:02d}" for i in range(10)]:
        for day in ("2019-08-11","2019-08-12","2019-08-13"):
            for k in range(60):
                hh=8+k//12;mm=(k%12)*5
                t=f"{day} {hh:02d}:{mm:02d}:00.000"
                alt=120.+k%10*20.
                bar= alt+100. if secondsensor else "NA"
                z[bird,day,k]=(t,2.88,43.96,str(alt) if valid else "NOT_ALTITUDE",
                                 str(bar), "1.3","9")
    return z


def test_paired_native_sensors_identical_5km_fix_support(monkeypatch):
    import prospective.france_gyps_2019_dualsensor_identity as d
    # Fixed source denominator is 742423 in official data; use synthetic
    # preheight sample only to test identical-source support without forcing
    # total N by monkeypatching the unrelated global count.
    monkeypatch.setattr(d,"TOTAL_SELECTED_SOURCE",1800)
    x=mkfirst()
    gps,baro,quality=paired_profiles(x,{f"B{i:02d}" for i in range(10)})
    assert quality["source_firstfix_pair_complete_fraction"]==1
    assert len(gps)==len(baro)==30
    assert quality["fixed_eligible_birds_after_paired_qc"]==10
    assert quality["joint_5min_GPS_fixes_for_scoring"]==1800
    check_two_native_sensor_same_sessions(gps,baro)
    for s,t in zip(gps,baro):
        for c in s["hist"]:
            assert np.array_equal(s["hist"][c],t["hist"][c])


def test_missing_barometric_native_height_does_not_trigger_fake_agreement(monkeypatch):
    import prospective.france_gyps_2019_dualsensor_identity as d
    monkeypatch.setattr(d,"TOTAL_SELECTED_SOURCE",1800)
    gps,baro,quality=paired_profiles(mkfirst(secondsensor=False),
                    {f"B{i:02d}" for i in range(10)})
    assert gps is None and baro is None
    assert quality["reason"]=="fixed_studywide_80percent_joint_sensor_quality_not_met"


def test_both_sensor_score_require_original_date_block_null_but_no_rescue(monkeypatch):
    import prospective.france_gyps_2019_dualsensor_identity as d
    monkeypatch.setattr(d,"TOTAL_SELECTED_SOURCE",1800)
    gps,baro,quality=paired_profiles(mkfirst(),{f"B{i:02d}" for i in range(10)})
    # One native sensor original 10-bird x 3-day, score donor support exists,
    # but 7 exploratory synthetic permutations cannot satisfy fixed 950 valid.
    x,draws=score_sensor(gps,"GPS",randomizations=7)
    assert x["terminal"]=="unavailable"
    assert x["calibration"]["requested"]==7
    assert len(draws)==7


def test_unavailable_one_sensor_is_always_p_one_in_two_sensor_family():
    records={
      "GPS":{"terminal":"tested_before_two_sensor_Holm",
             "calibration":{"p_upper":.001,"observed_minus_valid_null_mean":.2}},
      "BAROMETRIC":{"terminal":"unavailable","reason":"native altitude absent"}
    }
    two_sensor_family(records)
    assert records["BAROMETRIC"]["family_p_value"]==1.
    assert records["GPS"]["holm_p_upper"]==.002
    assert records["GPS"]["terminal"]=="supported_own_bird_altitude_shape"
