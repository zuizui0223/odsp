"""Exact target-specific information budgets under fixed released margins."""
from pathlib import Path
import json
import numpy as np
import pytest
from odsp.uljin_threeway_margin_identifiability_v0 import WORLD_A,WORLD_B
from odsp.uljin_minimal_threeway_measurement_v0 import (
    enumerate_original_fiber,evaluate_all_minimal_measurements
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_MINIMAL_THREEWAY_MEASUREMENT_V0_CONTRACT.json").read_text())
PARENT=json.loads((ROOT/"ULJIN_THREEWAY_MARGIN_FIBER_BOUNDS_V1_FIRST_RESULT_LEDGER.json").read_text())


def _row(results,selected):
    return next(r for r in results["every_frozen_candidate_subset"]
                if r["additional_early_rising_phase_bins"]==selected)


def test_original_full_parent_integer_fiber_replayed():
    worlds=enumerate_original_fiber()
    assert len(worlds)==2723
    assert len({v for v,ratio,sign in worlds})==2723
    assert tuple(map(int,WORLD_A[0,0])) in {v for v,_,_ in worlds}
    assert tuple(map(int,WORLD_B[0,0])) in {v for v,_,_ in worlds}
    assert set(s for _,_,s in worlds)=={-1,0,1}


def test_all_64_release_subsets_and_three_different_information_budgets():
    out=evaluate_all_minimal_measurements(PLAN,PARENT)
    assert out["exhaustive_subset_count"]==64
    assert len(out["every_frozen_candidate_subset"])==64
    assert out["minimum_number_of_additional_cell_counts_to_identify_any_fiber_world"]=={
        "sign":2,"exact_odds_ratio":2,"full_table":5
    }
    assert out["parent_complete_positive_integer_tables"]==2723
    assert not out["no_ecological_data_read"] is False
    assert not out["no_qualified_ODSP_route_change"] is False
    none=_row(out,[])
    assert none["augmented_linear_margin_rank"]==19
    assert none["feasible_tables_in_sign_ambiguous_classes"]==2723
    measured=_row(out,[0,5])
    assert measured["sign_universally_identified"]
    assert measured["odds_ratio_universally_identified"]
    assert not measured["complete_table_universally_identified"]
    assert measured["augmented_linear_margin_rank"]==21
    for selected in ([0,1,2,3,4],[1,2,3,4,5]):
        q=_row(out,selected)
        assert q["augmented_linear_margin_rank"]==24
        assert q["complete_table_universally_identified"]


def test_night_single_cell_is_optimal_for_deterministic_sign_coverage():
    out=evaluate_all_minimal_measurements(PLAN,PARENT)
    one=out["single_cell_designs"]
    assert len(one)==6
    night=_row(out,[5])
    assert night["sign_ambiguous_single_cell_observations"]==[[6]]
    assert night["feasible_tables_in_sign_ambiguous_classes"]==126
    assert all(not x["sign_universally_identified"] for x in one)
    assert all(x["feasible_tables_in_sign_ambiguous_classes"]>=126 for x in one)
    # Combinatorial coverage is NOT a prior probability or expected power.
    assert not out["number_of_possible_completions_not_a_probability_distribution"] is False


def test_original_world_specific_releases_and_no_false_certainty():
    out=evaluate_all_minimal_measurements(PLAN,PARENT)
    A=out["original_world_A_release_diagnostics"]
    B=out["original_world_B_release_diagnostics"]
    assert A["bins_5"]["released_counts"]==[6]
    assert set(A["bins_5"]["possible_signs"])=={-1,0,1}
    assert B["bins_5"]["released_counts"]==[3]
    assert B["bins_5"]["possible_signs"]==[-1]
    for world in (A,B):
        assert world["bins_0_5"]["remaining_odds_ratio_values"]==1
        assert len(world["bins_0_5"]["possible_signs"])==1


def test_deterministic_and_fail_closed_for_changed_parent_or_design():
    first=evaluate_all_minimal_measurements(PLAN,PARENT)
    assert first==evaluate_all_minimal_measurements(PLAN,PARENT)
    altered=json.loads(json.dumps(PLAN))
    altered["strict_assumptions"]["positive_integer_cells_at_least"]=0
    with pytest.raises(ValueError,match="frozen"):
        evaluate_all_minimal_measurements(altered,PARENT)
    broken=json.loads(json.dumps(PARENT))
    broken["frozen_positive_integer_complete_table_count"]=2722
    with pytest.raises(ValueError,match="frozen"):
        evaluate_all_minimal_measurements(PLAN,broken)
    json.dumps(first,allow_nan=False)
