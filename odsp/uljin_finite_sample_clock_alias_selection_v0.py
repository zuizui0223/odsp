"""Finite-sample, same-event solar-phase vs civil-clock geometric aliasing.

ONLY synthetic physical sites and the unchanged 41 astronomical date pairs.
An identical solar-phase intensity on both branches is simulated ONCE.
The SAME simulated events enter both time representations. No independent
resampling of clock and solar observations, real device logs or animals.

We use the EXISTING penalized conditional-binomial fitter on six collapsed
sufficient-statistic cells. With fixed full-day effort (four hours/bin on
both branches), this gives exactly the same fit as the full station×pair×bin
frame; the scoring denominator retains all 41*6 original cells/site.
"""
from __future__ import annotations

from datetime import date
from typing import Mapping
import math

import numpy as np

from .uljin_conditional_branch_shape_v0 import (
    MirrorCountCell, fit_conditional_branch_model,
)
from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)
from .uljin_original_pairs_equation_of_time_v0 import civil_solar_geometry

ID = "uljin_finite_sample_clock_vs_phase_same_events_v0"
PROFILES = (
    ("uniform_phase",0.0,0.0,0.0),
    ("smooth_morning",1.0,2.0,8.0),
    ("smooth_evening",1.0,2.0,19.0),
)
SCALES = (462,4623,46230)
WORLDS=200
SEED=2026100822
GRID_INTERVALS=16384
SITES=82
PAIRS=41
CELL_DENOMINATOR=PAIRS*6
TRAIN_IDX=np.array(list(range(20))+list(range(41,61)),dtype=int)
TEST_IDX=np.array(list(range(20,41))+list(range(61,82)),dtype=int)


def verify_frozen(plan:Mapping[str,object])->None:
    event=plan.get("event_sampling",{})
    station=plan.get("station_design",{})
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!="FROZEN_METHOD_AND_SCENARIOS_BEFORE_FIRST_SIMULATION_OUTCOME"
        or plan.get("parent_preoutcome_41_smooth_pr")!=234
        or plan.get("original_pair_count")!=41
        or plan.get("solar_geometry")!={"lat":36.85,"lon":129.2,
             "year":2022,"timezone":"Asia/Seoul",
             "exact_station_coordinates_used":False}
        or plan.get("profiles")!=[
            {"name":n,"amplitude":a,"kappa":k,"peak":p}
            for n,a,k,p in PROFILES]
        or event.get("synthetic_mean_total_events")!=list(SCALES)
        or event.get("worlds_per_scenario")!=WORLDS
        or event.get("seed")!=SEED
        or event.get("inverse_cdf_grid_intervals")!=GRID_INTERVALS
        or station.get("total_stations")!=SITES
        or station.get("pairs_per_station")!=PAIRS
        or station.get("training_station_indices")!="0-19 and 41-60"
        or station.get("test_station_indices")!="20-40 and 61-81"
        or plan.get("model",{}).get("penalty_lambda")!=2
        or plan.get("model",{}).get("intercept_ridge")!=1e-6
        or plan.get("model",{}).get("selection_rule")!=
          "choose shape only if test-site-equal mean heldout gain >0"
        or plan.get("source_access",None) is not None
        and plan["source_access"]!={"animal_events":False}
        or plan.get("qualification",{}).get("no_source_record_access") is not True
    ):
        raise ValueError("frozen synthetic selection panel contract mismatch")


def phase_intensity(phi:np.ndarray,profile:tuple[str,float,float,float]
                   )->np.ndarray:
    _,amp,kappa,peak=profile
    return 1.+amp*np.exp(kappa*(np.cos(2*np.pi*(phi-peak)/24.)-1.))


def inverse_cdf_table(profile:tuple[str,float,float,float]
                     )->tuple[np.ndarray,np.ndarray]:
    grid=np.linspace(0.,24.,GRID_INTERVALS+1)
    f=phase_intensity(grid,profile)
    steps=.5*(f[1:]+f[:-1])*(24/GRID_INTERVALS)
    cdf=np.r_[0.,np.cumsum(steps)]
    cdf/=cdf[-1]
    return cdf,grid


def geometry_for_pairs(date_pairs:list[dict])->np.ndarray:
    if len(date_pairs)!=PAIRS:
        raise ValueError("use original all 41 paired dates")
    matrix=np.empty((PAIRS,2,2),dtype=float)
    for i,p in enumerate(date_pairs):
        for b,field in enumerate(("ascending_date","descending_date")):
            dt=date.fromisoformat(p[field])
            g=civil_solar_geometry(dt,36.85,129.2)
            matrix[i,b,0]=g["sunrise_clock_minute"]/60
            matrix[i,b,1]=g["sunset_clock_minute"]/60
    return matrix


def phase_to_civil_numpy(phi:np.ndarray, sr:np.ndarray,ss:np.ndarray
                         )->np.ndarray:
    """Exact existing two-anchor solar-phase inverse, vectorized and periodic."""
    daylight=ss-sr
    night=24.-daylight
    early=ss+(phi+6.)*night/12.-24.
    middle=sr+(phi-6.)*daylight/12.
    late=ss+(phi-18.)*night/12.
    return np.mod(np.where(phi<6,early,np.where(phi<18,middle,late)),24.)


def event_count_frames(
    rng:np.random.Generator,
    mean_events:int,
    pair_geometry:np.ndarray,
    cdf:np.ndarray,
    grid:np.ndarray,
)->tuple[np.ndarray,np.ndarray,int]:
    """Counts indexed [physical site, branch, six-bin]; same latent events."""
    total=int(rng.poisson(mean_events))
    site=rng.integers(0,SITES,total)
    pair=rng.integers(0,PAIRS,total)
    branch=rng.integers(0,2,total)
    phase=np.interp(rng.random(total),cdf,grid)
    sr=pair_geometry[pair,branch,0]
    ss=pair_geometry[pair,branch,1]
    clock=phase_to_civil_numpy(phase,sr,ss)
    solar_bin=np.minimum(5,np.floor(phase/4.).astype(int))
    clock_bin=np.minimum(5,np.floor(clock/4.).astype(int))
    # Explicitly preserve the ORIGINAL station x date-pair x branch frame.
    # Conditionally sufficient sums over 41 pairs are taken only AFTER
    # verifying same-event identity at each independent original pair.
    base=((site*PAIRS+pair)*2+branch)*6
    frame_shape=(SITES,PAIRS,2,6)
    solar_pairs=np.bincount(base+solar_bin,
                            minlength=SITES*PAIRS*2*6).reshape(frame_shape)
    civil_pairs=np.bincount(base+clock_bin,
                            minlength=SITES*PAIRS*2*6).reshape(frame_shape)
    if not np.array_equal(solar_pairs.sum(axis=3),
                          civil_pairs.sum(axis=3)):
        raise ValueError("different events across the time projections")
    solar=solar_pairs.sum(axis=1)
    civil=civil_pairs.sum(axis=1)
    if int(solar.sum())!=total or int(civil.sum())!=total:
        raise ValueError("projecting timestamps lost events")
    return civil,solar,total


def _fit_sufficient(counts:np.ndarray,allow_shape:bool
                    )->tuple[float,...]:
    if counts.shape!=(2,6):
        raise ValueError("model input requires both date branches and six bins")
    rows=[MirrorCountCell(
        station="UJ1_SYNTHETIC_TRAIN_COLLAPSED",
        region="UJ1",taxon="synthetic",pair_id="collapsed_41_pairs",
        clock_bin=k,rising_count=int(counts[0,k]),
        falling_count=int(counts[1,k]),
        rising_active_hours=4.,falling_active_hours=4.)
        for k in range(6)]
    model=fit_conditional_branch_model(rows,allow_branch_shape=allow_shape)
    return model.six_branch_log_rate_ratios


def heldout_site_equal_gain(counts:np.ndarray)->float:
    """Train on fixed sites, score different sites; no event-selected roster."""
    if counts.shape!=(SITES,2,6) or np.any(counts<0):
        raise ValueError("only full fixed original station frame is permitted")
    training=counts[TRAIN_IDX].sum(axis=0)
    beta0=np.array(_fit_sufficient(training,False))
    beta1=np.array(_fit_sufficient(training,True))
    heldout=counts[TEST_IDX].astype(float)
    falling=heldout[:,1,:]
    totals=heldout.sum(axis=1)
    # Coefficients for all six bins; cell-wise binomial factorial cancels.
    delta=falling*(beta1-beta0)-totals*(
        np.logaddexp(0.,beta1)-np.logaddexp(0.,beta0))
    per_station=delta.sum(axis=1)/CELL_DENOMINATOR
    return float(per_station.mean())


def run_one_synthetic_world(
    profile:tuple[str,float,float,float],
    scale:int,
    profile_index:int,scale_index:int,world_index:int,
    geometry:np.ndarray,cdf:np.ndarray,grid:np.ndarray
)->dict[str,object]:
    rng=np.random.default_rng(np.random.SeedSequence(
        [SEED,profile_index,scale_index,world_index]))
    civil,solar,n=event_count_frames(rng,scale,geometry,cdf,grid)
    civil_gain=heldout_site_equal_gain(civil)
    solar_gain=heldout_site_equal_gain(solar)
    return {
        "events":n,
        "civil_gain_nats_per_original_site_cell":civil_gain,
        "solar_gain_nats_per_original_site_cell":solar_gain,
        "civil_shape_selected":civil_gain>0,
        "solar_shape_selected":solar_gain>0,
        "clock_only_selection":civil_gain>0 and solar_gain<=0,
    }


def run_frozen_finite_sample_panel(
    calendar_contract:Mapping[str,object],
    panel_contract:Mapping[str,object],
    *,_test_world_count:int|None=None,
)->dict[str,object]:
    verify_frozen(panel_contract)
    dates=generate_preoutcome_2022_mirror_calendar(calendar_contract)["matched_dates"]
    if (len(dates)!=PAIRS
        or len({x["ascending_date"] for x in dates})!=PAIRS
        or len({x["descending_date"] for x in dates})!=PAIRS):
        raise ValueError("the original 41 pair date roster is required")
    geom=geometry_for_pairs(dates)
    n_worlds=WORLDS if _test_world_count is None else _test_world_count
    if not isinstance(n_worlds,int) or not 1<=n_worlds<=WORLDS:
        raise ValueError("test world count must be positive and <= frozen number")
    cases=[]
    for i,profile in enumerate(PROFILES):
        cdf,grid=inverse_cdf_table(profile)
        for j,scale in enumerate(SCALES):
            worlds=[run_one_synthetic_world(profile,scale,i,j,k,geom,cdf,grid)
                    for k in range(n_worlds)]
            clock=np.array([w["civil_gain_nats_per_original_site_cell"] for w in worlds])
            solar=np.array([w["solar_gain_nats_per_original_site_cell"] for w in worlds])
            clock_select=np.array([w["civil_shape_selected"] for w in worlds])
            solar_select=np.array([w["solar_shape_selected"] for w in worlds])
            clock_only=np.array([w["clock_only_selection"] for w in worlds])
            p=float(clock_only.mean())
            cases.append({
                "profile":profile[0],"total_expected_events":scale,
                "replicates":n_worlds,
                "observed_mean_simulated_events":float(np.mean([w["events"] for w in worlds])),
                "clock_only_selection_count":int(clock_only.sum()),
                "clock_only_selection_frequency":p,
                "clock_only_monte_carlo_se":math.sqrt(p*(1.-p)/n_worlds),
                "clock_shape_selection_frequency":float(clock_select.mean()),
                "solar_shape_selection_frequency":float(solar_select.mean()),
                "mean_clock_gain_nats_per_original_site_cell":float(clock.mean()),
                "mean_solar_gain_nats_per_original_site_cell":float(solar.mean()),
                "median_paired_clock_minus_solar_gain":
                    float(np.median(clock-solar)),
            })
    return {
        "schema_version":1,
        "method":ID,
        "status":"SOURCE_FREE_FINITE_SAMPLE_DESCRIPTIVE_SELECTION_ONLY",
        "frozen_worlds_per_case":WORLDS,
        "worlds_per_case_executed":n_worlds,
        "case_count":len(cases),
        "unique_physical_synthetic_sites":SITES,
        "original_unchanged_date_pairs":PAIRS,
        "clock_and_solar_use_identical_simulated_events":True,
        "rule_is_not_a_calibrated_hypothesis_test":True,
        "cases":cases,
        "real_animal_events_accessed":False,
        "real_device_uptime_accessed":False,
        "existing_qualified_ODSP_routes_modified":False,
    }
