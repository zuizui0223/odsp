"""Matched-budget distance-stratified detector q versus target passage-mix w.

SOURCE-FREE study of allocation under an explicit valid independently
labeled animal-passage opportunity model. Each allocation costs exactly
8*q_n + 4*w_n opportunities for eight q(distance,season,solar-bin)
reference detector efficiencies and four independent target near-distance
passage-mixture values. For fixed costs, trade precision in q vs w.

Four simultaneous CP families are split by VARIABLE:
   8 q: alpha_q=.0125, 4 w: alpha_w=.0125.
A fixed-target-bin independent Poisson/Fisher test spends .025, so
union-bound false certification <=.05 IF gold-standard opportunity
labels, calibrated q and effective camera exposure are valid.

This is a new prospective SOURCE-FREE budget comparison, not an
empirical Uljin seasonal result, and the original 41 matched
photoperiod dates and previous ODSP qualified routes are unchanged.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np

from .uljin_q_transport_distance_mix_v0 import (
    NEAR,FAR,cp_band,mixed_detector_q_bounds,
    detector_gamma_upper,q_effective,detector_crossproduct
)
from .uljin_independent_q_split_alpha_v0 import (
    _draw_site_four_count_table,_tail_from_margins
)

METHOD="uljin_q_w_equal_budget_design_v0"
ALPHA_Q=.0125
ALPHA_W=.0125
ALPHA_TEST=.025
REPS=200
SEED=2026101011
WORLDS=(
 ("null_balanced",1.,(.5,.5,.5,.5),(80,80,80,80)),
 ("null_distance_composition",1.,(.2,.8,.8,.2),(80,80,80,80)),
 ("true_seasonal_equal_mix",2.,(.5,.5,.5,.5),(200,200,200,200)),
 ("true_seasonal_with_distance_composition",2.,(.2,.8,.8,.2),
  (200,200,200,200)),
)
DESIGNS=(
 (2400,(("equal_per_cell",200,200),("q_heavy",250,100),("w_heavy",100,400))),
 (6000,(("equal_per_cell",500,500),("q_heavy",625,250),("w_heavy",250,1000))),
 (12000,(("equal_per_cell",1000,1000),("q_heavy",1250,500),("w_heavy",500,2000))),
 (24000,(("equal_per_cell",2000,2000),("q_heavy",2500,1000),("w_heavy",1000,4000))),
)


def validate_frozen(
    plan:Mapping[str,object],parent:Mapping[str,object]
)->None:
    expected_worlds=[{"id":name,"theta_latent":theta,"mix":list(w),
                      "animal_fixed_margin_template":list(counts)}
                     for name,theta,w,counts in WORLDS]
    expected_designs=[
        {"total_opportunities":total,"strategies":[
            {"name":method,"q_n":qn,"w_n":wn}
            for method,qn,wn in allocs]}
        for total,allocs in DESIGNS
    ]
    assumptions=plan.get("alpha",{})
    sampling=plan.get("synthetic_sampling",{})
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "FROZEN_POST_PR253_RESULTS_PRE_NEW_ALLOCATION_OUTCOMES"
        or plan.get("parent_pr")!=253
        or plan.get("parent_ledger")!=
            "ULJIN_DISTANCE_MIX_TIPPING_RADIUS_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("parent_ledger_first_ci")!=38010654940
        or plan.get("four_synthetic_truths")!=expected_worlds
        or plan.get("reference_budgets_and_allocations")!=expected_designs
        or plan.get("axes",{}).get("true_q_near")!=list(NEAR)
        or plan.get("axes",{}).get("true_q_far")!=list(FAR)
        or assumptions.get("q_simultaneous_error")!=ALPHA_Q
        or assumptions.get("target_w_simultaneous_error")!=ALPHA_W
        or assumptions.get("animal_exact_one_sided")!=ALPHA_TEST
        or assumptions.get("total_false_certification_union_bound")!=.05
        or sampling.get("replicates_per_case")!=REPS
        or sampling.get("base_seed")!=SEED
        or sampling.get("animal_device_hour_crossproduct")!=1
        or sampling.get("source_41_original_2022_mirror_date_pairs_unchanged") is not True
        or parent.get("record_type")!=
            "FIRST_FROZEN_ULJIN_DISTANCE_MIX_TIPPING_RADIUS_V0_TERMINAL_RESULT"
        or parent.get("first_scored_ci_run")!=38010654940
    ):
        raise ValueError("frozen reference-allocation plan or parent provenance altered")


def _simulate_one(
    world:int,budget:int,strategy:int,rep:int
)->dict[str,object]:
    if (
        type(world) is not int or not 0<=world<len(WORLDS)
        or type(budget) is not int or not 0<=budget<len(DESIGNS)
        or type(strategy) is not int or not 0<=strategy<3
        or type(rep) is not int or not 0<=rep<REPS
    ):
        raise ValueError("outside frozen design/replicate identity")
    name,theta_latent,mix,animal_margins=WORLDS[world]
    total,options=DESIGNS[budget]
    _,nq,nw=options[strategy]
    if 8*nq+4*nw!=total:
        raise ValueError("reference opportunity cost constraint violated")
    rng=np.random.default_rng(
        np.random.SeedSequence([SEED,world,budget,strategy,rep]))
    near_s=tuple(int(x) for x in rng.binomial(nq,np.asarray(NEAR)))
    far_s=tuple(int(x) for x in rng.binomial(nq,np.asarray(FAR)))
    mix_s=tuple(int(x) for x in rng.binomial(nw,np.asarray(mix)))
    q_lo,q_hi=cp_band(near_s+far_s,nq,ALPHA_Q)
    w_lo,w_hi=cp_band(mix_s,nw,ALPHA_W)
    qnear_lo,qnear_hi=q_lo[:4],q_hi[:4]
    qfar_lo,qfar_hi=q_lo[4:],q_hi[4:]
    qeff_lo,qeff_hi=mixed_detector_q_bounds(
        qnear_lo,qnear_hi,qfar_lo,qfar_hi,w_lo,w_hi)
    B=detector_gamma_upper(qeff_lo,qeff_hi)
    qt=q_effective(NEAR,FAR,mix)
    true_gamma=detector_crossproduct(qt)
    animals=_draw_site_four_count_table(
        rng,animal_margins,theta_latent*true_gamma)
    x=animals[2]
    if math.isfinite(B):
        p=_tail_from_margins(animal_margins,x,B)
        positive=bool(p<ALPHA_TEST)
    else:
        p=1.
        positive=False
    oracle_p=_tail_from_margins(animal_margins,x,true_gamma)
    qcover=bool(
        np.all(qnear_lo<=NEAR) and np.all(qnear_hi>=NEAR)
        and np.all(qfar_lo<=FAR) and np.all(qfar_hi>=FAR)
    )
    wcover=bool(np.all(w_lo<=mix) and np.all(w_hi>=mix))
    return {
        "certified":positive,
        "joint_q_coverage":qcover,
        "joint_w_coverage":wcover,
        "all_12_coverage":qcover and wcover,
        "HOLD":not math.isfinite(B),
        "B":B,
        "oracle_certification":bool(oracle_p<ALPHA_TEST),
        "exact_animal_total":sum(animals),
        "true_detector_gamma":true_gamma,
    }


def _fraction(v:list[dict[str,object]],key:str)->float:
    return sum(bool(x[key]) for x in v)/len(v)


def run_allocation_panel(
    frozen:Mapping[str,object],parent:Mapping[str,object],
    *,_test_replicates:int|None=None
)->dict[str,object]:
    validate_frozen(frozen,parent)
    reps=REPS if _test_replicates is None else _test_replicates
    if type(reps) is not int or not 1<=reps<=REPS:
        raise ValueError("replicate count not within frozen preflight support")
    rows=[]
    for wi,(name,theta,w,source) in enumerate(WORLDS):
        for bi,(total,options) in enumerate(DESIGNS):
            for si,(strategy,nq,nw) in enumerate(options):
                trials=[_simulate_one(wi,bi,si,k) for k in range(reps)]
                positives=_fraction(trials,"certified")
                oracle=_fraction(trials,"oracle_certification")
                valid_B=[x["B"] for x in trials if math.isfinite(x["B"])]
                expected_gamma=detector_crossproduct(q_effective(NEAR,FAR,w))
                if any(abs(x["true_detector_gamma"]-expected_gamma)>1e-12
                       or x["exact_animal_total"]!=sum(source) for x in trials):
                    raise ValueError("truth or conditional animal margin changed")
                rows.append({
                    "truth":name,
                    "true_latent_encounter_OR":theta,
                    "true_detector_OR":expected_gamma,
                    "reference_budget_opportunities":total,
                    "strategy":strategy,
                    "detector_q_reference_trials_per_eight_cells":nq,
                    "target_near_mix_reference_trials_per_four_cells":nw,
                    "q_reference_opportunities_total":8*nq,
                    "w_reference_opportunities_total":4*nw,
                    "worlds":reps,
                    "robust_latent_encounter_certification_fraction":positives,
                    "robust_certification_mc_standard_error":
                        math.sqrt(positives*(1-positives)/reps),
                    "oracle_known_detector_rate_conditional_certification_fraction":
                        oracle,
                    "eight_q_joint_coverage":_fraction(trials,"joint_q_coverage"),
                    "four_w_joint_coverage":_fraction(trials,"joint_w_coverage"),
                    "twelve_cell_joint_coverage":_fraction(trials,"all_12_coverage"),
                    "zero_detector_q_lower_HOLD_fraction":_fraction(trials,"HOLD"),
                    "median_finite_detector_crossproduct_upper_B":
                        (float(np.median(valid_B)) if valid_B else None),
                })
    if len(rows)!=len(WORLDS)*len(DESIGNS)*3:
        raise ValueError("not all original opportunity designs retained")
    for item in rows:
        if (item["q_reference_opportunities_total"]
           +item["w_reference_opportunities_total"]
           !=item["reference_budget_opportunities"]):
            raise ValueError("unfair opportunity budget")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":("SOURCE_FREE_Q_W_EQUAL_COST_FULL_PANEL"
                  if reps==REPS else "SOURCE_FREE_Q_W_ALLOCATION_PREFLIGHT"),
        "all_predeclared_worlds":rows,
        "world_count":len(rows)*reps,
        "truth_case_count":len(rows),
        "original_same_cost_opportunity_accounting_verified":True,
        "calibration_q_alpha":ALPHA_Q,
        "target_mix_w_alpha":ALPHA_W,
        "animal_exact_one_sided_alpha":ALPHA_TEST,
        "conditional_false_certification_union_bound":ALPHA_Q+ALPHA_W+ALPHA_TEST,
        "coverage_guarantee_requires_independent_valid_reference_labels":True,
        "oracle_comparison_not_equal_cost":True,
        "real_EcoBank_events_original_device_logs_reference_passages_read":False,
        "original_ODSP_qualified_routes_unchanged":True
    }
