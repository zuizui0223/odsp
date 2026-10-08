"""EXACT source-free solar-phase exposure from original hardware clock intervals.

Given a fixed astronomical context (sunrise sr, sunset ss), the original
two-anchor map phi(t) is piecewise affine with day Jacobian 12/(ss-sr)
and night Jacobian 12/(24-(ss-sr)). For a camera-operating subset A of
the civil-clock 24h day, exposure of each 4h SOLAR-PHASE bin k is

    E_k = integral_{t in A, phi(t) in [4k,4(k+1))}
                    dphi(t)/dt dt.

This transforms both the EFFORT MEASURE and the eventual event times.
It does not merely relabel animal events while retaining civil-clock
hours as the exposure offset, which would be mathematically wrong.

Source context is the paper's generalized Uljin region coordinate, NOT
restricted camera GPS. Synthetic intervals only; the real v1.1 EcoBank
operation log has not been acquired or authenticated.
"""
from __future__ import annotations

from datetime import date
import math
from typing import Sequence,Mapping

from .uljin_original_pairs_equation_of_time_v0 import civil_solar_geometry

METHOD="uljin_exact_original_mirror_solar_phase_uptime_v0"


def _sun(day:date,lat:float=36.85,lon:float=129.2)->tuple[float,float]:
    if not isinstance(day,date) or day.year!=2022 or lat!=36.85 or lon!=129.2:
        raise ValueError("only fixed source-free public 2022 representative solar context")
    astro=civil_solar_geometry(day,lat,lon)
    sr=astro["sunrise_clock_minute"]/60
    ss=astro["sunset_clock_minute"]/60
    if not 0<sr<ss<24:
        raise ValueError("solar sunrise and sunset outside one civil day")
    return sr,ss


def _inverse_unwrapped(phi:float,sr:float,ss:float)->float:
    daylight=ss-sr
    night=24-daylight
    if phi<6:
        return ss+(phi+6)*night/12-24
    if phi<18:
        return sr+(phi-6)*daylight/12
    return ss+(phi-18)*night/12


def clock_to_phase(clock_hour:float,day:date)->float:
    sr,ss=_sun(day)
    if not isinstance(clock_hour,(int,float)) or not math.isfinite(clock_hour) or not 0<=clock_hour<24:
        raise ValueError("civil-clock hour outside original daily support")
    if sr<=clock_hour<ss:
        return 6+12*(clock_hour-sr)/(ss-sr)
    adjusted=clock_hour if clock_hour>=ss else clock_hour+24
    return (18+12*(adjusted-ss)/(24-(ss-sr)))%24


def phase_to_clock(phase_hour:float,day:date)->float:
    sr,ss=_sun(day)
    if not isinstance(phase_hour,(int,float)) or not math.isfinite(phase_hour) or not 0<=phase_hour<24:
        raise ValueError("solar-phase hour outside 24h circle")
    return _inverse_unwrapped(float(phase_hour),sr,ss)%24


def _uptime_intervals(intervals:Sequence[tuple[float,float]]
                     )->list[tuple[float,float]]:
    if not isinstance(intervals,(list,tuple)):
        raise ValueError("camera daytime operation intervals must be declared")
    good=[]
    for pair in intervals:
        if not isinstance(pair,(tuple,list)) or len(pair)!=2:
            raise ValueError("clock-hour camera interval should be a pair")
        a,b=pair
        if (any(isinstance(v,bool) or not isinstance(v,(int,float))
                or not math.isfinite(v) for v in (a,b))
            or not 0<=a<b<=24):
            raise ValueError("invalid original operation interval in [0,24]")
        good.append((float(a),float(b)))
    merged=[]
    for a,b in sorted(good):
        if merged and a<=merged[-1][1]:
            merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:
            merged.append((a,b))
    return merged


def solar_phase_operating_exposure(
    day:date,clock_operation_intervals:Sequence[tuple[float,float]],
)->tuple[float,...]:
    """Real civil operating intervals -> six correctly Jacobian-weighted solar hours.

    If the original operation source only reports functional NIGHTS or
    civil four-hour totals, it CANNOT be supplied to this function;
    a specific within-bin operating chronology is necessary to
    integrate the piecewise astronomical change of variable exactly.
    """
    sr,ss=_sun(day)
    operating=_uptime_intervals(clock_operation_intervals)
    exposures=[]
    for k in range(6):
        left,right=4*k,4*(k+1)
        pieces=[left]+[v for v in (6.,18.) if left<v<right]+[right]
        mass=0.
        for a,b in zip(pieces[:-1],pieces[1:]):
            t0=_inverse_unwrapped(a,sr,ss)
            t1=_inverse_unwrapped(b,sr,ss)
            if t1<=t0:
                raise ValueError("nonpositive phase-clock inverse Jacobian")
            jac=(b-a)/(t1-t0)
            for shift in (-24.,0.,24.):
                window_start,window_end=t0+shift,t1+shift
                for x,y in operating:
                    overlap=max(0.,min(window_end,y)-max(window_start,x))
                    mass+=overlap*jac
        if mass< -1e-9 or mass>4.+1e-9:
            raise ValueError("impossible phase operating exposure from original intervals")
        exposures.append(min(4.,max(0.,mass)))
    return tuple(exposures)


def phase_exposure_first_known_truth_control(
    original_plan:Mapping[str,object],
    synthetic_plan:Mapping[str,object],
)->dict[str,object]:
    if (
        synthetic_plan.get("schema_version")!=1
        or synthetic_plan.get("method_id")!=METHOD
        or synthetic_plan.get("original_pairs")!=41
        or synthetic_plan.get("status")!=
        "SOURCE_FREE_ASTRONOMICAL_EXPOSURE_TRANSFORMATION_THEORY_BEFORE_SYNTHETIC_RESULTS"
        or synthetic_plan.get("transformation",{}).get("full_day_phase_bin_exposure_hours")!=4
    ):
        raise ValueError("frozen source-free solar-exposure design changed")
    from .uljin_photoperiod_mirror_design_v0 import generate_preoutcome_2022_mirror_calendar
    original=generate_preoutcome_2022_mirror_calendar(original_plan)
    if len(original["matched_dates"])!=41:
        raise ValueError("original 41 date pairs must not be rematched")
    example=synthetic_plan["theoretical_control"]["frozen_example_pair"]
    selected=next((p for p in original["matched_dates"]
                   if [p["ascending_date"],p["descending_date"]]==example),None)
    if selected is None:
        raise ValueError("frozen example date pair is not original matched pair")
    a,b=(date.fromisoformat(x) for x in example)
    full=[(0.,24.)]
    sr,ss=_sun(a)
    full_a=solar_phase_operating_exposure(a,full)
    full_b=solar_phase_operating_exposure(b,full)
    daylight=solar_phase_operating_exposure(a,[(sr,ss)])
    # Phase chosen just before the 08:00 civil-time edge on rising date.
    # Same PHASE falls into the adjacent civil bin on descending date.
    first_clock=7.94
    solar_phase=clock_to_phase(first_clock,a)
    second_clock=phase_to_clock(solar_phase,b)
    if not (
        all(abs(x-4)<1e-9 for x in (*full_a,*full_b))
        and all(abs(x-y)<1e-9 for x,y in zip(daylight,(0,2,4,4,2,0)))
        and first_clock<8<=second_clock
    ):
        raise ValueError("frozen source-free solar-exposure known-truth control failed")
    return {
        "schema_version":1,
        "method":METHOD,
        "status":"PASS_SOURCE_FREE_SOLAR_PHASE_DEVICE_MEASURE",
        "original_unmodified_astronomy_pairs":41,
        "example_ascending_date":example[0],
        "example_descending_date":example[1],
        "full_day_phase_hours_ascending":list(full_a),
        "full_day_phase_hours_descending":list(full_b),
        "daylight_only_phase_hours_ascending":list(daylight),
        "same_solar_phase_example":solar_phase,
        "rising_civil_clock_hour":first_clock,
        "falling_civil_clock_hour":second_clock,
        "clock_bin_artifact_without_solar_geometry_control":True,
        "exact_station_coordinates_used":False,
        "real_camera_operation_intervals_read":False,
        "real_animal_source_events_read":False,
        "photoperiod_hysteresis_effect_estimated":False,
        "original_ODSP_primary_result_reclassified":False,
    }
