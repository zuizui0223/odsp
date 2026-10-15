"""Ecological question, NOT another detector-q optimizer.

At 41 frozen equal-daylength pairs in 2022, compare the time-use
signature of four ungulates between late spring/early summer
(2022-05-01..06-10) and midsummer (2022-07-01..08-31).

The ecological responses are independently meaningful:
- daylight CORE vs combined two daylight EDGES: midday avoidance
- NIGHT vs all DAYLIGHT: nocturnal shift
- heterogeneity of those changes across four species: potential
  temporal niche reassembly, not evidence of species competition.

Original local civil event times are ALWAYS the response; solar
geometry only classifies externally defined ecological zones.
Without independently verified ORIGINAL source HOURLY operating
intervals, timestamps alone give no rate-based ecology. This
utility computes audit tables only; never fabricates source data
or treats site×date cells as independent regions.
"""
from __future__ import annotations

from collections import Counter,defaultdict
from collections.abc import Mapping,Sequence
from datetime import date
import math
import re

from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar
)
from .uljin_original_pairs_equation_of_time_v0 import civil_solar_geometry

METHOD="uljin_four_ungulates_equal_daylength_temporal_refuge_ecology_v0"
TAXA=("Goral","Water deer","Roe deer","Wild boar")
ZONES=("daylight_core","daylight_edge","night")
BRANCHES=("rising","falling")
GEO_LAT=36.85
GEO_LONG=129.2
MIN_EVENTS_EACH_BRANCH=30
MIN_STATIONS_BOTH_BRANCHES=8
_TIME=re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]:(?:[0-5][0-9])$")
_LOCAL_FIELDS=("Station","Species","Date","Time")


def assert_frozen_ecology(
    contract:Mapping[str,object],calendar:Mapping[str,object]
)->dict[str,str]:
    if not isinstance(contract,Mapping) or not isinstance(calendar,Mapping):
        raise ValueError("original frozen ecological question and calendar required")
    frame=contract.get("correct_calendar",{})
    cats=contract.get("zone_definitions",{})
    source=contract.get("real_data_admission",{})
    if (
        contract.get("schema_version")!=1
        or contract.get("contract_id")!=METHOD
        or contract.get("stage")!=
            "BIOLOGICAL_QUESTIONS_FROZEN_BEFORE_REAL_EVENT_AND_HOURLY_OPERATION_SOURCE_ADMISSION"
        or contract.get("species_predeclared")!=list(TAXA)
        or frame.get("original_41_unchanged_mirror_pairs") is not True
        or frame.get("early_growing_season_window")!=[
            "2022-05-01","2022-06-10"]
        or frame.get("late_growing_season_window")!=[
            "2022-07-01","2022-08-31"]
        or cats.get("solar_daylight_core")!=
            "Central HALF of sunrise-to-sunset daylight, [sunrise+0.25*daylength,sunrise+0.75*daylength), i.e. solar-phase 09:00–15:00."
        or source.get("source_operational_hour_precision_required") is not True
        or source.get("no_event_based_pair_or_species_filtering") is not True
    ):
        raise ValueError("original biological contrast, taxonomy or zone freeze altered")
    c=generate_preoutcome_2022_mirror_calendar(calendar)
    pairs=c["matched_dates"]
    if len(pairs)!=41:
        raise ValueError("not original 41 independent astronomy matched days")
    days={}
    for p in pairs:
        for b,k in (("rising","ascending_date"),
                    ("falling","descending_date")):
            day=p[k]
            if day in days:
                raise ValueError("date was reused between original matched pairs")
            days[day]=b
    if len(days)!=82:
        raise ValueError("not all 82 original astronomical dates preserved")
    return days


def parse_clock_minutes(value:str)->float:
    if not isinstance(value,str) or not _TIME.fullmatch(value):
        raise ValueError("require source local Asia/Seoul HH:MM:SS event clock")
    hour,minute,second=map(int,value.split(":"))
    return hour*60+minute+second/60


def solar_zone_bounds(day:date)->dict[str,list[tuple[float,float]]]:
    geom=civil_solar_geometry(day,GEO_LAT,GEO_LONG)
    sr=geom["sunrise_clock_minute"]
    ss=geom["sunset_clock_minute"]
    dl=ss-sr
    q1=sr+dl/4
    q3=sr+3*dl/4
    if not (0<sr<q1<q3<ss<24*60):
        raise ValueError("invalid source-generalized sunrise/sunset for day")
    return {
        "daylight_core":[(q1,q3)],
        "daylight_edge":[(sr,q1),(q3,ss)],
        "night":[(0.,sr),(ss,1440.)],
    }


def classify_event_time(day:date,minutes:float)->str:
    if not math.isfinite(minutes) or not 0<=minutes<1440:
        raise ValueError("invalid local detection time")
    bounds=solar_zone_bounds(day)
    for zone in ZONES:
        if any(a<=minutes<b for a,b in bounds[zone]):
            return zone
    raise ValueError("uncovered solar daypart boundary")


def solar_zone_operation_minutes(
    day:date,intervals:Sequence[tuple[float,float]]
)->dict[str,float]:
    """Allocate verified clock-hour operation to SOURCE day-zone durations.

    Intervals must already be normalized to one LOCAL calendar day
    from an independently authenticated camera operation log. Never
    fill unreported gaps or manufacture 24h from 'functional nights'.
    """
    if not isinstance(intervals,(tuple,list)):
        raise ValueError("require source-verified hourly operating intervals")
    values=[]
    for t in intervals:
        if (not isinstance(t,(tuple,list)) or len(t)!=2
            or not all(isinstance(x,(float,int)) and not isinstance(x,bool)
                       and math.isfinite(x) for x in t)
            or not 0<=t[0]<t[1]<=1440):
            raise ValueError("nonpositive or non-hour-verified operation interval")
        values.append((float(t[0]),float(t[1])))
    values.sort()
    if any(values[i][1]>values[i+1][0] for i in range(len(values)-1)):
        raise ValueError("overlapping camera operating intervals: do not double count")
    zones=solar_zone_bounds(day)
    result={
        label:sum(max(0.,min(right,e)-max(left,s))
                  for s,e in values
                  for left,right in boundaries)
        for label,boundaries in zones.items()
    }
    observed=sum(e-s for s,e in values)
    if abs(sum(result.values())-observed)>1e-8:
        raise ValueError("sunrise classification does not partition true operating hours")
    return result


def source_timestamp_audit(
    contract:Mapping[str,object],calendar:Mapping[str,object],
    source_event_rows:Sequence[Mapping[str,str]],
    *,
    source_member_verified:bool=False,
)->dict[str,object]:
    """No rate nor real ecological inference, only source event support.

    Does not require or fabricate daily camera operating intervals.
    HOLD if source original member is not authenticated. Also works
    with synthetic fixture rows strictly for software tests.
    """
    days=assert_frozen_ecology(contract,calendar)
    if source_member_verified is not True:
        return {
            "status":"HOLD_ORIGINAL_EVENT_MEMBER_PROVENANCE_UNVERIFIED",
            "real_ecological_conclusion":False,
            "calendar_day_pair_count":41,
            "no_event_rows_classified":True
        }
    if not isinstance(source_event_rows,(list,tuple)):
        raise ValueError("raw original event table must be verified")
    zone_counts=Counter()
    stations=defaultdict(set)
    bad_species=set()
    selected=0
    out_of_calendar=0
    for event in source_event_rows:
        if not isinstance(event,Mapping):
            raise ValueError("source original event row must have named columns")
        if any(k not in event for k in _LOCAL_FIELDS):
            raise ValueError("source row absent required independently observed column")
        # Unmatched source events stay in source membership audit,
        # never used to reselect or alter original dates.
        day_text=event["Date"]
        try:
            day=date.fromisoformat(day_text)
        except (TypeError,ValueError):
            raise ValueError("invalid source event date")
        if not (day.isoformat()==day_text):
            raise ValueError("source event date not in YYYY-MM-DD form")
        if day_text not in days:
            out_of_calendar+=1
            continue
        sp=event["Species"]
        if sp not in TAXA:
            bad_species.add(str(sp))
            continue
        station=event["Station"]
        if not isinstance(station,str) or not station.strip():
            raise ValueError("invalid original physical station identifier")
        minutes=parse_clock_minutes(event["Time"])
        zone=classify_event_time(day,minutes)
        branch=days[day_text]
        selected+=1
        zone_counts[(sp,branch,zone)]+=1
        stations[(sp,branch)].add(station)
    if bad_species:
        raise ValueError("source taxonomic naming unrecognized: "+",".join(sorted(bad_species)))
    species_rows=[]
    for sp in TAXA:
        for b in BRANCHES:
            species_rows.append({
                "Species":sp,"photoperiod_branch":b,
                "daylight_core_detected_events":zone_counts[(sp,b,"daylight_core")],
                "daylight_edge_detected_events":zone_counts[(sp,b,"daylight_edge")],
                "night_detected_events":zone_counts[(sp,b,"night")],
                "all_events":sum(zone_counts[(sp,b,z)] for z in ZONES),
                "unique_source_camera_stations_with_events":len(stations[(sp,b)]),
            })
    return {
        "status":"TIMESTAMP_ONLY_ECOLOGICAL_SUPPORT_AUDIT_NOT_EFFORT_OR_LATENT_ACTIVITY",
        "real_ecological_conclusion":False,
        "fixed_matched_astronomical_day_pairs":41,
        "fixed_calendar_dates":82,
        "source_events_within_original_82_dates":selected,
        "source_events_outside_original_82_dates":out_of_calendar,
        "all_four_taxa_retained_even_with_zero_events":True,
        "species_branch_solar_zone_counts":species_rows,
        "real_independent_hourly_camera_operation_verified":False,
        "source_camera_q_independently_calibrated":False,
        "temperature_or_human_clock_time_qualified":False,
        "warning":"The event category table is NOT an effort-adjusted activity rate and cannot be used to claim thermal or interspecific causal processes."
    }


def source_effort_and_ecological_support(
    contract:Mapping[str,object],calendar:Mapping[str,object],
    event_audit:Mapping[str,object],
    verified_operation_intervals:Mapping[tuple[str,str],Sequence[tuple[float,float]]],
    *,
    independent_operation_log_attested:bool=False,
)->dict[str,object]:
    """Non-inferential site×branch zone exposure denominators; fail closed.

    Source table must contain operational intervals for ALL original
    stations×matched dates; missing keys are NOT interpreted as camera-off.
    """
    days=assert_frozen_ecology(contract,calendar)
    if (
        independent_operation_log_attested is not True
        or event_audit.get("status")!=
           "TIMESTAMP_ONLY_ECOLOGICAL_SUPPORT_AUDIT_NOT_EFFORT_OR_LATENT_ACTIVITY"
    ):
        return {"status":"HOLD_NO_HOURLY_OPERATION_DURATION",
                "rate_estimates_computed":False}
    if not isinstance(verified_operation_intervals,Mapping):
        raise ValueError("requires independent ORIGINAL operational clock intervals")
    if not verified_operation_intervals:
        return {"status":"HOLD_EMPTY_ORIGINAL_CAMERA_OPERATION_ROSTER",
                "rate_estimates_computed":False}
    roster={s for s,d in verified_operation_intervals}
    if any(not isinstance(s,str) or not s for s in roster):
        raise ValueError("invalid independent original camera site roster")
    expected={(s,day) for s in roster for day in days}
    if set(verified_operation_intervals)!=expected:
        return {
            "status":"HOLD_INCOMPLETE_STATION_DATE_OPERATION_COVERAGE",
            "expected_station_day_cells":len(expected),
            "provided_cells":len(verified_operation_intervals),
            "rate_estimates_computed":False
        }
    exposure=Counter()
    station_branch=defaultdict(lambda:Counter())
    for (station,d), intervals in verified_operation_intervals.items():
        zoned=solar_zone_operation_minutes(date.fromisoformat(d),intervals)
        for zone,minutes in zoned.items():
            exposure[(days[d],zone)]+=minutes/60.
            station_branch[station][(days[d],zone)]+=minutes/60.
    paired_operating_sites=sum(
        all(sum(station_branch[s][(b,z)] for z in ZONES)>0
            for b in BRANCHES)
        for s in roster
    )
    supported=[]
    for taxon in TAXA:
        selected=[x for x in event_audit["species_branch_solar_zone_counts"]
                  if x["Species"]==taxon]
        okay=(
            all(x["all_events"]>=MIN_EVENTS_EACH_BRANCH for x in selected)
            and paired_operating_sites>=MIN_STATIONS_BOTH_BRANCHES
        )
        supported.append({"Species":taxon,
                          "descriptive_support_guard_passed":bool(okay),
                          "minimum_events_each_branch":min(x["all_events"] for x in selected)})
    return {
        "status":"SOURCE_OPERATION_HOURLY_EFFORT_ADMITTED_DESCRIPTIVE_SUPPORT_ONLY",
        "rate_estimates_computed":False,
        "no_statistical_ecological_inference_produced":True,
        "fixed_source_station_roster_size":len(roster),
        "stations_positive_operation_both_branches":paired_operating_sites,
        "camera_hours_by_branch_zone":[
            {"branch":b,"zone":z,"camera_hours":exposure[(b,z)]}
            for b in BRANCHES for z in ZONES
        ],
        "taxa_preserved_with_predeclared_low_support_flags":supported,
        "source_q_for_true_latent_activity_still_unqualified":True
    }
