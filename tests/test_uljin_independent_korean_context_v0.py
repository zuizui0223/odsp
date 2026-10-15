"""Offline fixtures test scoped abstract-verification logic only.

Real CI separately fetches BOTH KCI publisher pages plus independently
hash-authenticated Zenodo Supplement 3. Fixtures do not establish biology.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location(
    "cross_korean_context",ROOT/"scripts"/"run_uljin_independent_korean_context_v0.py")
route=importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)
PLAN=json.loads((ROOT/"ULJIN_INDEPENDENT_KOREAN_UNGULATE_CONTEXT_V0_CONTRACT.json").read_text())

HAN="""<html><main>
<p>10.13087/kosert.2024.27.2.55</p>
This study aimed to figure out diel activity patterns of water deer and wild boar.
18 camera traps were used January 2021 to November 2022; dawn, day, dusk, and night.
Both species showed changes in fall and winter.
Water deer 61.9% night and wild boar 77.6% night in fall,
wild boar 78.0% in winter. Trail-near and far rates 12.1%, 24.6%, 3.4%, 5.7%.
</main></html>"""

JEONG="""<html><main><p>10.14397/jals.2025.59.5.111</p>
The objective of this study was to investigate the daily activity patterns
of Bukhansan National Park water deer and wild boar.
457 images in forests and wetlands. Forest water deer 70.27% night and wild boar 70.85%.
Wetland water deer 83.64% night and wild boar 77.03%.
</main></html>"""

PROFILE=[
 ("Long-tailed goral",1325,139,853),
 ("Siberian roe deer",463,73,272),
 ("Water deer",264,51,499),
 ("Wild boar",475,37,172),
]

def sample_source():
    return {"status":"REPRODUCED_PUBLISHED_DAYPART_POOLED_DESCRIPTIVE_SIGNATURE_ONLY",
      "reproduced_total_events":4623,
      "original_hourly_camera_operation_verified":False,
      "species_profiles":[
        {"species":s,"period_counts":{"daytime":d,"crepuscular":t,"nighttime":n}}
        for s,d,t,n in PROFILE]}


def test_identifies_nonuniversal_species_ordering_without_cross_study_p():
    out=route.compare(PLAN,sample_source(),HAN,JEONG)
    assert out["status"]==route.STATUS
    assert len(out["within_study_season_and_habitat_night_percent_contexts"])==4
    a=out["within_study_season_and_habitat_night_percent_contexts"]
    assert abs(a[0]["water_minus_boar_percentage_points"]-36.156012)<2e-6
    assert a[1]["water_minus_boar_percentage_points"]==-15.7
    assert a[2]["water_minus_boar_percentage_points"]==-0.58
    assert a[3]["water_minus_boar_percentage_points"]==6.61
    assert out["reported_night_share_ordering_not_universal_across_contexts"]
    assert out["han_suburban_wild_boar_winter_night_percent"]==78.
    habitat=out["bukhansan_within_study_forest_vs_wetland_night_share_pp"]
    assert habitat["water_deer_wetland_minus_forest"]==13.37
    assert habitat["wild_boar_wetland_minus_forest"]==6.18
    assert habitat["difference_of_reported_differences"]==7.19
    assert not habitat["statistical_significance_claimed"]
    trail=out["han_within_study_day_share_near_far_trail_pp"]
    assert trail["water_deer_far_minus_near"]==12.5
    assert trail["wild_boar_far_minus_near"]==2.3
    assert not trail["human_avoidance_causally_proven"]
    assert not out["cross_study_night_zone_definition_harmonized"]
    assert not out["between_study_difference_significance_claimed"]
    assert not out["landscape_causal_effect_estimated"]
    assert not out["original_2022_41_mirror_pairs_evaluated"]


def test_publication_date_or_location_cannot_be_swapped_for_source():
    with pytest.raises(ValueError,match="DOI_ABSENT"):
        route.verify_abstract(JEONG,PLAN["sources"]["suburban_2024"],"suburban_2024")
    with pytest.raises(ValueError,match="ABSTRACT_MISSING"):
        route.verify_abstract("<html>10.13087/kosert.2024.27.2.55</html>",
                              PLAN["sources"]["suburban_2024"],"suburban_2024")


def test_raw_expected_claims_invalidated_when_public_percent_missing():
    bad=HAN.replace("77.6%","76.7%")
    with pytest.raises(ValueError,match="PERCENT_NOT_IN_ABSTRACT"):
        route.compare(PLAN,sample_source(),bad,JEONG)


def test_guard_cannot_promote_field_claim_or_frozen_original_date_analysis():
    changed=json.loads(json.dumps(PLAN))
    changed["integrity_guards"]["camera_hour_effort_matched"]=True
    with pytest.raises(ValueError,match="INFERENCE_BOUNDARY"):
        route.compare(changed,sample_source(),HAN,JEONG)
    changed=json.loads(json.dumps(PLAN))
    changed["analysis_stage"]="BEFORE_PUBLICATION_PREREGISTERED"
    with pytest.raises(ValueError,match="INFERENCE_BOUNDARY"):
        route.compare(changed,sample_source(),HAN,JEONG)


def test_missing_source_original_is_not_allowed():
    u=sample_source()
    u["original_hourly_camera_operation_verified"]=True
    with pytest.raises(ValueError,match="ULJIN_ORIGINAL_SOURCE_NOT_ALLOWED"):
        route.compare(PLAN,u,HAN,JEONG)
