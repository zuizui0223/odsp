"""Outcome-embargoed, source-free bounds for DATE-only original camera logs.

Date-censored start/end records do NOT imply a 24h operational day. Under
a conservative unknown-within-calendar-day interpretation, compute
guaranteed and POSSIBLE active time, after union of deployment/outages.
Only classify a 41-pair camera comparison 'guaranteed eligible' when
each of its 12 fixed clock bins has at least 3h of guaranteed uptime.
A definitely ineligible pair has at least one bin with <3h even under
the possible-uptime upper bound. All others are AMBIGUOUS and held.

Only synthetic normalized rows are accepted in this v0. No original
EcoBank field values, wildlife event or photo records are read.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta, time, timezone
import json
import math
import re

from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)

METHOD="uljin_operation_date_censored_pair_support_v0"
KST=timezone(timedelta(hours=9))
BINS=((0,4),(4,8),(8,12),(12,16),(16,20),(20,24))
STATION_RE=re.compile(r"^UJ[12][_-][A-Za-z0-9_-]+$")
MIN_HOURS=3.


# Immutable semantic mirror of pre-result version-0 assumptions.
# A header or 3-hour cutoff check alone cannot detect a post-result change
# to the meaning of "guaranteed deployment" or possible downtime.
_FROZEN_INPUTS=json.loads(r'''{"declared":"EXPLICIT SYNTHETIC normalized source-independent hypothetical deployment and complete downtime interval records only","deployment_record_keys":["Station","DeploymentStartDate","DeploymentEndDate"],"downtime_record_keys":["Station","DowntimeStartDate","DowntimeEndDate"],"date_format":"YYYY-MM-DD calendar day in Asia/Seoul","date_interpretation":"Deployment begins at an unknown instant in its first named day and ends at an unknown instant on its last named day; downtime also begins/ends at unknown times within its named boundary days","unknown_completeness":"If downtime coverage/completeness is unknown, no robust eligibility may be claimed","deployment_and_downtime_intervals_must_be_field_original_independent_of_photos":true}''')
_FROZEN_BOUNDS=json.loads(r'''{"possible_deployment":"[00:00 of start date, 00:00 day following end date)","guaranteed_deployment":"[00:00 day following start date, 00:00 of end date), if nonempty","possible_downtime":"[00:00 start date, 00:00 day following end date)","guaranteed_downtime":"[00:00 day following start date, 00:00 end date), if nonempty","guaranteed_active":"union(guaranteed deployment) minus union(possible downtime)","possibly_active":"union(possible deployment) minus union(guaranteed downtime)","bins":[[0,4],[4,8],[8,12],[12,16],[16,20],[20,24]],"minimum_guaranteed_or_possible_active_hours_per_bin":3,"eligible_pair":"all six 4h bins on both ORIGINAL matched astronomical days have GUARANTEED operating >=3h","ineligible_pair":"at least one of 12 bins has POSSIBLE operating <3h","otherwise":"AMBIGUOUS_NOT_ELIGIBLE_FOR_CONFIRMATORY_RESEARCH","unbounded_unknown_downtime":"HOLD_DOWNTIME_COMPLETENESS_UNKNOWN"}''')

def _validate_contract(plan:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=METHOD
        or plan.get("stage")!="FROZEN_SOURCE_FREE_BEFORE_FIRST_BOUND_RESULT"
        or plan.get("original_calendar")!=
            "ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
        or plan.get("source_status")!=
            "ECOBANK_V1P1_ARCHIVE_UNAVAILABLE_AND_HOURLY_OPERATION_PROVENANCE_UNVERIFIED"
        or plan.get("conservative_interval_bounds")!=_FROZEN_BOUNDS
        or plan.get("inputs")!=_FROZEN_INPUTS
        or plan.get("hard_gates",[])[-1:]!=[
            "Do not reclassify registered ODSP training-process or untouched-external results"
        ]
    ):
        raise ValueError("frozen date-censored operating-hours contract changed")


def _day(value:object)->date:
    if not isinstance(value,str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",value):
        raise ValueError("date-only hardware log needs exact YYYY-MM-DD")
    d=date.fromisoformat(value)
    if d.year not in (2022,2023):
        raise ValueError("only synthetic source study-era dates accepted")
    return d


def _midnight(day:date)->datetime:
    return datetime.combine(day,time.min,tzinfo=KST)


def _merge(parts:Sequence[tuple[datetime,datetime]]
           )->list[tuple[datetime,datetime]]:
    result=[]
    for a,b in sorted(parts):
        if a>=b:
            continue
        if result and a<=result[-1][1]:
            result[-1]=(result[-1][0],max(result[-1][1],b))
        else:
            result.append((a,b))
    return result


def _subtract(base:Sequence[tuple[datetime,datetime]],
              removed:Sequence[tuple[datetime,datetime]]
              )->list[tuple[datetime,datetime]]:
    result=[]
    for begin,end in _merge(base):
        cursor=begin
        for off,on in _merge(removed):
            if on<=cursor:continue
            if off>=end:break
            if off>cursor:
                result.append((cursor,min(off,end)))
            cursor=max(cursor,min(on,end))
            if cursor>=end:break
        if cursor<end:
            result.append((cursor,end))
    return _merge(result)


def _read_date_windows(
    rows:Sequence[Mapping[str,object]],
    start_key:str,end_key:str
)->dict[str,tuple[list[tuple[datetime,datetime]],
                 list[tuple[datetime,datetime]]]]:
    if not isinstance(rows,(list,tuple)):
        raise ValueError("synthetic source windows must be a sequence")
    lows=defaultdict(list)
    highs=defaultdict(list)
    for row in rows:
        if not isinstance(row,Mapping) or set(row)!={"Station",start_key,end_key}:
            raise ValueError("only frozen date-only interval columns allowed")
        station=row["Station"]
        if not isinstance(station,str) or not STATION_RE.fullmatch(station):
            raise ValueError("synthetic physical station ID/prefix invalid")
        a,b=_day(row[start_key]),_day(row[end_key])
        if a>b:
            raise ValueError("source start date after end date")
        h0,h1=_midnight(a),_midnight(b+timedelta(days=1))
        highs[station].append((h0,h1))
        l0,l1=_midnight(a+timedelta(days=1)),_midnight(b)
        if l0<l1:
            lows[station].append((l0,l1))
    return {
        station:(_merge(lows[station]),_merge(highs[station]))
        for station in highs
    }


def _active_interval_bounds(
    deploy:tuple[list[tuple[datetime,datetime]],
                 list[tuple[datetime,datetime]]],
    downtime:tuple[list[tuple[datetime,datetime]],
                   list[tuple[datetime,datetime]]],
)->tuple[list[tuple[datetime,datetime]],list[tuple[datetime,datetime]]]:
    lower_deploy,upper_deploy=deploy
    lower_off,upper_off=downtime
    # Possible downtime outside all possible deployment cannot be a
    # legitimate independently authored hardware outage row.
    if _subtract(upper_off,upper_deploy):
        raise ValueError("source downtime potentially outside original operation dates")
    guaranteed=_subtract(lower_deploy,upper_off)
    possible=_subtract(upper_deploy,lower_off)
    if _subtract(guaranteed,possible):
        raise ValueError("guaranteed uptime exceeds possible uptime")
    return guaranteed,possible


def _hours(intervals:Sequence[tuple[datetime,datetime]],
           day:date,h0:int,h1:int)->float:
    start=_midnight(day)+timedelta(hours=h0)
    end=_midnight(day)+timedelta(hours=h1)
    value=sum(max(0.,(min(b,end)-max(a,start)).total_seconds())
              for a,b in intervals)/3600.
    if value<-1e-12 or value>4.+1e-12 or not math.isfinite(value):
        raise ValueError("impossible bounded camera-hour exposure")
    return max(0.,min(4.,value))


def classify_date_censored_mirror_support(
    original_calendar:Mapping[str,object],
    frozen_plan:Mapping[str,object],
    synthetic_deployments:Sequence[Mapping[str,object]],
    synthetic_downtime:Sequence[Mapping[str,object]],
    *,
    synthetic_complete_downtime_roster:bool,
    input_kind:str="synthetic_only",
)->dict[str,object]:
    _validate_contract(frozen_plan)
    if input_kind!="synthetic_only":
        raise ValueError("v0 is synthetic only: no original EcoBank data intake")
    pairs=generate_preoutcome_2022_mirror_calendar(original_calendar)["matched_dates"]
    if len(pairs)!=41:
        raise ValueError("original astronomy date pairs must remain unchanged")
    if type(synthetic_complete_downtime_roster) is not bool:
        raise ValueError("synthetic outage-completeness flag required")
    if not synthetic_complete_downtime_roster:
        return {
            "schema_version":1,
            "method":METHOD,
            "status":"HOLD_DOWNTIME_COMPLETENESS_UNKNOWN",
            "no_station_pair_eligibility_inferred":True,
            "real_source_archive_or_operations_read":False,
            "animal_detection_rows_read":False,
            "real_eligibility_claimed":False,
        }
    dep=_read_date_windows(
        synthetic_deployments,"DeploymentStartDate","DeploymentEndDate"
    )
    off=_read_date_windows(
        synthetic_downtime,"DowntimeStartDate","DowntimeEndDate"
    )
    if not dep or set(off)-set(dep):
        raise ValueError("missing deployment or downtime for unknown physical station")
    per_region={
        "UJ1":{"synthetic_stations":0,"guaranteed_eligible_pairs":0,
               "definitely_ineligible_pairs":0,"ambiguous_pairs":0,
               "stations_with_any_guaranteed_pair":0},
        "UJ2":{"synthetic_stations":0,"guaranteed_eligible_pairs":0,
               "definitely_ineligible_pairs":0,"ambiguous_pairs":0,
               "stations_with_any_guaranteed_pair":0}
    }
    for site in sorted(dep):
        region=site[:3]
        region_summary=per_region[region]
        region_summary["synthetic_stations"]+=1
        lower,upper=_active_interval_bounds(dep[site],
                     off.get(site,([],[])))
        have_any=False
        for pair in pairs:
            dates=[_day(pair["ascending_date"]),
                   _day(pair["descending_date"])]
            low_hours=[_hours(lower,day,a,b)
                       for day in dates for a,b in BINS]
            high_hours=[_hours(upper,day,a,b)
                        for day in dates for a,b in BINS]
            if any(a>b+1e-12 for a,b in zip(low_hours,high_hours)):
                raise ValueError("invalid monotone interval-censored bounds")
            if all(h+1e-12>=MIN_HOURS for h in low_hours):
                region_summary["guaranteed_eligible_pairs"]+=1
                have_any=True
            elif any(h+1e-12<MIN_HOURS for h in high_hours):
                region_summary["definitely_ineligible_pairs"]+=1
            else:
                region_summary["ambiguous_pairs"]+=1
        if have_any:
            region_summary["stations_with_any_guaranteed_pair"]+=1
    for region,v in per_region.items():
        if (v["guaranteed_eligible_pairs"]+v["definitely_ineligible_pairs"]
             +v["ambiguous_pairs"]!=41*v["synthetic_stations"]):
            raise ValueError("the 41-pair station frame was not conserved")
    result={
        "schema_version":1,"method":METHOD,
        "status":"SYNTHETIC_INTERVAL_CENSORED_OPERATION_BOUNDS_ONLY",
        "original_unchanged_date_pair_count":len(pairs),
        "minimum_hours_per_original_four_hour_bin":MIN_HOURS,
        "region_only_counts":per_region,
        "original_archive_authenticated":False,
        "original_hardware_source_independence_attested":False,
        "hourly_operation_log_verified":False,
        "animal_detection_rows_read":False,
        "source_precise_station_ids_reported":False,
        "real_Uljin_pair_eligibility_claimed":False,
        "qualified_ODSP_route_modified":False
    }
    return result
