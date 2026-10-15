"""Tests for original Jeong et al 2025 printed 11-camera clock table derivatives.

Actual biological evidence comes from original published camera/hour source
margins. The rank correlation and overlap decomposition are retrospective
descriptions, NOT a camera-level independent-animal significance test.
"""
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sp=importlib.util.spec_from_file_location(
    "joint",ROOT/"scripts"/"run_bukhansan_published_joint_space_clock_overlap_v3.py")
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)
PLAN=json.loads((ROOT/"BUKHANSAN_PUBLIC_JOINT_SPACE_CLOCK_OVERLAP_V3_CONTRACT.json").read_text())
SOURCE=json.loads((ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json").read_text())

def result():
    return m.compute(PLAN,SOURCE)

def test_original_11_published_camera_and_time_bin_marginal_overlap():
    o=result()
    assert o["status"]==m.STATUS
    assert o["source_totals"]=={"water_deer":184,"wild_boar":273}
    assert len(o["individual_camera_source_record_profiles_all_sites"])==11
    x=o["pooled_recorded_overlap"]
    assert abs(x["camera_space_only"]-.652114190)<1e-8
    assert abs(x["three_clock_window_time_only"]-.914397197)<1e-8
    assert abs(x["joint_camera_x_clock_window"]-.615464246)<1e-8
    assert x["joint_camera_x_clock_window"] < min(
        x["camera_space_only"],x["three_clock_window_time_only"])
    assert x["both_exact_marginalization_identities_verified"]
    assert x["attribution_is_order_dependent_and_not_causal"]

def test_spatial_first_and_clock_first_exact_decompositions_both_add():
    x=result()["pooled_recorded_overlap"]
    s=x["spatial_first_decomposition"]
    t=x["clock_first_alternative"]
    assert abs(s["spatial_marginal_TV"]-.347885810)<1e-8
    assert abs(s["ADDITIONAL_clock_given_spatial_refinement_TV"]-.036649944)<1e-8
    assert abs(s["spatial_marginal_TV"]+s["ADDITIONAL_clock_given_spatial_refinement_TV"]-
               x["joint_detected_record_distribution_total_variation"])<1e-8
    assert abs(t["clock_marginal_TV"]-.085602803)<1e-8
    assert abs(t["ADDITIONAL_spatial_given_clock_refinement_TV"]-.298932951)<1e-8
    assert abs(t["clock_marginal_TV"]+t["ADDITIONAL_spatial_given_clock_refinement_TV"]-
               x["joint_detected_record_distribution_total_variation"])<1e-8
    assert abs(s["fraction_of_joint_discrepancy_visible_already_at_camera_marginal"]-
               .904690412)<1e-8
    assert abs(s["fraction_of_joint_discrepancy_additional_after_adding_clock"]-
               .095309588)<1e-8
    sym=x["symmetric_average_over_both_refinement_orders_NOT_CAUSAL"]
    assert abs(sym["spatial_record_distribution_component_TV"]-.323409380)<1e-8
    assert abs(sym["clock_record_distribution_component_TV"]-.061126374)<1e-8
    assert abs(sym["spatial_fraction_of_joint_record_discrepancy"]-.841038517)<1e-8
    assert abs(sym["clock_fraction_of_joint_record_discrepancy"]-.158961483)<1e-8
    assert sym["different_numbers_of_site_and_clock_categories_NOT_CONTROLLED"]

def test_temporal_overlap_loss_is_mainly_G19_not_M2_and_no_individual_CI():
    o=result()
    camera=o["cameras_accounting_for_observed_additional_clock_refinement"]
    assert len(camera)==2
    assert [x["site_code"] for x in camera]==["G19","M1"]
    assert abs(camera[0]["observed_additional_overlap_loss"]-.032150820)<1e-8
    assert abs(camera[0]["share_of_total_additional_loss"]-.877240630)<1e-8
    assert abs(camera[1]["observed_additional_overlap_loss"]-.004499124)<1e-8
    assert abs(sum(x["share_of_total_additional_loss"] for x in camera)-1)<1e-8
    assert not o["valid_animal_or_independent_camera_significance_computed"]
    assert not o["true_within_camera_competition_causally_tested"]

def test_spatial_co_detection_vs_time_overlap_rank_does_not_survive_count_filter():
    x=result()["post_publication_spatial_record_balance_vs_local_clock_overlap"]
    assert [r["n_sites"] for r in x]==[7,5]
    assert abs(x[0]["record_balance_vs_local_temporal_overlap_spearman_rho_POSTHOC"]-
               .464285714)<1e-8
    assert abs(x[1]["record_balance_vs_local_temporal_overlap_spearman_rho_POSTHOC"]+
               .5)<1e-8
    assert "G12" not in x[1]["eligible_published_camera_codes"]
    assert "G21" not in x[1]["eligible_published_camera_codes"]
    assert all(not row["site_independence_or_significance_established"] for row in x)

def test_unverified_original_data_or_frozen_predata_cannot_be_promoted():
    changed=json.loads(json.dumps(PLAN))
    changed["output_guards"]["original_2022_Uljin_fixed_41_mirror_dates_evaluated"]=True
    with pytest.raises(ValueError,match="INFERENCE_PROMOTION"):
        m.compute(changed,SOURCE)
    changed=json.loads(json.dumps(PLAN))
    changed["analysis_class"]="PREREGISTERED_BEFORE_FIELD_DATA"
    with pytest.raises(ValueError,match="SOURCE_PLAN"):
        m.compute(changed,SOURCE)
    changed=json.loads(json.dumps(SOURCE))
    changed["derived_publication_site_six_hour_window_counts"][10]["water_deer"]["01to06"]+=1
    with pytest.raises(ValueError,match="SITE_HOUR_MARGINS"):
        m.compute(PLAN,changed)
