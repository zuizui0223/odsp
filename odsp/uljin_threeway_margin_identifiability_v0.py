"""Exact source-free three-way marginalization counterexample.

Axes: two synthetic physical site TYPES × two photoperiod BRANCHES
× six solar-phase bins. World A has no within-site branch×phase
interaction. World B does. Both have IDENTICAL numerical two-way
site×branch, site×phase, and branch×phase count margins.

A stronger PROBABILITY-LAW equality is claimed ONLY for the season×phase
aggregate under independent Poisson sampling, where sums over sites
remain independent Poisson with the same means. Do NOT infer that
the JOINT LAW of all three overlapping two-way margins is equal.
Covariances of overlapping margin cells reveal the difference under
repeated independent Poisson tables. Nor is this a novel general theorem
about contingency tables.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import numpy as np

METHOD = "uljin_threeway_margin_identifiability_v0"
SITES=("early","late")
BRANCHES=("rising","falling")
K=6
WORLD_A = np.asarray([
    [[48,6,6,6,6,6],[144,18,18,18,18,18]],
    [[6,6,6,6,6,48],[2,2,2,2,2,16]],
],dtype=np.int64)
DELTA = np.asarray([
    [[3,0,0,0,0,-3],[-3,0,0,0,0,3]],
    [[-3,0,0,0,0,3],[3,0,0,0,0,-3]],
],dtype=np.int64)
WORLD_B = WORLD_A + DELTA

def verify_contract(plan:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!="FROZEN_SOURCE_FREE_BEFORE_FIRST_CONSTRUCTIVE_RESULT"
        or plan.get("parent_pr")!=238
        or plan.get("index_axes") !=
            ["site_type:early,late","branch:rising,falling","phase_bin:0..5"]
        or plan.get("world_A_counts") != {
            "early":{"rising":[48,6,6,6,6,6],
                     "falling":[144,18,18,18,18,18]},
            "late":{"rising":[6,6,6,6,6,48],
                    "falling":[2,2,2,2,2,16]},
        }
        or plan.get("world_B_symmetric_perturbation") != {
            "e_rise":[3,0,0,0,0,-3],
            "l_rise":[-3,0,0,0,0,3],
            "e_fall":[-3,0,0,0,0,3],
            "l_fall":[3,0,0,0,0,-3],
        }
        or plan.get("interpretation_boundaries",{}).get(
            "actual_EcoBank_or_station_records_read") is not False
        or plan.get("interpretation_boundaries",{}).get(
            "new_general_theorem") is not False
    ):
        raise ValueError("frozen three-way marginalization contract altered")

def two_way_margins(x:np.ndarray)->dict[str,np.ndarray]:
    if x.shape!=(2,2,K):
        raise ValueError("require complete physical site×branch×phase table")
    return {
        "site_branch":x.sum(axis=2),
        "site_phase":x.sum(axis=1),
        "branch_phase":x.sum(axis=0),
    }

def marginalization_matrix()->np.ndarray:
    """All 4+12+12 two-way marginal cells as linear functions of 24 cells."""
    columns=2*2*K
    m=[]
    for s in range(2):
        for b in range(2):
            row=np.zeros((2,2,K),dtype=np.int64)
            row[s,b,:]=1
            m.append(row.reshape(columns))
    for s in range(2):
        for k in range(K):
            row=np.zeros((2,2,K),dtype=np.int64)
            row[s,:,k]=1
            m.append(row.reshape(columns))
    for b in range(2):
        for k in range(K):
            row=np.zeros((2,2,K),dtype=np.int64)
            row[:,b,k]=1
            m.append(row.reshape(columns))
    return np.stack(m,axis=0)

def _is_constant_within_site_ratio(x:np.ndarray,s:int)->bool:
    a=x[s,0,:]
    d=x[s,1,:]
    return bool(np.all(d*a[0]==a*d[0]))

def poisson_independent_cells_KL(a:np.ndarray,b:np.ndarray)->float:
    """D(Pois(a) independent cells || Pois(b) independent cells)."""
    if (
        a.shape!=b.shape or np.any(a<=0) or np.any(b<=0)
        or not np.isfinite(a).all() or not np.isfinite(b).all()
    ):
        raise ValueError("Poisson rates must be positive finite matched tables")
    return float(np.sum(a*np.log(a/b)+b-a))

def construct_marginal_identifiability_witness(
    frozen_plan:Mapping[str,object]
)->dict[str,object]:
    verify_contract(frozen_plan)
    a,b=WORLD_A.copy(),WORLD_B.copy()
    if not (np.issubdtype(a.dtype,np.integer)
            and (a>0).all() and (b>0).all()
            and not np.array_equal(a,b)):
        raise ValueError("two distinct strictly positive integer worlds needed")
    for s in range(2):
        if not _is_constant_within_site_ratio(a,s):
            raise ValueError("baseline truth has forbidden within-site interaction")
        if _is_constant_within_site_ratio(b,s):
            raise ValueError("adversarial world unexpectedly invariant")

    am,bm=two_way_margins(a),two_way_margins(b)
    if any(not np.array_equal(am[k],bm[k]) for k in am):
        raise ValueError("two-way count summaries differ across worlds")
    A=marginalization_matrix()
    rank=int(np.linalg.matrix_rank(A))
    nullity=A.shape[1]-rank
    if (A.shape!=(28,24) or rank!=19 or nullity!=5
        or np.any(A@DELTA.reshape(-1)!=0)):
        raise ValueError("two-way marginal fiber algebra fails")

    # Poisson marginal aggregated law: sum of independent site cells has
    # independent Pois(sum_site mu) bins. This is EQUALITY OF LAWS.
    agg_kl=poisson_independent_cells_KL(
        am["branch_phase"].astype(float),bm["branch_phase"].astype(float))
    full_kl=poisson_independent_cells_KL(a.astype(float),b.astype(float))
    if not (agg_kl==0. and full_kl>0):
        raise ValueError("fine versus coarse KL information boundary fails")

    # Joint LAW of all overlapping 2-way summary tables is DIFFERENT:
    # Cov(site=early,branch=rising total,
    #     branch=rising,phase=first total) equals the corresponding cell mean.
    covariance_a=int(a[0,0,0])
    covariance_b=int(b[0,0,0])
    if covariance_a==covariance_b:
        raise ValueError("joint-margin dependence witness lost")

    return {
        "schema_version":1,
        "method":METHOD,
        "status":"EXACT_POSITIVE_INTEGER_THREEWAY_MARGIN_FIBER_WITNESS",
        "axes":{"site_type":list(SITES),"branch":list(BRANCHES),
                "phase_bins":K},
        "world_A_site_by_branch_by_phase_counts":a.tolist(),
        "world_B_site_by_branch_by_phase_counts":b.tolist(),
        "world_A_has_within_site_branch_time_change":False,
        "world_B_has_within_site_branch_time_change":True,
        "all_three_two_way_count_margins_exactly_equal":True,
        "two_way_count_margins":{k:v.tolist() for k,v in am.items()},
        "total_events_each_world":int(a.sum()),
        "two_way_margin_operator_shape":list(A.shape),
        "two_way_margin_operator_rank":rank,
        "two_way_margin_operator_nullity":nullity,
        "formula_for_nullity":"(n_site_types-1)*(n_branches-1)*(n_bins-1)",
        "perturbation_in_exact_integer_nullspace":True,
        "independent_poisson_coarse_branch_phase_laws_identical":True,
        "independent_poisson_coarse_branch_phase_KL":agg_kl,
        "independent_poisson_full_threeway_KL_A_vs_B":full_kl,
        "joint_distribution_of_all_overlapping_two_way_margins_equal":False,
        "overlapping_margin_covariance_A":covariance_a,
        "overlapping_margin_covariance_B":covariance_b,
        "observation_needed_for_direct_within_site_test":
            "physical station × matched-date pair × season branch × solar-phase bin counts with independent positive exposure",
        "evidence_type":"CONSTRUCTIVE_SOURCE_FREE_NOT_NEW_GENERAL_THEOREM",
        "ecobank_events_accessed":False,
        "device_operation_records_accessed":False,
        "real_behavioural_hysteresis_claimed":False,
        "previous_qualified_ODSP_routes_modified":False,
    }
