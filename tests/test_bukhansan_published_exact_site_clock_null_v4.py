"""Exact record-label null checks using true author-published 11-camera margins.

Synthetic tiny contingency tables below test enumeration independently.
All biological outputs are only source-published PHOTO-COUNT conditional
diagnostics; animal exchangeability, camera q and source on-time unverified.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location(
    "conditional_null",ROOT/"scripts"/"run_bukhansan_published_exact_site_clock_null_v4.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
PLAN=json.loads((ROOT/"BUKHANSAN_PUBLISHED_SITE_CONDITIONAL_CLOCK_NULL_V4_CONTRACT.json").read_text())
SOURCE=json.loads((ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json").read_text())
V3=json.loads((ROOT/"BUKHANSAN_PUBLIC_JOINT_SPACE_CLOCK_OVERLAP_V3_CONTRACT.json").read_text())


def result():
    return m.analyze(PLAN,SOURCE,V3)


def test_tiny_exact_multivariate_hypergeometric_masses_are_not_uniform_over_tables():
    # Two Water labels and one Boar label across bins holding counts (2,1,0):
    # W=(2,0,0): weight 1, score 0
    # W=(1,1,0): weight 2, score 1 (Nboar=1, Nwater=2)
    den,states=m.enumerate_camera_null((2,1,0),2,2,1)
    assert den==3
    assert states=={0:1,1:2}
    assert sum(states.values())==den
    assert m.score_integer((1,1,0),(2,1,0),2,1)==1
    with pytest.raises(ValueError,match="INVALID_PUBLISHED_SITE_CONDITIONING"):
        m.enumerate_camera_null((1,1,0),3,2,1)


def test_two_site_exact_convolution_matches_independent_integer_expansion():
    a=m.enumerate_camera_null((2,1,0),2,3,2)
    b=m.enumerate_camera_null((1,1,0),1,3,2)
    denom,pmf=m.convolve_exact([("a",*a),("b",*b)],50000)
    expected={}
    for sa,wa in a[1].items():
        for sb,wb in b[1].items():
            expected[sa+sb]=expected.get(sa+sb,0)+wa*wb
    assert denom==a[0]*b[0]
    assert pmf==expected
    assert sum(pmf.values())==denom


def test_authentic_full_exact_conditional_reference_result_and_source_support():
    o=result()
    assert o["status"]==m.STATUS
    assert o["source_record_totals"]=={"water_deer":184,"wild_boar":273}
    assert len(o["all_11_source_camera_station_roster_retained"])==11
    x=o["exact_integer_conditional_null"]
    assert x["source_fixed_site_and_clock_margins_preserved"] if "source_fixed_site_and_clock_margins_preserved" in x else o["source_fixed_site_and_clock_margins_preserved"]
    assert x["original_observed_integer_overlap_score"]==30916
    assert x["total_integer_supported_global_scores"]==9922
    assert abs(x["observed_site_only_overlap"]-.652114190)<1e-8
    assert abs(x["observed_joint_site_clock_overlap"]-.615464246)<1e-8
    assert abs(x["observed_additional_clock_discrepancy"]-.036649944)<1e-8
    assert abs(x["EXACT_null_expected_additional_clock_discrepancy"]-.041139977)<1e-8
    assert abs(x["observed_minus_null_mean_additional_discrepancy"]+ .004490032)<1e-8
    assert abs(x["EXACT_one_sided_P_null_gap_at_least_observed_NOT_BIOLOGICAL_P"]-.569788726301)<1e-9
    assert len(x["exact_integer_conditional_tail_numerator"])>=90
    assert len(x["exact_integer_conditional_probability_denominator"])>=90
    assert not x["independently_replicated_biological_effect_significance_established"]


def test_exact_discrete_interval_contains_observed_and_null_mean():
    x=result()["exact_integer_conditional_null"]
    q=x["EXACT_null_conditional_gap_quantiles_2p5_50_97p5"]
    assert len(q)==3
    assert abs(q[0]-.011825131)<1e-8
    assert abs(q[1]-.039357382)<1e-8
    assert abs(q[2]-.079411530)<1e-8
    assert q[0] < x["observed_additional_clock_discrepancy"] < q[2]
    assert x["EXACT_null_expected_additional_clock_discrepancy"] > x["observed_additional_clock_discrepancy"]


def test_g19_big_descriptive_contribution_not_significant_under_its_own_null():
    o=result()
    site=o["source_selected_G19_exploratory_local_null"]
    assert site["observed_additional_gap"]==pytest.approx(.032150820,abs=1e-8)
    assert site["exact_expected_gap"]==pytest.approx(.01629155,abs=1e-8)
    assert site["POSTHOC_local_one_sided_tail_NOT_MULTIPLICITY_ADJUSTED"]==pytest.approx(.12537237,abs=1e-8)
    assert site["source_site_selected_after_outcomes"]
    assert not site["population_avoidance_effect_identified"]
    x=o["original_11_published_camera_local_conditional_nulls"]
    assert len(x)==11
    assert [s["public_camera_code"] for s in x]==list(m.SITES)
    assert all(not s["population_site_hypothesis_confirmed"] for s in x)


def test_original_published_source_and_animal_inference_hold_cannot_be_bypassed():
    changed=json.loads(json.dumps(PLAN))
    changed["source_holds"]["individual_event_permutation_null_biologically_validated"]=True
    with pytest.raises(ValueError,match="WILDLIFE_SIGNIFICANCE"):
        m.analyze(changed,SOURCE,V3)
    changed=json.loads(json.dumps(PLAN))
    changed["stage"]="PREREGISTERED_BEFORE_PUBLISHED_DATA"
    with pytest.raises(ValueError,match="CONTRACT_CHANGED"):
        m.analyze(changed,SOURCE,V3)
    changed=json.loads(json.dumps(SOURCE))
    changed["derived_publication_site_six_hour_window_counts"][10]["wild_boar"]["01to06"]+=1
    with pytest.raises(ValueError,match="SITE_HOUR_MARGINS"):
        m.analyze(PLAN,changed,V3)
    o=result()
    assert not o["source_photo_record_independence_verified"]
    assert not o["source_physical_camera_operation_hours_verified"]
    assert not o["real_2022_Uljin_fixed_41_date_pairs_tested"]
    assert not o["ecological_temporal_partition_confirmed"]
