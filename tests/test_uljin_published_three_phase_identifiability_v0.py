"""Regression with SYNTHETIC ZIP BYTES encoding published table values.

Fixture is never treated as independently authenticated empirical data.
GitHub Actions second step downloads and verifies ORIGINAL public Zenodo
Supplement 3 bytes and external publisher MD5 without monkeypatching.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import inspect_uljin_published_supp3_aggregate_v0 as source
modspec=importlib.util.spec_from_file_location(
    "phase",ROOT/"scripts"/"run_uljin_published_three_phase_identifiability_v0.py")
phase=importlib.util.module_from_spec(modspec)
modspec.loader.exec_module(phase)
SOURCE_PLAN=json.loads((ROOT/"ULJIN_PUBLISHED_SUPPL3_DAYPART_SIGNATURE_V0_CONTRACT.json").read_text())
PHASE_PLAN=json.loads((ROOT/"ULJIN_PUBLISHED_SUPPL3_PHASE_IDENTIFIABILITY_V0_CONTRACT.json").read_text())

SOURCE_COUNTS={
 "Long-tailed goral":(1325,139,853),
 "Siberian roe deer":(463,73,272),
 "Water deer":(264,51,499),
 "Wild boar":(475,37,172)
}

def fixture():
    header="Species\tdiel_period\tn\tn_total\tprop_pct\thours_total\tdetections_per_hour\tdetections_per_100h"
    rows=[header]
    for species,counts in SOURCE_COUNTS.items():
        total=sum(counts)
        for period,count in zip(phase.CATEGORIES,counts):
            hours=SOURCE_PLAN["published_period_hours"][period]
            rows.append(f"{species}\t{period}\t{count}\t{total}\t{100*count/total:.1f}\t{hours}\t{count/hours}\t{100*count/hours}")
    z=io.BytesIO()
    with zipfile.ZipFile(z,"w") as zipf:
        zipf.writestr(SOURCE_PLAN["source"]["member"],"\n".join(rows)+"\n")
    return z.getvalue()

def compute_fixture(monkeypatch):
    raw=fixture()
    monkeypatch.setattr(source,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    return phase.inspect(PHASE_PLAN,SOURCE_PLAN,raw)

def test_all_four_peak_twilight_but_no_behavioral_preference_claim(monkeypatch):
    r=compute_fixture(monkeypatch)
    assert r["status"]==phase.STATUS
    assert r["all_four_source_profiles_peak_in_civil_twilight_per_published_period_hour"]
    assert len(r["four_species_all_three_parts"])==4
    bysp={x["species"]:x for x in r["four_species_all_three_parts"]}
    assert bysp["Wild boar"]["relative_difference_of_top_to_second_rate"]<.03
    assert bysp["Siberian roe deer"]["night_to_civil_twilight_rate_ratio"]<.33
    assert not bysp["Water deer"]["population_behavior_or_species_preference_inferred"]
    assert not r["per_camera_robust_species_temporal_differentiation_identified"]
    assert not r["original_frozen_41_mirror_pairs_observed"]

def test_exact_three_part_cross_species_identity_all_six(monkeypatch):
    r=compute_fixture(monkeypatch)
    assert len(r["all_six_unordered_species_pairs"])==6
    assert all(x["three_part_identity_holds"] for x in r["all_six_unordered_species_pairs"])
    sub=r["water_deer_to_boar_three_part_ratio"]
    assert abs(sub["twilight_to_day_between_species"]-2.480036855)<1e-8
    assert abs(sub["night_to_twilight_between_species"]-2.104765162)<1e-8
    assert abs(sub["night_to_day_between_species"]-5.219895173)<1e-8
    assert abs(sub["twilight_to_day_between_species"]*sub["night_to_twilight_between_species"]-sub["night_to_day_between_species"])<1e-8

def test_detector_factor_tipping_is_conditional_not_real_q(monkeypatch):
    out=compute_fixture(monkeypatch)
    q=out["conditional_effective_detector_q_sensitivity"]
    assert abs(q["equal_latent_ratio_tipping_qmax_over_qmin_IF_common_site_exposure"]-2.284708991)<1e-8
    assert not q["q_is_observed_in_real_data"]
    assert q["site_mix_assumed_equal_in_conditional_formula"]
    scenarios={s["hypothetical_qmax_over_qmin"]:s for s in q["q_scenarios"]}
    assert scenarios[2.0]["minimum_latent_ratio_IF_common_exposure_and_q_only"]>1
    assert scenarios[2.3]["minimum_latent_ratio_IF_common_exposure_and_q_only"]<1
    assert not scenarios[2.0]["observed_q_or_exposure_claimed"]

def test_two_abstract_station_group_witness_exactly_fits_all_four_margins(monkeypatch):
    out=compute_fixture(monkeypatch)
    w=out["no_species_specific_within_stratum_phase_difference_counterexample"]
    assert w["status"]=="EXACT_EXPECTED_TWO_ABSTRACT_GROUPS_DAY_NIGHT_ONLY"
    assert w["possible_even_with_perfect_equal_camera_q"]
    assert not w["actual_two_study_areas_or_camera_station_membership_measured"]
    for row in w["species_composition_weights"]:
        A=w["group_A_identical_night_probability_for_all_species"]
        B=w["group_B_identical_night_probability_for_all_species"]
        fraction=row["HYPOTHETICAL_fraction_of_detected_events_from_A"]
        assert 0<fraction<1
        assert abs(fraction*A+(1-fraction)*B-
                   row["published_detected_night_fraction_excluding_twilight"])<1e-8

def test_try_to_relabel_source_or_frozen_predata_is_rejected(monkeypatch):
    raw=fixture()
    monkeypatch.setattr(source,"ZENODO_MD5",hashlib.md5(raw).hexdigest())
    p=json.loads(json.dumps(PHASE_PLAN))
    p["source_guards"]["original_2022_41_pairs_tested"]=True
    with pytest.raises(ValueError,match="LIMITATIONS"):
        phase.inspect(p,SOURCE_PLAN,raw)
    p=json.loads(json.dumps(PHASE_PLAN))
    p["stage"]="PRE_PUBLICATION_PREREGISTERED"
    with pytest.raises(ValueError,match="PLAN_MISMATCH"):
        phase.inspect(p,SOURCE_PLAN,raw)


def test_all_twilight_reclassification_bounds_certify_water_highest_boar_lowest(monkeypatch):
    o=compute_fixture(monkeypatch)
    b=o["adversarial_civil_twilight_as_night_source_fraction_bounds"]
    assert b["water_deer_always_greater_than_all_three_other_taxa"]
    assert b["wild_boar_always_less_than_all_three_other_taxa"]
    assert len(b["all_six_pairwise_partial_order_certificates"])==6
    data={x["species"]:x for x in b["per_taxon"]}
    assert abs(data["Water deer"]["night_share_lower_percent"]-61.302211302)<1e-7
    assert abs(data["Water deer"]["night_share_upper_percent"]-67.567567568)<1e-7
    assert abs(data["Wild boar"]["night_share_lower_percent"]-25.146198830)<1e-7
    assert abs(data["Wild boar"]["night_share_upper_percent"]-30.555555556)<1e-7
    assert abs(b["water_deer_minus_wild_boar_difference_pp_bounds"][0]-30.746655747)<1e-7
    assert abs(b["water_deer_minus_wild_boar_difference_pp_bounds"][1]-42.421368737)<1e-7
    assert not b["perfect_camera_q_or_matched_site_hours_claimed"]
    assert not b["independent_station_ecology_or_original_41_pairs_claimed"]


def test_middle_taxa_rank_not_guaranteed_under_twilight_reassignment(monkeypatch):
    o=compute_fixture(monkeypatch)
    certificates=o["adversarial_civil_twilight_as_night_source_fraction_bounds"]["all_six_pairwise_partial_order_certificates"]
    middle=next(p for p in certificates if set((p["species_a"],p["species_b"]))==
                {"Long-tailed goral","Siberian roe deer"})
    assert middle["verdict"]=="OVERLAPPING_POOLED_TWILIGHT_REALLOCATION_INTERVALS"
