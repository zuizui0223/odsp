"""Paired randomized detector-q reference calibration: CP versus Hoeffding.

A SOURCE-FREE post-PR249 finite-sample simulation. Both interval methods
receive the very same four independent binomial reference successes and
identical synthetic animal event table. This also EXACTLY replays the
earlier preregistered PR248 Hoeffding 16x600 panel (original RNG), without
reclassifying or retuning its observed outcomes.

Both joint detector bands pay α_cal=.025 over 4 q cells; the animal
noncentral Fisher test pays α_animal=.025. Under the declared external
reference-label, site and camera-response assumptions, the union bound
gives false certification probability <=.05, not a demonstrated
ecological result or empirical population-level size guarantee.
"""
from __future__ import annotations

from collections.abc import Mapping
from functools import lru_cache
import math
import numpy as np

from .uljin_independent_q_split_alpha_v0 import (
    TRUTHS,N_REF,REPS,SEED,ALPHA_CAL,ALPHA_TEST,ALPHA_ALL,
    QBounds,independent_hoeffding_bounds,
    _draw_site_four_count_table,_tail_from_margins,
    true_detector_crossproduct,
)
from .uljin_detector_bias_robust_or_v0 import FourCells

ID="uljin-paired-randomized-clopper-pearson-vs-hoeffding-power-v1"
CP_TAIL=ALPHA_CAL/8
ALL_CASES=len(TRUTHS)*len(N_REF)


def verify_frozen(plan:Mapping[str,object],old:Mapping[str,object],
                  cp_ledger:Mapping[str,object])->None:
    if (not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!=
        "FROZEN_AFTER_HOEFFDING_AND_DETERMINISTIC_CP_RESULTS_BEFORE_RANDOM_CP_RESULTS"
        or plan.get("parent_prs")!=[248,249]
        or plan.get("parent_hoeffding_ledger")!=
           "ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("parent_cp_deterministic_ledger")!=
           "ULJIN_EXACT_CP_VS_HOEFFDING_Q_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("sampling",{}).get("reference_trials_per_q_cell")!=list(N_REF)
        or plan.get("sampling",{}).get("replicates_per_case")!=REPS
        or plan.get("sampling",{}).get("root_seed")!=SEED
        or plan.get("sampling",{}).get("worlds")!=[x[0] for x in TRUTHS]
        or plan.get("methods",{}).get("calibration_joint_alpha")!=ALPHA_CAL
        or plan.get("methods",{}).get("animal_conditional_alpha")!=ALPHA_TEST
        or plan.get("methods",{}).get("overall_false_positive_bound")!=ALPHA_ALL
        or old.get("record_type")!=
           "FIRST_FROZEN_INDEPENDENT_DETECTOR_Q_SPLIT_ALPHA_V0_TERMINAL_RESULT"
        or old.get("first_complete_ci_run")!=37888152647
        or cp_ledger.get("record_type")!=
           "FIRST_FROZEN_EXACT_CP_VS_HOEFFDING_Q_V0_TERMINAL_RESULT"
        or cp_ledger.get("first_ci_run")!=37888492632
        or len(old.get("worlds",[]))!=len(TRUTHS)
    ):
        raise ValueError("frozen paired randomized q calibration contract/provenance mismatch")


try:
    from scipy.special import betaincinv
except ImportError as e:
    raise ImportError(
        "This optional isolated calibration benchmark requires scipy. "
        "Install in the dedicated workflow, not the ODSP package dependency."
    ) from e


def exact_cp_four_cell_bounds(
    successes:tuple[int,int,int,int],n:int
)->QBounds:
    """Exact two-sided CP per q cell; 4-way Bonferroni coverage >=.975."""
    if (type(successes) is not tuple or len(successes)!=4
        or type(n) is not int or n<1
        or any(type(x) is not int or x<0 or x>n for x in successes)):
        raise ValueError("four integer independently verified q samples required")
    lower=[]
    upper=[]
    for s in successes:
        lo=(float(betaincinv(s,n-s+1,CP_TAIL)) if s>0 else 0.)
        hi=(float(betaincinv(s+1,n-s,1.-CP_TAIL)) if s<n else 1.)
        if (not 0<=lo<=hi<=1 or not math.isfinite(lo)
            or not math.isfinite(hi)):
            raise ValueError("CP interval is invalid")
        lower.append(lo)
        upper.append(hi)
    return QBounds(tuple(lower),tuple(upper),n,successes)


def paired_world(wi:int,ni:int,rep:int)->dict[str,object]:
    if not (0<=wi<len(TRUTHS) and 0<=ni<len(N_REF) and 0<=rep<REPS):
        raise ValueError("only originally frozen q calibration simulation coordinates")
    name,q,e,source,latent_or=TRUTHS[wi]
    n=N_REF[ni]
    rng=np.random.default_rng(np.random.SeedSequence([SEED,wi,ni,rep]))
    successes=tuple(int(x) for x in rng.binomial(n,np.asarray(q)))
    theta_e=FourCells(source,e).effort_OR
    detector_or=true_detector_crossproduct(q)
    animals=_draw_site_four_count_table(rng,source,theta_e*detector_or*latent_or)
    x=animals[2]
    hoeff=independent_hoeffding_bounds(successes,n)
    cp=exact_cp_four_cell_bounds(successes,n)
    naive=_tail_from_margins(source,x,theta_e)<ALPHA_ALL
    ans={
        "naive_5pct_reject":naive,
        "same_reference_successes_for_both_methods":True,
        "same_animal_event_counts_for_both_methods":True,
        "observed_animal_2x2_table":animals,
    }
    for key,b in (("Hoeffding",hoeff),("CP",cp)):
        B=b.detector_gamma_upper
        hold=not math.isfinite(B)
        p=(_tail_from_margins(source,x,theta_e*B) if not hold else 1.)
        ans[key]={
            "joint_q_coverage":b.covers(q),
            "hold":hold,
            "certification":(not hold and p<ALPHA_TEST),
            "B":B,
            "robust_p":p,
        }
    return ans


def _median_finite(values:list[float])->float|None:
    finite=[v for v in values if math.isfinite(v)]
    return float(np.median(finite)) if finite else None


def paired_randomized_cp_panel(
    plan:Mapping[str,object],
    old:Mapping[str,object],
    cp_ledger:Mapping[str,object],
    *,_test_replicates:int|None=None
)->dict[str,object]:
    verify_frozen(plan,old,cp_ledger)
    nrep=REPS if _test_replicates is None else _test_replicates
    if type(nrep) is not int or not 1<=nrep<=REPS:
        raise ValueError("preflight replication override outside original ceiling")
    all_rows=[]
    old_worlds={w["id"]:w for w in old["worlds"]}
    replay_verified=(nrep==REPS)
    for wi,(name,q,e,source,latent_or) in enumerate(TRUTHS):
        parent=old_worlds[name]
        for ni,n in enumerate(N_REF):
            draws=[paired_world(wi,ni,r) for r in range(nrep)]
            result={
                "truth":name,
                "true_latent_encounter_OR":latent_or,
                "true_detector_crossproduct":true_detector_crossproduct(q),
                "reference_opportunities_per_q_cell":n,
                "replicates":nrep,
                "naive_detector_ignorant_rejection_fraction":sum(
                    int(d["naive_5pct_reject"]) for d in draws)/nrep,
            }
            for method in ("Hoeffding","CP"):
                records=[d[method] for d in draws]
                hits=sum(int(x["certification"]) for x in records)
                p=hits/nrep
                result[method]={
                    "certification_count":hits,
                    "certification_fraction":p,
                    "certification_monte_carlo_standard_error":
                        math.sqrt(p*(1-p)/nrep),
                    "empirical_four_q_simultaneous_coverage_fraction":
                        sum(int(x["joint_q_coverage"]) for x in records)/nrep,
                    "no_finite_q_crossproduct_HOLD_fraction":
                        sum(int(x["hold"]) for x in records)/nrep,
                    "median_finite_detector_crossproduct_upper_B":
                        _median_finite([x["B"] for x in records]),
                }
            cp_only=sum(
                int(d["CP"]["certification"] and
                    not d["Hoeffding"]["certification"]) for d in draws)
            h_only=sum(
                int(d["Hoeffding"]["certification"] and
                    not d["CP"]["certification"]) for d in draws)
            diffs=np.array([
                int(d["CP"]["certification"])-int(d["Hoeffding"]["certification"])
                for d in draws],dtype=float)
            result["CP_only_certification_count"]=cp_only
            result["Hoeffding_only_certification_count"]=h_only
            result["paired_CP_minus_Hoeffding_certification_fraction"]=(cp_only-h_only)/nrep
            result["paired_difference_Monte_Carlo_SE"]=(
                float(np.std(diffs,ddof=1)/math.sqrt(nrep))
                if nrep>1 else None
            )
            if nrep==REPS:
                for metric,legacy in (
                    ("certification_fraction","robust_reject_fractions"),
                    ("empirical_four_q_simultaneous_coverage_fraction","joint_q_coverages"),
                    ("no_finite_q_crossproduct_HOLD_fraction","lower_zero_hold_fraction"),
                    ("median_finite_detector_crossproduct_upper_B","median_detector_bound_B")
                ):
                    previous=parent.get(legacy,[0.,0.,0.,0.])[ni]
                    present=result["Hoeffding"][metric]
                    if abs(present-previous)>1e-12:
                        raise ValueError(f"PREVIOUS frozen Hoeffding {name}/{n} {metric} did NOT replay")
                if abs(result["naive_detector_ignorant_rejection_fraction"]-
                       parent["naive_ignore_q_reject_fractions"][ni])>1e-12:
                    raise ValueError("previous naive detector-ignore result failed exact replay")
            all_rows.append(result)
    if len(all_rows)!=ALL_CASES:
        raise ValueError("predeclared calibration study case loss")
    return {
        "schema_version":1,"method":ID,
        "status":("SOURCE_FREE_RANDOMIZED_CP_HOEFFDING_FULL_PANEL"
                  if nrep==REPS else "SOURCE_FREE_CP_PAIRED_PREFLIGHT_ONLY"),
        "total_worlds":len(all_rows)*nrep,
        "case_count":len(all_rows),
        "replications_per_case":nrep,
        "replayed_parent_first_Hoeffding_outcomes_without_retuning":replay_verified,
        "alpha_detector_joint":ALPHA_CAL,
        "alpha_exact_animal_test":ALPHA_TEST,
        "total_nominal_false_certification_upper_bound":ALPHA_ALL,
        "CP_and_Hoeffding_receive_same_reference_and_animal_draws":True,
        "simulated_case_results":all_rows,
        "coverage_guarantee_from_mathematics_not_600_draws":True,
        "real_camera_sensor_reference_and_ungulate_events_opened":False,
        "existing_qualified_ODSP_routes_untouched":True,
    }
