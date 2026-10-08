"""Astronomical equation-of-time control on ORIGINAL Uljin 41 mirror dates.

This is a deterministic POST-first-calendar, outcome-free diagnostic.
Equal astronomical day LENGTH does not imply equal CIVIL-CLOCK
sunrise/sunset/noon timing. Apparent solar noon depends on NOAA
equation of time and longitude. Within one fixed station, the
longitude/timezone terms CANCEL in a paired NOON TIME DIFFERENCE.

No real ungulate observations, camera uptime, station identities or
precise protected-animal locations are accessed. The original 41 pairs
and first calendar outcome remain unchanged.
"""
from __future__ import annotations

from datetime import date
import math
from typing import Any, Mapping

from .uljin_photoperiod_mirror_design_v0 import (
    apparent_daylength_hours,
    generate_preoutcome_2022_mirror_calendar,
)

ID="odsp-uljin-original-41-pairs-equation-of-time-diagnostic-v0"


def equation_of_time_minutes(day:date)->float:
    if not isinstance(day,date) or day.year!=2022:
        raise ValueError("frozen astronomical equation-of-time calendar is 2022")
    gamma=2.0*math.pi/365.0*(day.timetuple().tm_yday-1)
    return 229.18*(
        0.000075+0.001868*math.cos(gamma)
        -0.032077*math.sin(gamma)
        -0.014615*math.cos(2.0*gamma)
        -0.040849*math.sin(2.0*gamma)
    )


def civil_solar_geometry(
    day:date, latitude_degrees:float, longitude_degrees:float,
    utc_offset_hours:float=9.0,
)->dict[str,float]:
    if (not math.isfinite(latitude_degrees)
        or not math.isfinite(longitude_degrees)
        or not math.isfinite(utc_offset_hours)
        or not -180<=longitude_degrees<=180
        or utc_offset_hours!=9):
        raise ValueError("invalid public geographical context")
    dl=apparent_daylength_hours(day,latitude_degrees)
    eq=equation_of_time_minutes(day)
    noon=720.0-4.0*longitude_degrees-eq+60.0*utc_offset_hours
    return {
        "daylength_hours":dl,
        "equation_of_time_minutes":eq,
        "solar_noon_clock_minute":noon,
        "sunrise_clock_minute":noon-30.0*dl,
        "sunset_clock_minute":noon+30.0*dl,
    }


def _contract(plan:Mapping[str,object])->None:
    if (
        plan.get("schema_version")!=1
        or plan.get("contract_id")!=ID
        or plan.get("stage")!=
            "POST_FIRST_OUTCOME_FREE_ASTRONOMICAL_CALENDAR_SOURCE_FREE_SENSITIVITY"
        or plan.get("original_calendar_run_id")!=37771342454
        or plan.get("original_date_pairs_not_rematched") is not True
        or plan.get("latitude_degrees")!=36.85
        or plan.get("longitude_degrees")!=129.2
        or plan.get("timezone_standard_utc_offset_hours")!=9
        or plan.get("original_pair_count_required")!=41
        or plan.get("no_animal_records_accessed") is not True
    ):
        raise ValueError("frozen solar noon original date-pair contract changed")


def compare_original_41_mirror_noons(
    original_calendar_contract:Mapping[str,object],
    frozen_noon_contract:Mapping[str,object],
)->dict[str,Any]:
    _contract(frozen_noon_contract)
    calendar=generate_preoutcome_2022_mirror_calendar(
        original_calendar_contract
    )
    pairs=calendar["matched_dates"]
    if len(pairs)!=41:
        raise ValueError("original day-pair count changed")
    rows=[]
    latitude=36.85
    longitude=129.2
    for pair in pairs:
        first=date.fromisoformat(pair["ascending_date"])
        second=date.fromisoformat(pair["descending_date"])
        a=civil_solar_geometry(first,latitude,longitude)
        b=civil_solar_geometry(second,latitude,longitude)
        shift_noon=b["solar_noon_clock_minute"]-a["solar_noon_clock_minute"]
        shift_sunrise=b["sunrise_clock_minute"]-a["sunrise_clock_minute"]
        shift_sunset=b["sunset_clock_minute"]-a["sunset_clock_minute"]
        # The original solar-phase transformation maps sunrise/sunset
        # exactly to 06:00/18:00 by definition in BOTH seasons.
        rows.append({
            "ascending_date":pair["ascending_date"],
            "descending_date":pair["descending_date"],
            "daylength_difference_minutes":pair["daylength_difference_minutes"],
            "solar_noon_civil_shift_minutes":shift_noon,
            "sunrise_civil_shift_minutes":shift_sunrise,
            "sunset_civil_shift_minutes":shift_sunset,
            "sunrise_common_solar_phase_hour":6.0,
            "sunset_common_solar_phase_hour":18.0,
            "pair_has_matching_daylength_but_nonidentical_solar_noon":
                abs(shift_noon)>1e-10,
        })
    abs_noons=[abs(x["solar_noon_civil_shift_minutes"]) for x in rows]
    return {
        "schema_version":1,
        "method":"uljin_original_calendar_equation_of_time_design_v0",
        "status":"SOLAR_NOON_CLOCK_OFFSET_DESIGN_CONTROL_ONLY",
        "fixed_original_calendar_pairs":len(rows),
        "min_abs_solar_noon_clock_shift_minutes":min(abs_noons),
        "max_abs_solar_noon_clock_shift_minutes":max(abs_noons),
        "mean_abs_solar_noon_clock_shift_minutes":
            sum(abs_noons)/len(abs_noons),
        "max_abs_sunrise_clock_shift_minutes":max(
            abs(r["sunrise_civil_shift_minutes"]) for r in rows
        ),
        "max_abs_sunset_clock_shift_minutes":max(
            abs(r["sunset_civil_shift_minutes"]) for r in rows
        ),
        "all_original_mirror_dates_unchanged":True,
        "noon_difference_independent_of_fixed_station_longitude":True,
        "date_pairs":rows,
        "actual_station_sunrise_sunset_computed":False,
        "original_hourly_operating_effort_verified":False,
        "camera_or_ungulate_records_read":False,
        "ecological_hysteresis_effect_measured":False,
        "original_41_calendar_result_or_ODSP_inference_reclassified":False,
    }
