"""Synthetic post-outcome diagnostic: common Wstar shifts versus bird-specific changes."""
import numpy as np
from prospective.gyps_thermal_height_kernel import pack_profiles,permute_day_states
from prospective.gyps_species_shared_wstar_kernel import (
    build_shared_context,score_shared_vs_bird
)


def fake_profiles(n=12,idiosyncratic=False):
    p=[];labels={}
    days=[("2018-05-11",0),("2018-05-12",0),
          ("2018-05-13",1),("2018-05-14",1),
          ("2018-05-15",0),("2018-05-16",1)]
    for i in range(n):
        bird=f"b{i:02d}"
        for day,state in days:
            vertical_state=(1-state) if idiosyncratic and i%2 else state
            hist=np.zeros(10,np.int64)
            hist[2 if vertical_state==0 else 7]=60
            p.append({"bird":bird,"day":day,"hists":{(100,200):hist}})
            labels[bird,day]=state
    return p,labels


def test_12_birds_share_same_thermal_shift_no_strong_unique_reaction_gain():
    profiles,labels=fake_profiles()
    pack=pack_profiles(profiles,labels)
    ctx=build_shared_context(pack)
    z=score_shared_vs_bird(pack,ctx)
    assert z["eligible_birds"]==12
    assert z["eligible_bird_days"]==72
    assert z["scored_fixes"]==72*60
    assert abs(z["mean_gain"])<0.10


def test_bird_specific_opposite_responses_exceed_one_shared_species_shift():
    profiles,labels=fake_profiles(idiosyncratic=True)
    pack=pack_profiles(profiles,labels)
    z=score_shared_vs_bird(pack,build_shared_context(pack))
    assert z["eligible_birds"]==12
    assert z["mean_gain"]>0.15
    assert len(z["per_bird"])==12


def test_null_permutations_preserve_each_bird_year_month_regime_counts():
    profiles,labels=fake_profiles()
    pack=pack_profiles(profiles,labels)
    changed=permute_day_states(pack,np.random.default_rng(20261021))
    assert any(changed!=pack["labels"])
    for grp in pack["groups"]:
        assert sorted(changed[grp])==sorted(pack["labels"][grp])


def test_single_bird_cannot_define_a_population_wstar_response():
    profiles,labels=fake_profiles(1)
    pack=pack_profiles(profiles,labels)
    z=score_shared_vs_bird(pack,build_shared_context(pack))
    assert z["eligible_birds"]==0
    assert z["mean_gain"] is None


def test_context_reference_requires_two_other_individuals():
    profiles,labels=fake_profiles(2)
    p=pack_profiles(profiles,labels)
    z=score_shared_vs_bird(p,build_shared_context(p))
    assert z["eligible_birds"]==0
    assert z["scored_fixes"]==0


def test_unequal_animal_tracking_effort_not_raw_GPS_weighted():
    profiles,labels=fake_profiles()
    for p in profiles:
        if p["bird"]=="b01": p["hists"][(100,200)]*=3
    pack=pack_profiles(profiles,labels)
    z=score_shared_vs_bird(pack,build_shared_context(pack))
    assert z["eligible_birds"]==12
    assert z["eligible_bird_days"]==72
    assert z["scored_fixes"]==72*60 + 6*120
