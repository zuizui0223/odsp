"""Tests of PUBLIC-AGGREGATE INTEGER INVERSION, not tests of field biology.

Synthetic HTML below only checks the source-admission parser; the separate
CI step fetches genuine public KCI article and verifies each source statistic.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "bukhansan_inverse",ROOT/"scripts"/"run_bukhansan_2025_public_integer_reconstruction_v0.py")
# Script imports the existing official KCI reference reader in the same scripts folder.
import sys
sys.path.insert(0,str(ROOT/"scripts"))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
PLAN=json.loads((ROOT/"BUKHANSAN_PUBLISHED_INTEGER_RECONSTRUCTION_V0_CONTRACT.json").read_text())

PUBLIC_ABSTRACT_MINIMAL_FIXTURE="""<html><main>
<p>10.14397/jals.2025.59.5.111</p>
The objective of this study was to investigate the daily activity patterns of
wild boar and water deer in Bukhansan National Park.
Of 2,529 photographs, 457 images were analyzed.
In forests, wild boar was observed 29.15% by day and 70.85% at night,
while water deer had 29.73% by day and 70.27% at night.
In wetlands, wild boar was 22.97% day and 77.03% night,
while water deer was 16.36% day and 83.64% night.
The study included 457 images from forests and wetlands.
</main></html>"""


def test_unique_integer_photo_table_at_declared_source_rounding_precision():
    r=m.reconstruct(PLAN,PUBLIC_ABSTRACT_MINIMAL_FIXTURE)
    assert r["status"]==m.STATUS
    assert r["number_of_all_integer_solutions_after_total_constraint"]==1
    rows={(x["taxon"],x["habitat"]):(x["CONDITIONAL_day_photos"],x["CONDITIONAL_night_photos"])
          for x in r["only_integer_solution_under_EXPLICIT_UNVERIFIED_assumptions"]}
    assert rows=={
       ("Water deer","forest"):(22,52),
       ("Wild boar","forest"):(58,141),
       ("Water deer","wetland"):(18,92),
       ("Wild boar","wetland"):(17,57),
    }
    assert sum(sum(x) for x in rows.values())==457
    assert r["group_candidate_count_if_independently_considered"]==[12,10,14,12]
    assert r["source_validation"]["all_8_day_night_published_percentages_found"]
    missing=r["assumption_sensitivity_if_unclassified_photos_are_allowed"]
    assert missing["lowest_number_of_hypothetically_nonpartitioned_photos_needed_for_alternative"]==7
    assert missing["first_alternative_four_group_photo_count_total"]==450
    assert [q["CONDITIONAL_total"] for q in missing["first_alternative_group_total_night_pairs"]]==[74,247,55,74]
    assert not missing["unclassified_photos_observed_in_real_study"]
    assert missing["the_exact_four_group_partition_is_required_for_uniqueness"]
    assert not r["original_real_event_records_obtained"]


def test_exact_photo_habitat_mix_decomposition_not_population_causality():
    r=m.reconstruct(PLAN,PUBLIC_ABSTRACT_MINIMAL_FIXTURE)
    v=r["symmetric_kitagawa_DECOMPOSITION_OF_PHOTO_MARGINS_ONLY"]
    assert abs(v["observed_pooled_species_difference_percentage_points"]-5.733397038)<1e-7
    assert abs(v["within_habitat_distribution_component_pp"]-2.541102603)<1e-7
    assert abs(v["photo_habitat_mix_component_pp"]-3.192294435)<1e-7
    assert abs(v["photo_habitat_mix_share_of_pooled_difference"]-0.556789354)<1e-7
    assert abs(v["same_50_50_habitat_standardized_difference_pp"]-3.012667761)<1e-7
    assert v["proof_components_sum_to_pooled_difference"]
    assert not v["biological_causal_partition_identified"]
    assert abs(r["taxon_photo_wetland_representation"]["Water deer"]-110/184)<1e-8
    assert abs(r["taxon_photo_wetland_representation"]["Wild boar"]-74/273)<1e-8


def test_naive_photo_independence_diagnostic_not_a_biological_p_value():
    r=m.reconstruct(PLAN,PUBLIC_ABSTRACT_MINIMAL_FIXTURE)
    x=r["purely_naive_photo_independence_DIAGNOSTIC_NOT_ECOLOGICAL_INFERENCE"]
    assert abs(x["ratio_of_species_habitat_odds_ratios"]-1.567833155)<1e-8
    assert abs(x["independent_photo_WALD_two_sided_p"]-.3503)<.001
    assert x["independent_photo_WALD_95_percent_CI"][0]<1
    assert x["independent_photo_WALD_95_percent_CI"][1]>1
    assert x["this_is_NOT_a_valid_cluster_adjusted_biological_p_value"]
    assert x["unknown_camera_identity_and_repeated_animal_exposure"]


def test_nearest_rounding_and_nonexhaustive_alternative_do_not_get_hidden():
    p=m.parse_percent_basis_points("70.27")
    assert p==7027
    opts=m.candidate_photo_counts(p,457)
    assert (74,52) in opts
    assert (37,26) in opts
    # Without the independent total-457 constraint, MULTIPLE group count
    # solutions exist: therefore the raw table is NOT identified by rates alone.
    assert len(opts)>1
    bad=json.loads(json.dumps(PLAN))
    bad["source"]["focal_analyzed_images_reported"]=458
    with pytest.raises(ValueError,match="SOURCE_ID_AND_SAMPLE"):
        m.reconstruct(bad,PUBLIC_ABSTRACT_MINIMAL_FIXTURE)


def test_modified_published_percentages_and_source_guard_fail_closed():
    changed=PUBLIC_ABSTRACT_MINIMAL_FIXTURE.replace("70.27%","70.26%")
    with pytest.raises(ValueError,match="PERCENT"):
        m.reconstruct(PLAN,changed)
    corrupted=json.loads(json.dumps(PLAN))
    corrupted["design_guards"]["independent_photo_events_verified"]=True
    with pytest.raises(ValueError,match="ECOLOGICAL_SCOPE_PROMOTION"):
        m.reconstruct(corrupted,PUBLIC_ABSTRACT_MINIMAL_FIXTURE)
    assert m.reconstruct(PLAN,None)["status"]=="HOLD_ORIGINAL_KCI_ABSTRACT_NOT_ATTESTED"
