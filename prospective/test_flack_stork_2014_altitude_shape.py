"""Synthetic-only independent 2014 nestling stork altitude-shape gate.

Native archived altitude must stay unopened until these tests pass. Test
same-date, same-stage whole-session exchangeability, not GPS-fix permutations.
"""
import numpy as np
from prospective import medgull_sensitivity as scorer
from prospective.flack_stork_2014_altitude_shape import (
    labels_permuted_age_day, run_primary, ZIP_NAME, GPS_MD5, PREHEIGHT_FINGERPRINT,
    EXPECTED_PREHEIGHT_FLIGHT_BIRDS, EXPECTED_PREHEIGHT_50KM_BIRDS
)


def fake_cohort(n=11):
    data=[]
    ages={}
    for i in range(n):
        bird=f"stork{i:02d}"
        ages[bird]="nestling"
        for day in ("2014-08-12","2014-08-13","2014-08-14"):
            h=np.zeros(10,np.int64)
            h[i%4]=30
            h[5+i%4]=30
            data.append({"animal":bird,"day":day,"hist":{(101,203):h}})
    return scorer.pack(data),ages


def test_frozen_independent_source_id_count():
    assert ZIP_NAME=="Fall migration of white storks in 2014-gps.csv.zip"
    assert GPS_MD5=="c1fa0c4ca28d3fce5d61caaac36e87d2"
    assert PREHEIGHT_FINGERPRINT=="a741d2e1bc13d91a49f30ddb2cd13af97db855fd8be3d6c407b75ce827d1ec7d"
    assert EXPECTED_PREHEIGHT_FLIGHT_BIRDS==59
    assert EXPECTED_PREHEIGHT_50KM_BIRDS==11


def test_one_stage_session_exchange_preserves_date_uniqueness():
    x,age=fake_cohort(11)
    labels=labels_permuted_age_day(x,age,np.random.default_rng(20261020))
    assert len(labels)==len(x["labels"])
    assert np.mean(labels!=x["labels"])>0
    assert len(set(zip(labels,x["day_index"])))==len(labels)
    assert all(age[x["ids"][int(a)]]==age[x["ids"][int(b)]]
               for a,b in zip(x["labels"],labels))


def test_source_specific_stage_nestling_is_admissible_age_class():
    x,stage=fake_cohort(11)
    result,draws=run_primary(x,stage,draws=7)
    assert result["observed"]["eligible_birds"]==11
    assert result["eligible_by_age"]=={"nestling":11}
    assert result["reason"]=="insufficient_age_stratified_null_support"
    assert len(draws)==7
    assert result["terminal"]=="unavailable"


def test_unknown_stage_fails_prospective_age_registry_guard():
    x,stage=fake_cohort(11)
    stage={bird:"unknown" for bird in stage}
    outcome,draws=run_primary(x,stage,draws=7)
    assert outcome["terminal"]=="unavailable"
    assert outcome["reason"]=="unambiguous_age_crosswalk_below_95pct"
    assert draws==[]


def test_day_median_removes_constant_height_offset():
    a=scorer.center_bins([0.,20.,100.,150.])
    b=scorer.center_bins([1000.,1020.,1100.,1150.])
    assert np.array_equal(a,b)


def test_insufficient_unique_birds_is_no_biological_result():
    x,stage=fake_cohort(9)
    outcome,draws=run_primary(x,stage,draws=7)
    assert outcome["terminal"]=="unavailable"
    assert outcome["reason"]=="native_height_supported_birds_below_ten"
    assert draws==[]
