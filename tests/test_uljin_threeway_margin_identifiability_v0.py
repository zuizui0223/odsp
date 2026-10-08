"""Exact positive-integer identifiability counterexample, no source data."""
import json
from pathlib import Path
import math

import numpy as np
import pytest

from odsp.uljin_threeway_margin_identifiability_v0 import (
    WORLD_A,WORLD_B,DELTA,
    construct_marginal_identifiability_witness,
    marginalization_matrix,two_way_margins,
    poisson_independent_cells_KL,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/"ULJIN_THREEWAY_MARGIN_IDENTIFIABILITY_V0_CONTRACT.json").read_text())


def test_exact_all_three_two_way_margins_and_positive_integer_complete_tables():
    assert WORLD_A.shape==WORLD_B.shape==(2,2,6)
    assert np.all(WORLD_A>0) and np.all(WORLD_B>0)
    assert np.issubdtype(WORLD_A.dtype,np.integer)
    assert np.array_equal(WORLD_B,WORLD_A+DELTA)
    assert not np.array_equal(WORLD_A,WORLD_B)
    ma,mb=two_way_margins(WORLD_A),two_way_margins(WORLD_B)
    assert set(ma)=={"site_branch","site_phase","branch_phase"}
    for name in ma:
        assert np.array_equal(ma[name],mb[name])
    assert WORLD_A.sum()==WORLD_B.sum()


def test_within_site_truth_differs_even_when_all_margins_identical():
    # A: falling/rising season multiplier exactly 3 for E, 1/3 for L.
    assert np.array_equal(WORLD_A[0,1]*WORLD_A[0,0,0],
                          WORLD_A[0,0]*WORLD_A[0,1,0])
    assert np.array_equal(WORLD_A[1,1]*WORLD_A[1,0,0],
                          WORLD_A[1,0]*WORLD_A[1,1,0])
    assert not np.array_equal(WORLD_B[0,1]*WORLD_B[0,0,0],
                              WORLD_B[0,0]*WORLD_B[0,1,0])
    assert not np.array_equal(WORLD_B[1,1]*WORLD_B[1,0,0],
                              WORLD_B[1,0]*WORLD_B[1,1,0])


def test_dimension_five_transport_fiber_and_integer_nullspace():
    op=marginalization_matrix()
    assert op.shape==(28,24)
    assert np.linalg.matrix_rank(op)==19
    assert op.shape[1]-np.linalg.matrix_rank(op)==(2-1)*(2-1)*(6-1)==5
    assert np.array_equal(op@WORLD_A.reshape(-1),op@WORLD_B.reshape(-1))
    assert np.array_equal(op@DELTA.reshape(-1),np.zeros(op.shape[0],dtype=int))


def test_marginal_poisson_law_equal_but_all_overlapping_margin_joint_laws_not():
    ma,mb=two_way_margins(WORLD_A),two_way_margins(WORLD_B)
    # For independent cells, the season x phase summed-over-site Poisson
    # variables are independent and have exactly the same parameters.
    assert poisson_independent_cells_KL(
        ma["branch_phase"].astype(float),mb["branch_phase"].astype(float))==0.
    assert poisson_independent_cells_KL(
        WORLD_A.astype(float),WORLD_B.astype(float))>0.
    # Joint repeated-observation law of all overlapping two-way margins
    # is NOT equal: their intersection-cell covariance differs.
    assert WORLD_A[0,0,0]==48 and WORLD_B[0,0,0]==51


def test_first_frozen_source_free_receipt_and_scientific_boundaries():
    r=construct_marginal_identifiability_witness(PLAN)
    assert r["status"]=="EXACT_POSITIVE_INTEGER_THREEWAY_MARGIN_FIBER_WITNESS"
    assert r["all_three_two_way_count_margins_exactly_equal"]
    assert not r["world_A_has_within_site_branch_time_change"]
    assert r["world_B_has_within_site_branch_time_change"]
    assert r["two_way_margin_operator_nullity"]==5
    assert r["independent_poisson_coarse_branch_phase_laws_identical"]
    assert r["independent_poisson_coarse_branch_phase_KL"]==0
    assert r["independent_poisson_full_threeway_KL_A_vs_B"]>0
    assert not r["joint_distribution_of_all_overlapping_two_way_margins_equal"]
    assert r["overlapping_margin_covariance_A"]==48
    assert r["overlapping_margin_covariance_B"]==51
    assert not r["ecobank_events_accessed"]
    assert not r["real_behavioural_hysteresis_claimed"]
    json.dumps(r,allow_nan=False)


def test_frozen_contract_mutation_fails_closed():
    mutated=json.loads(json.dumps(PLAN))
    mutated["world_B_symmetric_perturbation"]["e_rise"][0]=2
    with pytest.raises(ValueError,match="frozen"):
        construct_marginal_identifiability_witness(mutated)
    with pytest.raises(ValueError,match="require complete"):
        two_way_margins(WORLD_A[0])
    with pytest.raises(ValueError):
        poisson_independent_cells_KL(
            WORLD_A.astype(float),np.zeros_like(WORLD_A,dtype=float))
