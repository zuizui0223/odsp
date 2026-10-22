"""Frozen French Gyps, paired native GPS/BARO, regional wind calendar null.

Tests use nonnumeric/unopened source metadata fixtures; no source heights from
the archived French Dataverse GPS study are inspected or outcome-tuned here.
"""
from collections import Counter
from pathlib import Path
import numpy as np
import pytest

from prospective.run_france_gyps_era5_2019_5km_bird_vs_shared import (
    SEED, MIN_BIRDS,validate_noheight_receipt,permute_calendar_days,
    paired_profiles,fixed_target_score,calibrate,sensors_holm
)
from prospective.france_wind_context_height_kernel import pack_profiles
from prospective.france_species_shared_regional_wind_kernel import (
    build_shared_context,score_shared_vs_bird
)


def small_source():
    return {
        "analysis":"FRANCE_GYPS_2019_2021_ERA5_WIND_5KM_SOURCE_ADMISSION_V1",
        "source_zip_md5":"b18cc8004d311d19ff24060f655178bf",
        "no_altitude_values_accessed_this_analysis":True,
        "source_preheight_reinspection":{
            "prior_GPS_first5min_fix_count":742078,
            "prior_preheight_5km_bird_sha":"031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928",
            "distinct_biological_bird_ids_after_quarantine":27,
            "source_first5min_after_tag_quarantine":726993,
            "excluded_bird_count":2,
            "tag_collision_by_native_id":{
                "182208":["bad1","bad2"]
            }
        },
        "independent_ERA5_regional_wind":{
            "n_calendar_days":1096,
            "per_calendar_day_state_sha256":"fd1cc44366f25429184eb7560097b90c8f44024b91d3beb3e4244dd79123cf74"
        },
        "population":{
            "5km_shared_species_wind_reference_support":{
                "birds":25,
                "bird_days":1844,
                "selected_GPS_fixes":59616,
                "bird_IDs_sha256":"0528f4c8cff551ccc43a65d97f661b0f01a2529b9f355012770057e227e5d6f0",
                "admitted":True,
                "bird_IDs":[f"b{i}" for i in range(25)]
            }
        }
    }


def test_exact_quarantined_nonheight_roster_required():
    target,aliased=validate_noheight_receipt(small_source())
    assert len(target)==25
    assert aliased=={"bad1","bad2"}


def test_alias_collision_drift_stops_before_native_height():
    p=small_source()
    p["source_preheight_reinspection"]["tag_collision_by_native_id"]={}
    with pytest.raises(ValueError,match="ambiguous tag"):
        validate_noheight_receipt(p)


def test_wind_randomization_preserves_monthwide_common_weather():
    dates=[f"2019-05-{d:02d}" for d in range(1,21)]
    labels={d:(0 if i<5 else (1 if i<10 else -1)) for i,d in enumerate(dates)}
    labels.update({f"2019-06-{d:02d}":(0 if d<10 else 1) for d in range(1,21)})
    changed=permute_calendar_days(labels,np.random.default_rng(SEED))
    assert changed!=labels
    for month in ("2019-05","2019-06"):
        a=sorted(v for d,v in labels.items() if d.startswith(month))
        b=sorted(v for d,v in changed.items() if d.startswith(month))
        assert a==b
    # Each calendar day is exactly one state for all birds.
    assert all(changed[d]==changed[d] for d in changed)


def test_native_two_sensor_day_alignment_requires_same_source_fixes():
    rows={}
    for day in ("2019-05-11","2019-05-12"):
        for i in range(25):
            rows["b0",day,i]=(
                f"{day} 08:{i*2:02d}:00",3.2,44.2,
                str(100+i),str(600+i),"2.2","10"
            )
    gps,baro,q=paired_profiles(rows,{"b0"})
    assert q["paired_native_source_quality_fraction"]==1
    assert len(gps)==2 and len(baro)==2
    for a,b in zip(gps,baro):
        assert (a["bird"],a["day"])==(b["bird"],b["day"])
        assert sum(x.sum() for x in a["hists"].values())==25
        assert {c:int(x.sum()) for c,x in a["hists"].items()}=={
            c:int(x.sum()) for c,x in b["hists"].items()
        }


def test_native_height_missing_earliest_cannot_be_rescued():
    rows={
        ("b0","2019-05-11",k):(
           f"2019-05-11 08:{k*2:02d}:00",3.2,44.2,
           "MISSING" if k>=3 else "100",str(500+k),"2.2","10"
        )
        for k in range(25)
    }
    g,b,q=paired_profiles(rows,{"b0"})
    assert g is None and b is None
    assert q["paired_native_source_quality_fraction"]==3/25


def test_only_frozen_25_target_birds_count_as_biological_replicates():
    scores={"mean_gain":1000.,"eligible_birds":3,"eligible_bird_days":30,
      "scored_fixes":900,
      "per_bird":{
         "target1":{"gain":.1,"low_days":2,"high_days":2,"scored_fixes":120},
         "target2":{"gain":.5,"low_days":3,"high_days":3,"scored_fixes":150},
         "DONOR_NOT_TARGET":{"gain":500.,"low_days":4,"high_days":4,"scored_fixes":400}
      }}
    x=fixed_target_score(scores,{"target1","target2"})
    assert x["eligible_birds"]==2
    assert abs(x["mean_gain"]-.3)<1e-12
    assert x["eligible_bird_days"]==10
    assert x["scored_fixes"]==270
    assert "DONOR_NOT_TARGET" not in x["per_bird"]


def test_two_native_sensor_Holm_and_unavailable_are_preserved():
    rows={
      "GPS":{"terminal":"exploratory_evaluated",
             "calibration":{"p_upper":.01,"observed_minus_null_mean":.2}},
      "BAROMETRIC":{"terminal":"unavailable","calibration":{"p_upper":.01}}
    }
    r=sensors_holm(rows)
    assert r["GPS"]["holm_p_upper"]==.02
    assert r["GPS"]["terminal"]=="exploratory_bird_specific_wind_context_extra_predictability"
    assert r["BAROMETRIC"]["holm_family_p"]==1.


def test_invalid_permutations_count_in_conservative_p_upper():
    obs={"mean_gain":.1}
    draws=[{"mean_gain":0,"eligible_birds":10},
       {"mean_gain":None,"eligible_birds":0},
       {"mean_gain":.2,"eligible_birds":11}]
    a=calibrate(obs,draws)
    assert a["p_lower"]==.5
    assert a["p_upper"]==.75
    assert a["valid"]==2


def test_shared_species_kernel_on_synthetic_copopulation():
    sessions=[];weather={}
    for bird_id in range(11):
        bird=f"B{bird_id:02d}"
        for day,state in [
            ("2019-05-11",0),("2019-05-12",0),
            ("2019-05-13",1),("2019-05-14",1),
            ("2019-05-15",0),("2019-05-16",1)
        ]:
            # Shared wind response across birds, no intrinsic slopes.
            hist=np.zeros(10,dtype=np.int64)
            hist[2 if state==0 else 7]=30
            sessions.append({"bird":bird,"day":day,"hists":{(2,6):hist}})
            weather[bird,day]=state
    p=pack_profiles(sessions,weather)
    c=build_shared_context(p)
    z=score_shared_vs_bird(p,c)
    assert z["eligible_birds"]==11
    assert z["eligible_bird_days"]==66
    assert np.isfinite(z["mean_gain"])
