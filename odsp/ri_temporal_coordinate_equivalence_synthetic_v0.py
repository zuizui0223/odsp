"""Continuous circular-time clock/solar coordinate equivalence and invariance.

SYNTHETIC/THEORETICAL ONLY: no archive, detection labels, empirical RI
scores, site selection, model fit, or change to any frozen ODSP route.

For civil time t on a 24h circle, site/date context z, and the original
piecewise affine solar phase phi_z(t), J_z(t)=d phi_z(t)/dt>0:

    f_clock(t|z) = g_solar(phi_z(t)|z)*J_z(t).

The Jacobian is REQUIRED if both models receive a proper continuous log
density score on the *same civil-clock t*. Conversely,

    g_solar(phi|z) = f_clock(phi_z^{-1}(phi)|z)*
                     d phi_z^{-1}(phi)/d phi.

If either model is allowed arbitrary context-specific densities, the
two representations define exactly the same prediction family: a
change of coordinates cannot by itself identify the animal's clock.

If SOLAR phase density must be constant across dates while CLOCK time
density must be constant across dates, those become competing
testable invariance assumptions. Here we evaluate ideal population-
optimal pooled references under two known-truth synthetic alternatives.

Unlike the historical six-bin RI analysis, this calculation has no
finite solar-bin-to-clock-bin stochastic mixing matrix, so it never
fabricates a clock-bin representational ceiling via binning.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from typing import Any, Callable, Mapping

import numpy as np

from .ri_solar_clock_transfer_v0 import sunrise_sunset_local

METHOD_VERSION="ri_temporal_coordinate_equivalence_synthetic_v0"
SEASONS=("winter","summer")
HOURS=24.0
EPS=1e-300


@dataclass(frozen=True)
class AstronomicalContext:
    """Solar geometry, not sampled ecological data."""
    label: str
    day: date
    latitude: float
    longitude: float
    sunrise: float
    sunset: float

    @classmethod
    def from_day(cls,label:str,day:date,latitude:float,longitude:float):
        if label not in SEASONS:
            raise ValueError("unsupported source-free synthetic season label")
        sr,ss=sunrise_sunset_local(day,latitude,longitude)
        return cls(label,day,latitude,longitude,sr,ss)


def _geometry(ctx:AstronomicalContext)->tuple[float,float]:
    if not isinstance(ctx,AstronomicalContext):
        raise ValueError("astronomical context is required")
    sr,ss=ctx.sunrise,ctx.sunset
    if not (
        all(math.isfinite(v) for v in (sr,ss))
        and 0.0<sr<ss<24.0
    ):
        raise ValueError("unsupported solar geometry")
    return ss-sr, 24.0-(ss-sr)


def _hours(value:np.ndarray|float,name:str)->np.ndarray:
    v=np.asarray(value,dtype=float)
    if not np.isfinite(v).all() or np.any(v<0) or np.any(v>=24):
        raise ValueError(f"{name} must be within [0,24) hours")
    return v


def solar_phase_and_clock_jacobian(
    civil_hour: np.ndarray|float,
    context:AstronomicalContext,
)->tuple[np.ndarray,np.ndarray]:
    """Forward circular change of variables and positive exact Jacobian."""
    t=_hours(civil_hour,"civil time")
    daylight,night=_geometry(context)
    sr,ss=context.sunrise,context.sunset
    day=(t>=sr)&(t<ss)
    phase=np.where(
        day,
        6.0+12.0*(t-sr)/daylight,
        (18.0+12.0*np.mod(t-ss,24.0)/night)%24.0,
    )
    jac=np.where(day,12.0/daylight,12.0/night)
    return np.mod(phase,24.0),np.asarray(jac)


def clock_time_and_inverse_jacobian(
    phase_hour:np.ndarray|float,
    context:AstronomicalContext,
)->tuple[np.ndarray,np.ndarray]:
    """Exact inverse solar phase and derivative of civil time wrt phase."""
    phi=_hours(phase_hour,"solar phase")
    daylight,night=_geometry(context)
    sr,ss=context.sunrise,context.sunset
    t=np.where(
        phi<6.0,
        ss+(phi+6.0)*night/12.0-24.0,
        np.where(
            phi<18.0,
            sr+(phi-6.0)*daylight/12.0,
            ss+(phi-18.0)*night/12.0,
        ),
    )
    day=(phi>=6.0)&(phi<18.0)
    inverse=np.where(day,daylight/12.0,night/12.0)
    return np.mod(t,24.0),np.asarray(inverse)


def von_mises_hour_density(
    hours:np.ndarray|float,
    *,
    peak_hour:float=7.5,
    concentration:float=2.2,
)->np.ndarray:
    """Smooth strictly positive normalized 24h circular reference density."""
    h=_hours(hours,"density evaluation time")
    if (
        not math.isfinite(peak_hour) or not 0<=peak_hour<24
        or not math.isfinite(concentration) or concentration<0
        or concentration>20
    ):
        raise ValueError("invalid synthetic circular reference density")
    theta=(2.0*math.pi/24.0)*(h-peak_hour)
    return np.exp(concentration*np.cos(theta))/(
        24.0*np.i0(concentration)
    )


def time_grid(n:int=24000)->tuple[np.ndarray,float]:
    if isinstance(n,bool) or not isinstance(n,int) or n<2400 or n%24!=0:
        raise ValueError("integration grid must be >=2400 and multiple of 24")
    delta=24.0/n
    return (np.arange(n,dtype=float)+0.5)*delta,delta


def clock_density_from_solar(
    clock_hours:np.ndarray,
    context:AstronomicalContext,
    solar_density:Callable[[np.ndarray],np.ndarray],
)->np.ndarray:
    phase,jac=solar_phase_and_clock_jacobian(clock_hours,context)
    source=np.asarray(solar_density(phase),dtype=float)
    if source.shape!=phase.shape or not np.isfinite(source).all() or np.any(source<=0):
        raise ValueError("solar conditional density must be strictly positive finite and aligned")
    return source*jac


def solar_density_from_clock(
    phase_hours:np.ndarray,
    context:AstronomicalContext,
    clock_density:Callable[[np.ndarray],np.ndarray],
)->np.ndarray:
    clock,inverse=clock_time_and_inverse_jacobian(phase_hours,context)
    source=np.asarray(clock_density(clock),dtype=float)
    if source.shape!=phase_hours.shape or not np.isfinite(source).all() or np.any(source<=0):
        raise ValueError("clock conditional density must be strictly positive finite and aligned")
    return source*inverse


def expected_log_density_gain(
    truth:np.ndarray,
    candidate:np.ndarray,
    reference:np.ndarray,
    clock_grid_step:float,
)->float:
    """Known-population expected proper-log-density difference, not a test."""
    a,b,c=(np.asarray(x,dtype=float) for x in (truth,candidate,reference))
    if (a.shape!=b.shape or a.shape!=c.shape
        or a.ndim!=1 or not a.size
        or any(not np.isfinite(x).all() or np.any(x<=0) for x in (a,b,c))
        or not math.isfinite(clock_grid_step) or clock_grid_step<=0):
        raise ValueError("invalid source-free expected-score inputs")
    return float(clock_grid_step*np.sum(
        a*(np.log(b)-np.log(c))
    ))


def _validate_synthetic_plan(plan:Mapping[str,object])->dict[str,Any]:
    if (not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=
          "odsp_temporal_coordinate_identifiability_and_capacity_v0"
        or plan.get("status")!=
          "SYNTHETIC_THEORY_ONLY_POST_RI_EMPIRICAL_RESULTS"):
        raise ValueError("unrecognized preregistered synthetic coordinate test")
    p=plan.get("synthetic_plan",{})
    if (
        p.get("astronomical_latitude")!=41.5
        or p.get("astronomical_longitude")!=-71.5
        or p.get("winter_date")!="2022-12-21"
        or p.get("summer_date")!="2022-06-21"
        or p.get("independent_context_weights")!=[.5,.5]
        or p.get("numerical_midpoint_grid_points")!=24000
        or p.get("von_mises_concentration")!=2.2
        or p.get("von_mises_peak_clock_or_phase_hour")!=7.5
        or p.get("tolerance_mass")!=.002
        or p.get("never_compute_empirical_ri_effect_or_revise_frozen_results")
            is not True
    ):
        raise ValueError("frozen synthetic sample/score design was changed")
    return p


def synthetic_population_coordinate_test(
    frozen_plan:Mapping[str,object],
)->dict[str,Any]:
    """Two KNOWN-truth worlds under exact continuous phase transport.

    For solar truth g(phi) shared across contexts:
       f_z(t)=g(phi_z(t))*J_z(t),
    the best pooled unrestricted civil-clock density across two equally
    weighted seasons is f_pool(t)=.5*(f_winter(t)+f_summer(t)).

    For clock truth f(t) shared across contexts, the optimal pooled
    solar-phase density is the mixture of transformed clock densities:
       g_pool(phi)=.5*(f(t_winter(phi))*t'_winter(phi)
                         +f(t_summer(phi))*t'_summer(phi)).

    This isolates which INVARIANCE constraint is correct; it does not
    claim that equal Fourier coefficients/equal histogram bin counts
    imply equal observational predictive capacity.
    """
    design=_validate_synthetic_plan(frozen_plan)
    ctxs=tuple(AstronomicalContext.from_day(
        name,date.fromisoformat(design[f"{name}_date"]),41.5,-71.5
    ) for name in SEASONS)
    grid,dt=time_grid(24000)
    density=lambda h: von_mises_hour_density(
        h,peak_hour=7.5,concentration=2.2
    )
    reference=density(grid)
    # A: true activity/detection model is invariant in SOLAR phase.
    solar_truth=[
        clock_density_from_solar(grid,z,density) for z in ctxs
    ]
    best_pooled_clock=.5*(solar_truth[0]+solar_truth[1])
    solar_truth_gains=[
        expected_log_density_gain(y,y,best_pooled_clock,dt)
        for y in solar_truth
    ]
    # B: true activity/detection model is invariant in CIVIL clock time.
    phase_grid,_=time_grid(24000)
    optimal_pooled_solar_phase=.5*(
        solar_density_from_clock(phase_grid,ctxs[0],density)+
        solar_density_from_clock(phase_grid,ctxs[1],density)
    )
    # Evaluate optimal pooled solar phase at arbitrary civil clock phases
    # from EXACT analytic inverse densities, no interpolation artefacts.
    def optimal_solar_density(phi:np.ndarray)->np.ndarray:
        return .5*(
            solar_density_from_clock(phi,ctxs[0],density)+
            solar_density_from_clock(phi,ctxs[1],density)
        )
    clock_truth_solar_predictions=[
        clock_density_from_solar(grid,z,optimal_solar_density)
        for z in ctxs
    ]
    clock_truth_clock_gains=[
        expected_log_density_gain(reference,reference,candidate,dt)
        for candidate in clock_truth_solar_predictions
    ]
    mass={
        "clock_reference":float(dt*np.sum(reference)),
        "solar_truth_winter":float(dt*np.sum(solar_truth[0])),
        "solar_truth_summer":float(dt*np.sum(solar_truth[1])),
        "best_pooled_clock_under_solar_truth":float(dt*np.sum(best_pooled_clock)),
        "best_pooled_solar_phase_under_clock_truth":float(
            dt*np.sum(optimal_pooled_solar_phase)
        ),
        "solar_projection_winter_under_clock_truth":float(
            dt*np.sum(clock_truth_solar_predictions[0])
        ),
        "solar_projection_summer_under_clock_truth":float(
            dt*np.sum(clock_truth_solar_predictions[1])
        ),
    }
    tol=design["tolerance_mass"]
    if any(abs(v-1.0)>tol for v in mass.values()):
        raise ValueError("continuous probability mass not conserved")
    return {
        "schema_version":1,
        "method_version":METHOD_VERSION,
        "status":"KNOWN_TRUTH_SYNTHETIC_COORDINATE_INVARIANCE",
        "contexts":[{
            "name":z.label,"day":z.day.isoformat(),
            "sunrise_local_hour":z.sunrise,
            "sunset_local_hour":z.sunset
        } for z in ctxs],
        "known_solar_invariant_truth":{
            "expected_nats_advantage_of_correct_solar_over_optimal_pooled_clock":
                {name:gain for name,gain in zip(SEASONS,solar_truth_gains)},
            "equal_context_mean_advantage":float(np.mean(solar_truth_gains)),
        },
        "known_clock_invariant_truth":{
            "expected_nats_advantage_of_correct_clock_over_optimal_pooled_solar":
                {name:gain for name,gain in zip(SEASONS,clock_truth_clock_gains)},
            "equal_context_mean_advantage":float(np.mean(clock_truth_clock_gains)),
        },
        "numerical_density_mass":mass,
        "same_civil_clock_continuous_density_target":True,
        "correct_solar_clock_jacobian_used":True,
        "solar_histogram_clock_bin_convex_hull_limit_imposed":False,
        "context_unrestricted_density_families_equivalent":True,
        "testable_difference_is_context_invariance_not_coordinate_name":True,
        "real_RI_wildlife_detection_rows_accessed":False,
        "empirical_solar_vs_clock_gain_computed":False,
        "causal_photoperiod_mechanism_identified":False,
        "previous_v2_ecological_result_reclassified":False,
        "any_ODSP_qualified_inference_modified":False,
    }



def detected_density_from_activity_and_effort(
    activity_density:np.ndarray,
    detection_effort:np.ndarray,
    dt:float,
)->np.ndarray:
    """Observe a(t)*effort(t) normalized, not unobserved animal activity.

    Even if cameras record every detection without classification error,
    activity intensity and time-varying effort/detection remain confounded.
    """
    a=np.asarray(activity_density,dtype=float)
    e=np.asarray(detection_effort,dtype=float)
    if (
        a.ndim!=1 or a.shape!=e.shape or not a.size
        or not np.isfinite(a).all() or np.any(a<=0)
        or not np.isfinite(e).all() or np.any(e<0) or np.any(e>1)
        or not math.isfinite(dt) or dt<=0
    ):
        raise ValueError("invalid activity and device/detection effort")
    exposure=a*e
    mass=float(dt*np.sum(exposure))
    if mass<=0 or not math.isfinite(mass):
        raise ValueError("zero or invalid observation exposure")
    return exposure/mass


def effort_reconstructing_arbitrary_detected_density(
    observed_density:np.ndarray,
    alternate_activity_density:np.ndarray,
)->np.ndarray:
    """Explicit observational equivalence for *any* positive activities.

    Choose e(t)=c * observed(t)/activity(t), where
      c = (1/2) / max_t observed(t)/activity(t).
    Then 0<e<=0.5 and the normalized detected distribution exactly
    equals the observed distribution, despite different biological
    activity functions. The factor 1/2 is a harmless arbitrary scale.
    """
    d=np.asarray(observed_density,dtype=float)
    a=np.asarray(alternate_activity_density,dtype=float)
    if (
        d.ndim!=1 or d.shape!=a.shape or not d.size
        or not np.isfinite(d).all() or not np.isfinite(a).all()
        or np.any(d<=0) or np.any(a<=0)
    ):
        raise ValueError("strictly positive aligned activity densities required")
    ratio=d/a
    scale=.5/float(np.max(ratio))
    return scale*ratio
