"""Pre-observation synthetic checks for age-aware 2013 migrant height-shape identity."""
import numpy as np
from prospective import medgull_sensitivity as engine
from prospective.stork_2013_migrant_altitude_shape import labels_permuted_age_day,run_primary


def synthetic(n=12):
    sessions=[]
    ages={}
    for i in range(n):
        bird=f"bird{i:02d}"
        ages[bird]="adult" if i<n//2 else "juv"
        for day in ("2013-08-12","2013-08-13","2013-08-14"):
            h=np.zeros(10,np.int64)
            h[i%4]=30
            h[4+i%4]=30
            sessions.append({"animal":bird,"day":day,"hist":{(101,203):h}})
    return engine.pack(sessions),ages


def test_same_individual_other_date_identity_uses_valid_bird_level_support():
    x,age=synthetic(12)
    r=engine.evaluate(x,1,"balanced")
    assert r["eligible_birds"]==12
    assert r["eligible_days"]==36
    assert r["mean_gain"]>0


def test_age_date_session_exchange_preserves_stage_and_date():
    x,ages=synthetic(12)
    perm=labels_permuted_age_day(x,ages,np.random.default_rng(20261020))
    assert len(perm)==len(x["labels"])
    assert np.mean(perm!=x["labels"])>0
    for obs,new in zip(x["labels"],perm):
        assert ages[x["ids"][int(obs)]]==ages[x["ids"][int(new)]]
    assert len(set(zip(perm,x["day_index"])))==len(perm)


def test_age_date_exchange_preserves_cohort_counts_per_day():
    x,ages=synthetic(12)
    labels=labels_permuted_age_day(x,ages,np.random.default_rng(42))
    for g in x["date_groups"]:
        before=[ages[x["ids"][int(x["labels"][i])]] for i in g]
        after=[ages[x["ids"][int(labels[i])]] for i in g]
        assert sorted(before)==sorted(after)


def test_missing_juvenile_adult_labels_fail_instead_of_claim_success():
    x,ages=synthetic(12)
    for k in ages:ages[k]="unknown"
    r,draws=run_primary(x,ages,draws=9)
    assert r["terminal"]=="unavailable"
    assert r["reason"]=="unambiguous_age_crosswalk_below_95pct"
    assert draws==[]


def test_zero_altitude_constant_additive_offset_is_removed_by_frozen_bin_model():
    a=engine.center_bins([100,130,190,230])
    b=engine.center_bins([600,630,690,730])
    assert np.array_equal(a,b)
