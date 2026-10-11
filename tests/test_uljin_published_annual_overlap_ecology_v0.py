"""Ecology: published year-long overlaps cannot certify matched-calendar effects.

The published six pairwise clock-time Delta4 estimates are genuine
Jeon & Lim (2026) whole-period results, NOT original 41 daylength
mirror-pair estimates and not newly independent evidence.
"""
import json
from itertools import combinations
from pathlib import Path

from odsp.uljin_ecological_temporal_refuge_v0 import (
    TAXA,assert_frozen_ecology
)

ROOT=Path(__file__).resolve().parents[1]
PUBLISHED=json.loads((ROOT/
    "ULJIN_PUBLISHED_ANNUAL_VS_MATCHED_DAYLENGTH_SPECIES_REASSEMBLY_V0.json").read_text())
BIO=json.loads((ROOT/
    "ULJIN_FOUR_UNGULATE_TEMPORAL_REFUGE_ECOLOGY_V0_CONTRACT.json").read_text())
CAL=json.loads((ROOT/
    "ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json").read_text())


def test_all_six_original_published_pairwise_annual_results_retained():
    source=PUBLISHED["annual_pooled_civil_KDE_fixed_data_from_paper"]
    assert source["not_observed_matched_pair_result"] is True
    assert source["n_physical_stations"]==82
    assert sum(source["counts"].values())==4623
    assert set(source["counts"])==set(TAXA)
    results=source["all_six_species_pairs"]
    assert len(results)==6
    assert {frozenset(x["pair"]) for x in results}=={
        frozenset(x) for x in combinations(TAXA,2)
    }
    assert all(x["ci95"][0] < x["delta"] < x["ci95"][1]
               for x in results)
    extrema={tuple(x["pair"]):x["delta"] for x in results}
    assert extrema["Goral","Roe deer"]==.840
    assert extrema["Water deer","Wild boar"]==.653
    assert extrema["Goral","Roe deer"]-extrema[
        "Water deer","Wild boar"]==round(.840-.653,3) or abs(
        extrema["Goral","Roe deer"]-extrema[
            "Water deer","Wild boar"]-(.840-.653))<1e-12


def test_original_pair_calendar_is_early_to_midsummer_not_fall():
    dates=assert_frozen_ecology(BIO,CAL)
    assert len(dates)==82
    assert sum(b=="rising" for b in dates.values())==41
    assert sum(b=="falling" for b in dates.values())==41
    assert PUBLISHED["new_ecological_question"].startswith(
        "Is annual pooled high temporal overlap hiding")
    assert PUBLISHED["no_overlap_delta_comparison_using_annual_bootstrap_ci_as_new_seasonal_pvalue"]
    assert PUBLISHED["not_identification_of_causal_competition_or_predation_or_temperature"]
    assert PUBLISHED["actual_original_zip_events_hourly_operation_unopened"]


def test_each_competing_species_ecology_prediction_has_a_real_falsifier():
    hypotheses=PUBLISHED["fixed_new_ecological_predictions"]
    assert [x["id"] for x in hypotheses]==[
        "E0_common_temporal_shift",
        "E1_divergent_refuge_allocation",
        "E2_pooled_overlap_masks_seasonal_reassembly"
    ]
    assert all(x["prediction"] and x["falsifier"] for x in hypotheses)
    assert PUBLISHED["all_fixed_species_pairs_carried_from_published_table"]
    assert PUBLISHED["no_scanning_to_pick_extreme_41_pair_results"]
