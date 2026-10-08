"""Outcome-free astronomical date pairs for a new Korean camera-trap study.

This is NOT a reanalysis of Rhode Island and accesses NO event rows or
camera-operation logs. From a prior public study summary only, it enumerates
pairs of fixed, same-year 2022 dates with near-equal apparent daylength
on opposite photoperiod branches. The comparison is a SCIENTIFIC DESIGN:
a pure solar-phase invariance model predicts the same phase distribution
at equal daylength; an ascending/descending branch effect would demand
additional ecological or observational explanation.

Real deployment/uptime logs, observation timestamps, independent-site
sampling, species support and any photoperiod-hysteresis effect remain
UNVERIFIED. Never label astronomical date matches as matched camera events.
"""
from __future__ import annotations

from dataclasses import asdict,dataclass
from datetime import date,timedelta
import math
from typing import Any,Mapping

PLAN_ID="odsp-uljin-2022-photoperiod-mirror-structural-design-v0"


def apparent_daylength_hours(
    day:date,
    latitude_degrees:float,
    *,
    apparent_zenith_degrees:float=90.833,
)->float:
    """Approximate sunrise-to-sunset length using standard NOAA declination.

    Daylength depends on declination, solar zenith, and latitude; NOT the
    zone offset or longitude. It is purely astronomical context, never an
    operational effort measure or measured animal activity.
    """
    if not isinstance(day,date):
        raise ValueError("day must be datetime.date")
    if (not isinstance(latitude_degrees,(float,int))
        or isinstance(latitude_degrees,bool)
        or not math.isfinite(float(latitude_degrees))
        or abs(latitude_degrees)>=66.0):
        raise ValueError("this comparator admits nonpolar latitudes only")
    if apparent_zenith_degrees!=90.833:
        raise ValueError("frozen apparent-solar zenith differs")
    gamma=2.0*math.pi/365.0*(day.timetuple().tm_yday-1)
    decl=(
        .006918-.399912*math.cos(gamma)+.070257*math.sin(gamma)
        -.006758*math.cos(2*gamma)+.000907*math.sin(2*gamma)
        -.002697*math.cos(3*gamma)+.00148*math.sin(3*gamma)
    )
    phi=math.radians(float(latitude_degrees))
    cos_h=(
        math.cos(math.radians(apparent_zenith_degrees))/
        (math.cos(phi)*math.cos(decl))
        -math.tan(phi)*math.tan(decl)
    )
    if not -1.0<cos_h<1.0:
        raise ValueError("sun never rises or sets at this site/date")
    hour_angle_degrees=math.degrees(math.acos(cos_h))
    return 2.0*hour_angle_degrees/15.0


def _window(start:str,end:str)->tuple[date,...]:
    a,b=date.fromisoformat(start),date.fromisoformat(end)
    if a>b or (b-a).days>366:
        raise ValueError("invalid fixed calendar window")
    return tuple(a+timedelta(days=i) for i in range((b-a).days+1))


@dataclass(frozen=True)
class PhotoperiodMirrorDatePair:
    ascending_date:str
    descending_date:str
    ascending_daylength_hours:float
    descending_daylength_hours:float
    daylength_difference_minutes:float
    calendar_gap_days:int

    def as_dict(self)->dict[str,Any]:
        return asdict(self)


def _precommitted_contract(plan:Mapping[str,object])->Mapping[str,object]:
    if (not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=PLAN_ID
        or plan.get("status")!="SCIENTIFIC_SOURCE_DESIGN_DISCOVERY_ONLY_UNQUALIFIED"):
        raise ValueError("unrecognized photoperiod mirror structural plan")
    d=plan.get("preoutcome_structural_pairing",{})
    frozen={
        "source_year":2022,
        "latitude_for_public_solar_geometry":36.85,
        "longitude_for_public_context":129.2,
        "ascending_window_start":"2022-05-01",
        "ascending_window_end":"2022-06-10",
        "descending_window_start":"2022-07-01",
        "descending_window_end":"2022-08-31",
        "one_to_one_nonreused_day_pairs":True,
        "pair_absolute_daylength_difference_max_hours":.15,
        "pair_min_calendar_separation_days":21,
        "pair_algorithm":"globally sort all eligible (abs(daylength difference),ascending_date,descending_date) triples and greedily accept pairs without replacement",
        "sunrise_sunset_definition":"NOAA apparent zenith=90.833°, fractional-year declination approximation at local noon",
        "only_published_general_site_coordinates_for_solar_geometry":True,
        "no_detection_rows_needed_to_generate_calendar_pairs":True,
    }
    if not isinstance(d,Mapping) or any(d.get(k)!=v for k,v in frozen.items()):
        raise ValueError("photoperiod pairing rules differ from frozen design")
    if plan.get("preoutcome_feasibility_gates",{}).get(
        "exact_operating_time_by_local_clock_category_required"
    ) is not True:
        raise ValueError("camera-hour effort provenance guard absent")
    return d


def generate_preoutcome_2022_mirror_calendar(
    plan:Mapping[str,object],
)->dict[str,Any]:
    """Deterministic public ASTRONOMICAL support, no wildlife source opened."""
    d=_precommitted_contract(plan)
    phi=d["latitude_for_public_solar_geometry"]
    asc=_window(d["ascending_window_start"],d["ascending_window_end"])
    desc=_window(d["descending_window_start"],d["descending_window_end"])
    a={day:apparent_daylength_hours(day,phi) for day in asc}
    b={day:apparent_daylength_hours(day,phi) for day in desc}
    candidates=[]
    for d1,v1 in a.items():
        for d2,v2 in b.items():
            gap=(d2-d1).days
            error=abs(v1-v2)
            if (gap>=d["pair_min_calendar_separation_days"]
                and error<=d["pair_absolute_daylength_difference_max_hours"]):
                candidates.append((error,d1,d2,gap))
    candidates.sort(key=lambda x:(x[0],x[1],x[2]))
    used_a=set()
    used_b=set()
    matching=[]
    for error,d1,d2,gap in candidates:
        if d1 in used_a or d2 in used_b:
            continue
        used_a.add(d1)
        used_b.add(d2)
        matching.append(PhotoperiodMirrorDatePair(
            ascending_date=d1.isoformat(),
            descending_date=d2.isoformat(),
            ascending_daylength_hours=a[d1],
            descending_daylength_hours=b[d2],
            daylength_difference_minutes=error*60.0,
            calendar_gap_days=gap,
        ))
    matching.sort(key=lambda p:p.ascending_date)
    return {
        "schema_version":1,
        "method_version":"uljin_photoperiod_mirror_astronomy_design_v0",
        "status":"PREDECLARED_ASTRONOMICAL_DATE_PAIR_CATALOG_ONLY",
        "published_study_region_rep_latitude":phi,
        "public_source_reference":"10.3897/BDJ.14.e191556",
        "two_region_cluster_warning":True,
        "candidate_ascending_dates":len(asc),
        "candidate_descending_dates":len(desc),
        "all_predeclared_eligible_date_edges":len(candidates),
        "selected_nonoverlapping_calendar_day_pairs":len(matching),
        "worst_matched_daylength_discrepancy_minutes":(
            max(x.daylength_difference_minutes for x in matching)
            if matching else None
        ),
        "matched_dates":[x.as_dict() for x in matching],
        "source_operational_log_or_animal_events_accessed":False,
        "actual_station_pairwise_observation_support_verified":False,
        "active_camera_hourly_effort_verified":False,
        "taxon_detection_density_computed":False,
        "temperature_or_biotic_context_measured":False,
        "hysteresis_effect_in_wildlife_inferred":False,
        "previous_RI_or_ODSP_ecological_result_reclassified":False,
    }
