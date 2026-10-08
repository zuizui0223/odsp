"""Exhaustive source-free positive-integer completion of all two-way margins.

Post-PR239 distinct route. Condition on a ONE-TIME published set of all
three two-way COUNT margins from a 2×2×6 contingency table; enumerate all
strictly positive integer full tables that produce them. This is a
DETERMINISTIC identification region, NOT a statistical confidence set,
and does not claim equality of the JOINT repeated-sampling law of all
overlapping two-way margin measurements.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product
import math
from collections.abc import Mapping
import numpy as np

from .uljin_threeway_margin_identifiability_v0 import (
    WORLD_A,WORLD_B,two_way_margins,marginalization_matrix
)

METHOD="uljin_exact_integer_threeway_fiber_bounds_v1"


def _frozen(plan:Mapping[str,object], prior:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!="FROZEN_POST_V0_WITNESS_BEFORE_FIRST_ENUMERATION_OUTCOME"
        or plan.get("parent_pr")!=239
        or plan.get("parent_contract")!=
            "ULJIN_THREEWAY_MARGIN_IDENTIFIABILITY_V0_CONTRACT.json"
        or plan.get("parent_outcome")!=
            "ULJIN_THREEWAY_MARGIN_IDENTIFIABILITY_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("fiber_constraints",{}).get("strictly_positive_cell_minimum")!=1
        or plan.get("fiber_constraints",{}).get(
            "all_3_two_way_margins_fixed_to_world_A") is not True
        or plan.get("frozen_target")!=(
            "Early-site log odds ratio of (falling vs rising rate) at FIRST "
            "phase bin relative to LAST bin: log[(F_early,first/R_early,first)"
            "/(F_early,last/R_early,last)]; odds ratio exactly 1 indicates "
            "no early-vs-late shape shift.")
        or prior.get("record_type")!=
            "FIRST_SOURCE_FREE_THREEWAY_MARGIN_IDENTIFIABILITY_V0_TERMINAL_RESULT"
        or prior.get("first_ci_run")!=37792259770
        or prior.get("all_three_two_way_margins_exactly_equal") is not True
    ):
        raise ValueError("frozen post-witness integer-fiber plan or provenance changed")


def reconstruct_from_early_rise(
    early_rise:tuple[int,...],
    margins:dict[str,np.ndarray],
)->np.ndarray:
    if (len(early_rise)!=6 or
        any(type(k) is not int or k<1 for k in early_rise)):
        raise ValueError("require six positive integer early-rising cells")
    x=np.array(early_rise,dtype=np.int64)
    site_phase=margins["site_phase"]
    branch_phase=margins["branch_phase"]
    er=x
    ef=site_phase[0]-er
    lr=branch_phase[0]-er
    lf=site_phase[1]-lr
    table=np.stack([np.stack([er,ef]),np.stack([lr,lf])])
    if np.any(table<1):
        raise ValueError("candidate full table violates positive cell constraint")
    if any(not np.array_equal(actual,margins[name])
           for name,actual in two_way_margins(table).items()):
        raise ValueError("candidate does not preserve all three pairwise margins")
    return table


def early_log_odds_ratio(table:np.ndarray)->tuple[Fraction,float,int]:
    if table.shape!=(2,2,6) or np.any(table<=0):
        raise ValueError("full positive three-way table required")
    # (F_early_first / R_early_first) /
    # (F_early_last / R_early_last)
    numerator=int(table[0,1,0])*int(table[0,0,5])
    denominator=int(table[0,0,0])*int(table[0,1,5])
    ratio=Fraction(numerator,denominator)
    return ratio, math.log(float(ratio)), (
        1 if numerator>denominator else -1 if numerator<denominator else 0
    )


def exhaustive_fiber_bounds(plan:Mapping[str,object],
                            parent_ledger:Mapping[str,object])->dict[str,object]:
    _frozen(plan,parent_ledger)
    margins=two_way_margins(WORLD_A)
    full_rank=int(np.linalg.matrix_rank(marginalization_matrix()))
    if full_rank!=19:
        raise ValueError("parent two-way margin operator unexpectedly changed")
    site_phase=margins["site_phase"]
    branch_phase=margins["branch_phase"]
    site_branch=margins["site_branch"]
    lower=tuple(max(1,int(branch_phase[0,k]-site_phase[1,k]+1))
                for k in range(6))
    upper=tuple(min(int(site_phase[0,k]-1),int(branch_phase[0,k]-1))
                for k in range(6))
    target=int(site_branch[0,0])
    if any(lo>hi for lo,hi in zip(lower,upper)):
        raise ValueError("empty integer fiber")

    min_ratio=None
    max_ratio=None
    min_witness=None
    max_witness=None
    counts={"negative":0,"zero":0,"positive":0}
    represented_A=False
    represented_B=False
    total=0
    for values in product(*(range(lower[k],upper[k]+1) for k in range(5))):
        last=target-sum(values)
        if not lower[5]<=last<=upper[5]:
            continue
        tab=reconstruct_from_early_rise(tuple(map(int,values))+(int(last),),margins)
        ratio,_,sign=early_log_odds_ratio(tab)
        total+=1
        counts["positive" if sign>0 else "negative" if sign<0 else "zero"]+=1
        represented_A|=bool(np.array_equal(tab,WORLD_A))
        represented_B|=bool(np.array_equal(tab,WORLD_B))
        if min_ratio is None or ratio<min_ratio:
            min_ratio,min_witness=ratio,tab.copy()
        if max_ratio is None or ratio>max_ratio:
            max_ratio,max_witness=ratio,tab.copy()

    if (not represented_A or not represented_B or total<3
        or any(counts[k]==0 for k in counts)
        or not min_ratio<1<max_ratio
        or sum(counts.values())!=total):
        raise ValueError("frozen directional nonidentification gate failed")
    def ratio_summary(ratio:Fraction,table:np.ndarray)->dict[str,object]:
        return {
            "numerator":ratio.numerator,
            "denominator":ratio.denominator,
            "odds_ratio":float(ratio),
            "log_odds_ratio":math.log(float(ratio)),
            "complete_site_branch_phase_table":table.tolist(),
        }
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"EXHAUSTIVE_INTEGER_FIBER_SIGN_NOT_IDENTIFIED_SOURCE_FREE",
        "all_two_way_margins_fixed_to_world_A":True,
        "two_way_margins":{key:arr.tolist() for key,arr in margins.items()},
        "six_early_rising_lower_bounds":list(lower),
        "six_early_rising_upper_bounds":list(upper),
        "fixed_early_site_rising_total":target,
        "admissible_positive_integer_complete_table_count":total,
        "by_direction":{"autumn_relative_early_minus_late":
                        {"negative":counts["negative"],
                         "no_shift":counts["zero"],
                         "positive":counts["positive"]}},
        "min_early_site_first_vs_last_branch_odds_ratio":
            ratio_summary(min_ratio,min_witness),
        "max_early_site_first_vs_last_branch_odds_ratio":
            ratio_summary(max_ratio,max_witness),
        "original_world_A_inside_fiber":represented_A,
        "original_world_B_inside_fiber":represented_B,
        "both_signs_and_null_possible_for_same_pairwise_margins":True,
        "statistical_confidence_interval_computed":False,
        "overlapping_pairwise_margin_joint_sampling_laws_equivalent_claimed":False,
        "probability_distribution_over_admissible_tables_assumed":False,
        "real_camera_events_or_uptime_read":False,
        "new_general_theorem_claimed":False,
        "qualified_ODSP_route_changed":False,
    }
