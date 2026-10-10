"""Gold-standard independent q/w calibration uncertainty decomposition.

Scientific estimand: within one preselected site×matched-photoperiod-pair,
detector q seasonal early-vs-late log odds ratio. Distance-specific q
and target near/far opportunity mix w are BOTH estimated from separate
independent labeled passages, not focal camera detections.

Delta-method first-order Var(log detector OR_hat) = A/nq + C/nw,
where A and C are EXACT local-gradient propagation coefficients
under the four-by-two binomial sampling model. This is NOT the
animal encounter OR confidence interval or causal zeitgeber evidence.

The continuous independent opportunity-count variance optimum
nq/nw=sqrt((4*A)/(8*C)) uses costs 8 q cells and 4 w cells;
the empirical robust CP+Fisher decision's optimal allocation may differ.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import numpy as np

METHOD="uljin_q_w_variance_budget_decomposition_v0"
SEED=2026101015
REPS=800
NEAR=(.9,.9,.9,.9)
FAR=(.3,.3,.3,.3)
WORLDS=(
    ("null_balanced",(.5,.5,.5,.5)),
    ("null_distance_composition",(.2,.8,.8,.2)),
    ("true_seasonal_equal_mix",(.5,.5,.5,.5)),
    ("true_seasonal_with_distance_composition",(.2,.8,.8,.2))
)
DESIGNS=(
    (2400,(("equal_per_cell",200,200),("q_heavy",250,100),("w_heavy",100,400))),
    (6000,(("equal_per_cell",500,500),("q_heavy",625,250),("w_heavy",250,1000))),
    (12000,(("equal_per_cell",1000,1000),("q_heavy",1250,500),("w_heavy",500,2000))),
    (24000,(("equal_per_cell",2000,2000),("q_heavy",2500,1000),("w_heavy",1000,4000))),
)
SIGN=np.array([-1.,1.,1.,-1.])


def _validate_frozen(plan:Mapping[str,object],parent:Mapping[str,object])->None:
    if not isinstance(plan,Mapping) or not isinstance(parent,Mapping):
        raise ValueError("original source-free q/w budget contract required")
    worlds=plan.get("source_unchanged",{}).get("target_truth_worlds",[])
    designs=plan.get("source_unchanged",{}).get("strategies",[])
    budgets=plan.get("source_unchanged",{}).get("reference_budgets",[])
    expected_worlds=[{"id":z,"mix":list(w)} for z,w in WORLDS]
    expected_designs=[
        {"id":name,
         "nq_per_8_q_cell":[options[s][1] for _,options in DESIGNS],
         "nw_per_4_w_cell":[options[s][2] for _,options in DESIGNS]}
        for s,name in enumerate(("equal_per_cell","q_heavy","w_heavy"))]
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!=
            "FROZEN_AFTER_PR254_FIRST_RESULTS_BEFORE_NEW_MONTE_CARLO_VARIANCE_RESULT"
        or plan.get("parent_pr")!=254
        or plan.get("parent_first_ci")!=38011059007
        or plan.get("parent_first_result")!=
           "ULJIN_Q_W_EQUAL_BUDGET_V0_FIRST_RESULT_LEDGER.json"
        or worlds!=expected_worlds
        or designs!=expected_designs
        or budgets!=[budget for budget,_ in DESIGNS]
        or plan.get("source_unchanged",{}).get("q_near")!=list(NEAR)
        or plan.get("source_unchanged",{}).get("q_far")!=list(FAR)
        or plan.get("validation",{}).get(
            "independent_replications_per_world_budget_strategy")!=REPS
        or plan.get("validation",{}).get("original_world_seed")!=SEED
        or parent.get("record_type")!=
           "FIRST_FROZEN_ODSP_EQUAL_REFERENCE_Q_W_BUDGET_V0_TERMINAL_RESULT"
        or parent.get("first_scored_workflow_id")!=38011059007
        or parent.get("first_artifact_id")!=11652334689
        or len(parent.get("all_48_first_logged_aggregate_outcomes",[]))!=48
    ):
        raise ValueError("original frozen q/w decomposition or parent results altered")


def detector_log_or(qnear:np.ndarray,qfar:np.ndarray,w:np.ndarray)->np.ndarray:
    """Log q_Fearly+log q_Rlate-log q_Rearly-log q_Flate.

    Any leading replicate axes broadcast with last dimension four.
    """
    qnear=np.asarray(qnear,dtype=float)
    qfar=np.asarray(qfar,dtype=float)
    w=np.asarray(w,dtype=float)
    if (qnear.shape[-1]!=4 or qfar.shape[-1]!=4 or w.shape[-1]!=4
        or np.any(qnear<=0) or np.any(qnear>1)
        or np.any(qfar<=0) or np.any(qfar>1)
        or np.any(w<0) or np.any(w>1)):
        raise ValueError("need positive true independent four-cell q and valid near mix")
    effective=w*qnear+(1.-w)*qfar
    if np.any(effective<=0):
        raise ValueError("HOLD: log detector OR not defined at 0 effective q")
    return np.sum(SIGN*np.log(effective),axis=-1)


def local_variance_coefficients(
    qnear:tuple[float,...],
    qfar:tuple[float,...],
    w:tuple[float,...],
)->dict[str,float]:
    a,b,m=(np.asarray(x,dtype=float) for x in (qnear,qfar,w))
    detector_log_or(a,b,m)
    p=m*a+(1.-m)*b
    qvar=np.sum((m*m*a*(1-a)+(1-m)*(1-m)*b*(1-b))/(p*p))
    wvar=np.sum(((a-b)**2*m*(1-m))/(p*p))
    if not qvar>0 or not wvar>0:
        raise ValueError("positive detector and distance-mix variation expected")
    return {"A_q":float(qvar),"C_w":float(wvar),
            "true_log_detector_OR":float(detector_log_or(a,b,m)),
            "true_detector_OR":float(math.exp(detector_log_or(a,b,m)))}


def variance_at_budget(A:float,C:float,budget:float,ratio:float)->float:
    """Continuous cost constraint 8*nq+4*nw=T, nq/nw=ratio."""
    if (not all(math.isfinite(x) and x>0 for x in (A,C,budget,ratio))):
        raise ValueError("strictly positive finite budget and coefficients required")
    nw=budget/(8*ratio+4)
    nq=ratio*nw
    return A/nq+C/nw


def analytic_continuous_allocation(A:float,C:float)->dict[str,float]:
    """One cost-constrained local optimum, not a global field design."""
    if not (A>0 and C>0):
        raise ValueError("unidentified reference variance component")
    r=math.sqrt(A/(2*C))
    q_budget_share=8*r/(8*r+4)
    for factor in (.8,1.2):
        if variance_at_budget(A,C,10000.,r)>variance_at_budget(
            A,C,10000.,r*factor)+1e-12:
            raise ValueError("derived analytic variance optimum incorrect")
    return {
        "continuous_optimal_nq_over_nw":r,
        "fraction_total_reference_opportunities_to_q":q_budget_share,
        "fraction_total_reference_opportunities_to_w":1-q_budget_share,
    }


def one_design(
    world_index:int,budget_index:int,strategy_index:int,replicates:int=REPS
)->dict[str,object]:
    if (
        type(world_index) is not int or not 0<=world_index<len(WORLDS)
        or type(budget_index) is not int or not 0<=budget_index<len(DESIGNS)
        or type(strategy_index) is not int or not 0<=strategy_index<3
        or type(replicates) is not int or not 1<=replicates<=REPS
    ):
        raise ValueError("outside fixed calibration variance design")
    name,mix=WORLDS[world_index]
    budget,choices=DESIGNS[budget_index]
    strategy,nq,nw=choices[strategy_index]
    if 8*nq+4*nw!=budget:
        raise ValueError("unequal independent passage sample costs")
    c=local_variance_coefficients(NEAR,FAR,mix)
    vq=c["A_q"]/nq
    vw=c["C_w"]/nw
    expected=vq+vw
    qtrue=np.array([NEAR,FAR])
    wtrue=np.asarray(mix)
    rng=np.random.default_rng(
        np.random.SeedSequence([SEED,world_index,budget_index,strategy_index,0]))
    successes=rng.binomial(nq,qtrue[None,:,:],size=(replicates,2,4))
    what=rng.binomial(nw,wtrue[None,:],size=(replicates,4))/nw
    qa=successes[:,0,:]/nq
    qb=successes[:,1,:]/nq
    positive=bool(np.all(successes>0))
    p_full=np.sum(np.array(what)*qa+(1-what)*qb<=0)
    if p_full>0 or not positive:
        raise ValueError("HOLD: zero estimated camera q; no pseudo counts")
    estimated=detector_log_or(qa,qb,what)
    q_only=detector_log_or(qa,qb,np.broadcast_to(wtrue,(replicates,4)))
    w_only=detector_log_or(np.broadcast_to(qtrue[0],(replicates,4)),
                           np.broadcast_to(qtrue[1],(replicates,4)),what)
    actual=float(np.var(estimated,ddof=1)) if replicates>1 else None
    sample_vq=float(np.var(q_only,ddof=1)) if replicates>1 else None
    sample_vw=float(np.var(w_only,ddof=1)) if replicates>1 else None
    discrepancy=(actual/expected-1.) if actual is not None else None
    if replicates==REPS and abs(discrepancy)>.2:
        raise ValueError("frozen analytic vs empirical q/w variance mismatch exceeds 20pct")
    return {
        "truth":name,"budget":budget,"strategy":strategy,
        "n_q_per_each_of_eight_reference_cells":nq,
        "n_w_per_each_of_four_target_mix_cells":nw,
        "q_reference_opportunities":8*nq,
        "w_reference_opportunities":4*nw,
        "replicates":replicates,
        "true_detector_OR":c["true_detector_OR"],
        "q_coefficient_A":c["A_q"],
        "w_coefficient_C":c["C_w"],
        "first_order_q_variance":vq,
        "first_order_w_variance":vw,
        "first_order_total_log_detector_OR_variance":expected,
        "first_order_fraction_variance_due_to_q":vq/expected,
        "first_order_fraction_variance_due_to_w":vw/expected,
        "sample_variance_q_only_or_null":sample_vq,
        "sample_variance_w_only_or_null":sample_vw,
        "sample_variance_full_or_null":actual,
        "empirical_over_first_order_relative_error_or_null":discrepancy,
        "sample_mean_log_detector_OR":float(np.mean(estimated)),
        "sample_bias_log_detector_OR":float(
            np.mean(estimated)-c["true_log_detector_OR"]),
        "log_detector_OR_variance_formula_not_exact_small_n":True,
    }


def run_full_decomposition(
    plan:Mapping[str,object],parent:Mapping[str,object],
    *,_test_replicates:int|None=None
)->dict[str,object]:
    _validate_frozen(plan,parent)
    reps=REPS if _test_replicates is None else _test_replicates
    if type(reps) is not int or not 1<=reps<=REPS:
        raise ValueError("unfrozen variance validation replicate count")
    worlds=[one_design(w,b,s,reps) for w in range(4)
            for b in range(4) for s in range(3)]
    if len(worlds)!=48 or any(
        z["q_reference_opportunities"]+z["w_reference_opportunities"]
         !=z["budget"] for z in worlds
    ):
        raise ValueError("not all original equal budgets/48 worlds audited")
    opt={name:analytic_continuous_allocation(
        local_variance_coefficients(NEAR,FAR,mix)["A_q"],
        local_variance_coefficients(NEAR,FAR,mix)["C_w"])
        for name,mix in WORLDS}
    return {
        "schema_version":1,
        "method":METHOD,
        "status":("SOURCE_FREE_Q_W_DELTA_VARIANCE_FULL_FIRST_PANEL"
                  if reps==REPS else "SOURCE_FREE_Q_W_DELTA_PREFLIGHT_ONLY"),
        "all_original_equal_budget_scenarios":worlds,
        "number_of_scenarios":48,
        "independent_gold_standard_reference_replications_per_scenario":reps,
        "total_independent_worlds":48*reps,
        "continuous_local_variance_optimum_by_truth":opt,
        "first_order_only_not_exact_variance_or_confidence_interval":True,
        "real_animal_count_and_device_hour_sampling_variance_not_included":True,
        "real_Uljin_animal_events_reference_sensors_not_accessed":True,
        "parent_first_results_and_previous_qualified_ODSP_routes_unchanged":True
    }
