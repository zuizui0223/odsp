"""Paired astronomy-neutral synthetic placebo for geometric excess selection.

Source-free v1 after v0's first frozen outcomes. All 82 simulated stations,
41 original pairs and every observed synthetic event are identical across:
(A) original spring/autumn calendar geometry;
(B) counterfactual identical ASCENDING-date geometry on both branches;
(C) original invariant solar-phase coordinate. Any difference A vs B is
caused by the imposed astronomy mapping, conditional on the simulation,
not by resampling another wildlife population.
"""
from __future__ import annotations

from typing import Mapping
import math
import numpy as np

from .uljin_finite_sample_clock_alias_selection_v0 import (
    PROFILES,SCALES,WORLDS,SEED,GRID_INTERVALS,SITES,PAIRS,
    verify_frozen as verify_v0,
    inverse_cdf_table,geometry_for_pairs,phase_to_civil_numpy,
    event_count_frames,heldout_site_equal_gain,
)
from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)

METHOD="uljin_geometry_neutral_paired_placebo_v1"


def verify_frozen_contract(plan:Mapping[str,object],
                           previous:Mapping[str,object],
                           ledger:Mapping[str,object])->None:
    verify_v0(previous)
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!="FROZEN_POST_V0_OUTCOME_BEFORE_FIRST_PLACEBO_RESULT"
        or plan.get("parent_pr")!=235
        or plan.get("profiles")!=[p[0] for p in PROFILES]
        or plan.get("total_expected_event_counts")!=list(SCALES)
        or plan.get("worlds_per_scenario")!=WORLDS
        or plan.get("seed")!=SEED
        or plan.get("parent_v0_contract")!=
            "ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_CONTRACT.json"
        or plan.get("parent_v0_outcome")!=
            "ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_FIRST_RESULT_LEDGER.json"
        or plan.get("primary_effect")!=
        "Mean per-world paired difference I(actual_clock>0 AND solar<=0) - I(placebo_clock>0 AND solar<=0), reported across all nine profiles and event counts"
        or ledger.get("record_type")!=
            "FIRST_PRE_FROZEN_NINE_CASE_FINITE_SAMPLE_OUTCOME_LEDGER"
        or ledger.get("first_ci_head_sha")!=
            "397efd713a837a166c344aee004d9a801e5b1303"
        or len(ledger.get("cases",[]))!=9
    ):
        raise ValueError("paired geometry-neutral placebo frozen contract changed")


def three_same_event_frames(
    rng:np.random.Generator,scale:int,geometry:np.ndarray,
    cdf:np.ndarray,grid:np.ndarray,
)->tuple[np.ndarray,np.ndarray,np.ndarray,int]:
    n=int(rng.poisson(scale))
    site=rng.integers(0,SITES,n)
    pair=rng.integers(0,PAIRS,n)
    branch=rng.integers(0,2,n)
    phase=np.interp(rng.random(n),cdf,grid)
    solar_bin=np.minimum(5,(phase/4).astype(int))

    real_sr=geometry[pair,branch,0]
    real_ss=geometry[pair,branch,1]
    placebo_sr=geometry[pair,0,0]
    placebo_ss=geometry[pair,0,1]
    actual=phase_to_civil_numpy(phase,real_sr,real_ss)
    placebo=phase_to_civil_numpy(phase,placebo_sr,placebo_ss)
    actual_bin=np.minimum(5,(actual/4).astype(int))
    placebo_bin=np.minimum(5,(placebo/4).astype(int))

    base=((site*PAIRS+pair)*2+branch)*6
    frame=(SITES,PAIRS,2,6)
    def to_cells(which_bin):
        return np.bincount(base+which_bin,
                           minlength=SITES*PAIRS*2*6).reshape(frame)
    a=to_cells(actual_bin)
    b=to_cells(placebo_bin)
    s=to_cells(solar_bin)
    if (not np.array_equal(a.sum(axis=3),b.sum(axis=3))
        or not np.array_equal(a.sum(axis=3),s.sum(axis=3))):
        raise ValueError("paired geometry controls changed latent animal events")
    return a.sum(axis=1),b.sum(axis=1),s.sum(axis=1),n


def run_one_paired_placebo_world(
    profile_index:int,scale_index:int,world_index:int,
    geometry:np.ndarray,cdf:np.ndarray,grid:np.ndarray,
)->dict[str,object]:
    scale=SCALES[scale_index]
    rng=np.random.default_rng(np.random.SeedSequence(
        [SEED,profile_index,scale_index,world_index]))
    real,neutral,solar,n=three_same_event_frames(
        rng,scale,geometry,cdf,grid)
    actual_gain=heldout_site_equal_gain(real)
    placebo_gain=heldout_site_equal_gain(neutral)
    solar_gain=heldout_site_equal_gain(solar)
    actual_selected=actual_gain>0
    neutral_selected=placebo_gain>0
    solar_selected=solar_gain>0
    actual_only=actual_selected and not solar_selected
    placebo_only=neutral_selected and not solar_selected
    return {
        "events":n,
        "actual_clock_gain":actual_gain,
        "placebo_clock_gain":placebo_gain,
        "solar_gain":solar_gain,
        "actual_clock_selected":actual_selected,
        "placebo_clock_selected":neutral_selected,
        "solar_selected":solar_selected,
        "actual_clock_only":actual_only,
        "placebo_clock_only":placebo_only,
        "paired_indicator_difference":int(actual_only)-int(placebo_only),
    }


def run_paired_geometry_placebo_panel(
    calendar_contract:Mapping[str,object],
    v0_contract:Mapping[str,object],
    first_v0_ledger:Mapping[str,object],
    placebo_contract:Mapping[str,object],
    *,_test_world_count:int|None=None,
)->dict[str,object]:
    verify_frozen_contract(placebo_contract,v0_contract,first_v0_ledger)
    cal=generate_preoutcome_2022_mirror_calendar(calendar_contract)
    pairs=cal["matched_dates"]
    if len(pairs)!=PAIRS:
        raise ValueError("original 41 mirrored pairs required")
    geometry=geometry_for_pairs(pairs)
    worlds=WORLDS if _test_world_count is None else _test_world_count
    if type(worlds) is not int or not 1<=worlds<=WORLDS:
        raise ValueError("world count invalid")
    cases=[]
    for pi,profile in enumerate(PROFILES):
        cdf,grid=inverse_cdf_table(profile)
        for si,scale in enumerate(SCALES):
            draws=[run_one_paired_placebo_world(pi,si,k,geometry,cdf,grid)
                   for k in range(worlds)]
            def values(name):
                return np.array([d[name] for d in draws],dtype=float)
            gain_real=values("actual_clock_gain")
            gain_placebo=values("placebo_clock_gain")
            gain_solar=values("solar_gain")
            actual_only=values("actual_clock_only")
            neutral_only=values("placebo_clock_only")
            paired=values("paired_indicator_difference")
            case={
                "profile":profile[0],
                "expected_total_events":scale,
                "worlds":worlds,
                "actual_clock_only_selection_frequency":float(actual_only.mean()),
                "placebo_clock_only_selection_frequency":float(neutral_only.mean()),
                "paired_excess_clock_only_frequency":float(paired.mean()),
                "paired_excess_monte_carlo_standard_error":
                    float(paired.std(ddof=1)/np.sqrt(worlds))
                    if worlds>1 else None,
                "actual_clock_shape_selection_frequency":
                    float(values("actual_clock_selected").mean()),
                "placebo_clock_shape_selection_frequency":
                    float(values("placebo_clock_selected").mean()),
                "solar_shape_selection_frequency":
                    float(values("solar_selected").mean()),
                "mean_actual_clock_gain":float(gain_real.mean()),
                "mean_placebo_clock_gain":float(gain_placebo.mean()),
                "mean_solar_gain":float(gain_solar.mean()),
                "median_paired_actual_minus_placebo_gain":
                    float(np.median(gain_real-gain_placebo)),
            }
            if worlds==WORLDS:
                earlier=next((c for c in first_v0_ledger["cases"]
                              if c["profile"]==profile[0]
                              and c["expected_total_events"]==scale),None)
                if (earlier is None
                    or abs(case["actual_clock_only_selection_frequency"]-
                           earlier["clock_only_selection_fraction"])>1e-12
                    or abs(case["mean_actual_clock_gain"]-
                           earlier["mean_civil_gain"])>1e-10
                    or abs(case["mean_solar_gain"]-
                           earlier["mean_phase_gain"])>1e-10):
                    raise ValueError("original v0 first outcome failed exact replay")
            cases.append(case)
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"SOURCE_FREE_PAIRED_GEOMETRY_NEUTRAL_PLACEBO_ONLY",
        "worlds_per_case":worlds,
        "case_count":len(cases),
        "all_41_original_astronomical_pairs":True,
        "same_simulated_events_across_three_clock_projections":True,
        "v0_outcome_replayed_if_full_panel":worlds==WORLDS,
        "cases":cases,
        "not_a_calibrated_5pct_test":True,
        "real_wildlife_event_rows_read":False,
        "real_camera_uptime_rows_read":False,
        "prior_ODSP_results_reclassified":False,
    }
