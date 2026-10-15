"""Source-backed Bukhansan v5 habitat-heterogeneity tests.

All comparisons are photograph/animal RECORD allocations from Jeong et al.
(2025) author's public camera×hour count tables (reduced to 3 windows).
No independent camera/animal inference or habitat-selection causality.
"""
from __future__ import annotations
import importlib.util
import json
import math
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sp=importlib.util.spec_from_file_location(
    "wetland_camera_v5",ROOT/"scripts"/"run_bukhansan_published_wetland_camera_heterogeneity_v5.py")
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)
PLAN=json.loads((ROOT/"BUKHANSAN_PUBLISHED_WETLAND_CAMERA_HETEROGENEITY_V5_CONTRACT.json").read_text())
SOURCE=json.loads((ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json").read_text())


def calc():
    return m.compute(PLAN,SOURCE)


def test_original_author_wetland_counts_and_two_site_differential_identity():
    result=calc()
    assert result["status"]==m.STATUS
    assert result["forest_source_counts"]=={"water_deer":74,"wild_boar":199}
    assert result["two_wetland_source_counts"]=={"water_deer":110,"wild_boar":74}
    x=result["wetland_source_photo_record_composition"]
    assert x["water_minus_boar_wetland_record_share_pp"]==pytest.approx(32.676381589,abs=1e-8)
    assert x["whole_network_species_record_wetland_vs_forest_OR"]==pytest.approx(3.997443389,abs=1e-8)
    assert len(x["within_camera_original_record_contributions"])==2
    bysite={r["source_wetland_camera"]:r for r in x["within_camera_original_record_contributions"]}
    assert (bysite["M1"]["water_deer_record_count"],bysite["M1"]["boar_record_count"])==(18,25)
    assert (bysite["M2"]["water_deer_record_count"],bysite["M2"]["boar_record_count"])==(92,49)
    assert bysite["M1"]["source_record_fraction_differential_contribution_pp"]==pytest.approx(.625099538,abs=1e-8)
    assert bysite["M2"]["source_record_fraction_differential_contribution_pp"]==pytest.approx(32.051282051,abs=1e-8)
    assert x["M2_fraction_of_observed_wetland_share_differential"]==pytest.approx(.980869989,abs=1e-8)
    assert x["zero_causal_habitat_preference_claim"]


def test_drop_each_wetland_camera_recomputes_species_denominators_and_does_not_fake_replication():
    result=calc()
    cases={r["omitted_wetland_camera"]:r for r in
           result["both_single_wetland_camera_omission_studies_RECOMPUTE_DENOMINATORS"]}
    assert len(cases)==2
    a=cases["M2"]
    assert a["remaining_wetland_camera"]=="M1"
    assert (a["remaining_water_total_across_retained_cameras"],
            a["remaining_boar_total_across_retained_cameras"])==(92,224)
    assert a["RECOMPUTED_wetland_record_share_species_difference_pp"]==pytest.approx(
        8.404503106,abs=1e-8)
    assert a["RECOMPUTED_source_record_wetland_vs_forest_OR"]==pytest.approx(1.936216216,abs=1e-8)
    b=cases["M1"]
    assert b["remaining_wetland_camera"]=="M2"
    assert (b["remaining_water_total_across_retained_cameras"],
            b["remaining_boar_total_across_retained_cameras"])==(166,248)
    assert b["RECOMPUTED_wetland_record_share_species_difference_pp"]==pytest.approx(
        35.663622231,abs=1e-8)
    assert b["RECOMPUTED_source_record_wetland_vs_forest_OR"]==pytest.approx(5.049089906,abs=1e-8)
    assert all(not x["independent_ecological_habitat_replication_claimed"]
               for x in cases.values())


def test_all_exact_55_hypothetical_pair_ranks_are_descriptive_not_habitat_permutation_p():
    r=calc()["all_55_two_camera_set_descriptive_rank"]
    assert r["number_of_possible_source_two_camera_sets"]==55
    assert r["actual_source_wetland_pair_ranking_descending"]==2
    assert r["actual_pair_number_of_sets_equal_or_more_extreme"]==2
    assert r["actual_pair_upper_fraction_among_all_55_source_camera_pair_scores"]==pytest.approx(2/55,abs=1e-9)
    assert r["highest_record_contrast_pair_in_original_camera_network"]==["G19","M2"]
    assert r["highest_pair_record_contrast_pp"]==pytest.approx(34.163481446,abs=1e-8)
    assert not r["actual_habitat_labels_randomly_assigned"]
    assert r["source_site_pair_ranking_is_NOT_a_valid_independent_habitat_p_value"]


def test_exact_combinatorial_record_label_reference_and_true_independence_HOLD():
    tiny=m.hypergeom_upper_tail(population=5,category_total=2,draws=2,observed_category_draws=2)
    assert tiny["exact_FORMAL_record_label_one_sided_P_at_least_observed_NOT_ECOLOGICAL_P"]==pytest.approx(.1,abs=1e-15)
    x=calc()["formal_photo_count_label_exchangeability_benchmarks_NOT_POPULATION_P"]
    wet=x["forest_vs_both_wetlands"]
    m2=x["M2_vs_other_ten_camera_codes"]
    assert wet["exact_FORMAL_record_label_one_sided_P_at_least_observed_NOT_ECOLOGICAL_P"]==pytest.approx(
        2.4985892056581e-12,rel=1e-10)
    assert m2["exact_FORMAL_record_label_one_sided_P_at_least_observed_NOT_ECOLOGICAL_P"]==pytest.approx(
        4.08155536557827e-13,rel=1e-10)
    assert len(wet["exact_photo_probability_denominator"])>110
    assert not x["actual_photo_and_animal_independence_verified"]
    assert not wet["actual_independent_animal_replicates_or_randomized_habitat_assumed_proven"]


def test_source_row_corruption_fails_before_ecology_and_original_41_route_immutable():
    source=json.loads(json.dumps(SOURCE))
    source["derived_publication_site_six_hour_window_counts"][10]["water_deer"]["19to24"]+=1
    with pytest.raises(ValueError,match="SITE_HOUR_MARGINS"):
        m.compute(PLAN,source)
    changed=json.loads(json.dumps(PLAN))
    changed["negative_controls"]["no_original_Uljin_2022_frozen_41_date_pairs_tested"]=True
    with pytest.raises(ValueError,match="SIGNIFICANCE_PROMOTION"):
        m.compute(changed,SOURCE)
    changed=json.loads(json.dumps(PLAN))
    changed["analysis_stage"]="PREPUBLICATION_PREREGISTERED"
    with pytest.raises(ValueError,match="SOURCE_PLAN_CHANGED"):
        m.compute(changed,SOURCE)
    result=calc()
    assert not result["original_frozen_Uljin_2022_41_daylength_pairs_tested"]
    assert not result["causal_wetland_vs_forest_habitat_mechanism_proved"]
