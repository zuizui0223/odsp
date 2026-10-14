"""Source-verified descriptive 11-camera ecological influence diagnostics.

No event-level p-values, ecological significance, verified q, original 41
calendar pair or real physical camera on-time are permitted.
"""
import importlib.util
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location(
  "camera_influence",ROOT/"scripts"/"run_bukhansan_published_camera_site_influence_v2.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
PLAN=json.loads((ROOT/"BUKHANSAN_PUBLISHED_CAMERA_SITE_INFLUENCE_V2_CONTRACT.json").read_text())
SOURCE=json.loads((ROOT/"BUKHANSAN_PUBLISHED_SITE_HOUR_WINDOWS_V1_CONTRACT.json").read_text())

def result():
    return m.analyze(PLAN,SOURCE)

def test_authentic_11_station_counts_and_unequal_record_concentration():
    r=result()
    spatial=r["observational_site_detection_spatial_pattern"]
    assert r["status"]==m.STATUS
    assert spatial["source_photos_by_species"]=={"water_deer":184,"wild_boar":273}
    assert spatial["public_camera_codes_with_positive_record"]=={"water_deer":7,"wild_boar":11}
    effective=spatial["inverse_Herfindahl_effective_camera_count_of_detected_records"]
    assert abs(effective["water_deer"]-3.034235526)<1e-8
    assert abs(effective["wild_boar"]-7.438766344)<1e-8
    assert abs(spatial["Schoener_site_record_distribution_overlap_not_latent_occupancy"]-.65211419)<1e-8
    assert spatial["M2_record_share_by_species"]=={"water_deer":.5,"wild_boar":round(49/273,9)}
    assert spatial["does_not_estimate_animal_abundance_occupancy_or_independent_replicates"]

def test_every_published_camera_omission_keeps_MH_recorded_effect_direction():
    r=result()
    loo=r["all_11_leave_one_published_camera_out"]
    assert [x["omitted_camera_code"] for x in loo]==list(m.SITES)
    assert r["MH_OR_direction_above_one_after_every_single_camera_omission"]
    assert abs(r["MH_OR_all_informative_published_cameras"]-1.615826474)<1e-8
    assert abs(r["MH_OR_leave_one_station_out_min_max"][0]-1.331580447)<1e-8
    assert abs(r["MH_OR_leave_one_station_out_min_max"][1]-1.725022039)<1e-8
    assert sum(x["camera_positive_both_species_in_original_table"] for x in loo)==7
    assert all(not x["population_biological_significance_tested"] for x in loo)

def test_common_station_photo_weight_and_equal_site_estimands_not_identical():
    r=result()
    shared=r["source_positive_both_species_clock_comparison"]
    assert shared["number_of_source_positive_both_species_camera_codes"]==7
    assert abs(shared["detected_late_fraction_species_difference_pp"]-8.414390406)<1e-7
    assert abs(shared["equal_camera_weight_mean_species_difference_pp"]-6.288660048)<1e-7
    assert abs(shared["noncausal_symmetrical_within_site_component_pp"]-10.220464754)<1e-7
    assert abs(shared["noncausal_symmetrical_camera_weight_component_pp"]+1.806074348)<1e-7
    assert abs(sum([shared["noncausal_symmetrical_within_site_component_pp"],
                    shared["noncausal_symmetrical_camera_weight_component_pp"]])-
               shared["detected_late_fraction_species_difference_pp"])<1e-8
    assert shared["total_water_photos_used"]==158
    assert shared["total_boar_photos_used"]==190
    assert not shared["site_exposure_or_detector_q_adjusted"]

def test_leave_one_camera_diagnostics_identify_one_site_dependence_without_erasing_sign():
    r=result()
    subs={x["omitted_camera_code"]:x for x in r["all_11_leave_one_published_camera_out"]}
    assert abs(subs["M2"]["Mantel_Haenszel_source_count_OR_not_causal"]-1.331580447)<1e-8
    assert abs(subs["M1"]["Mantel_Haenszel_source_count_OR_not_causal"]-1.725022039)<1e-8
    assert abs(subs["M2"]["late_fraction_difference_pp_given_source_positive_cameras"]-6.613386613)<1e-8
    assert abs(subs["G21"]["equal_source_camera_weight_mean_difference_pp"]-.193912913)<1e-8
    assert abs(subs["G12"]["equal_source_camera_weight_mean_difference_pp"]-14.479627199)<1e-8
    assert abs(r["source_shared_roster_late_share_difference_pp_LOO_range"][0]-6.613386613)<1e-8
    assert abs(r["source_shared_roster_late_share_difference_pp_LOO_range"][1]-9.432842905)<1e-8
    assert abs(r["equal_shared_camera_mean_difference_pp_LOO_range"][0]-.193912913)<1e-8
    assert abs(r["equal_shared_camera_mean_difference_pp_LOO_range"][1]-14.479627199)<1e-8
    influence=r["M2_omission_sensitivity"]
    assert abs(influence["M2_fraction_of_aggregate_CMH_score_deviation"]-.642068242)<1e-7
    assert abs(influence["conditional_event_independence_p_unvalidated_all"]-.046616409)<1e-8
    assert abs(influence["conditional_event_independence_p_unvalidated_without_M2"]-.356179423)<1e-8
    assert not influence["population_significance_or_animal_independence_claimed"]

def test_wrong_source_margins_fail_before_ecological_output():
    changed=json.loads(json.dumps(SOURCE))
    changed["derived_publication_site_six_hour_window_counts"][10]["water_deer"]["01to06"]+=1
    with pytest.raises(ValueError,match="SOURCE_SITE_HOUR_MARGINS"):
        result_changed=m.analyze(PLAN,changed)
    assert "result_changed" not in locals()

def test_cannot_relabel_nonindependent_record_contrast_as_real_animal_effect():
    changed=json.loads(json.dumps(PLAN))
    changed["negative_controls"]["Uljin_41_photoperiod_matched_pairs_tested"]=True
    with pytest.raises(ValueError,match="INFERENCE_CLAIM_PROMOTED"):
        m.analyze(changed,SOURCE)
    changed=json.loads(json.dumps(PLAN))
    changed["analysis_stage"]="PREREGISTERED_BEFORE_FIELD_DATA"
    with pytest.raises(ValueError,match="PLAN_CHANGED"):
        m.analyze(changed,SOURCE)
    r=result()
    assert r["clock_bins_01to06_and_19to24_not_date_solar_phase"]
    assert not r["site_clustering_community_population_or_occupancy_significance_claimed"]
    assert not r["original_uljin_2022_41_fixed_date_pairs_processed"]
