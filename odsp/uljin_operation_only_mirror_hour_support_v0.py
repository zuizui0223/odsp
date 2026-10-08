"""Outcome-free Uljin camera operating HOURS for the original 41 date pairs.

THIS DOES NOT READ ECOBANK: it accepts independently sourced/validated
NORMALIZED camera-operation rows if an original, authenticated operation
log becomes available. The source has NOT been materialized yet.

A 24h camera deployment window cannot be reconstructed from an animal
photo; likewise a functional CAMERA NIGHT count is not a verified
clock-hour denominator. This evaluator therefore requires exact offset-
aware original hardware operation/downtime intervals with UTC+09:00,
unions overlapping deployment periods, unions overlapping downtime,
subtracts only once and aggregates by six frozen 4h civil-clock bins.

Only station counts, never exact station ID/timing, leave this module.
No event, species, animal activity, predictive score or inferred
causal seasonal hysteresis enters the computation. The original
first 41 date matches NEVER change.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime,date,time,timedelta,timezone
import math
from typing import Any,Mapping,Sequence

from .uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)

CONTRACT_ID="odsp-uljin-operation-only-mirrored-days-hourly-exposure-v0"
KST=timezone(timedelta(hours=9))
BINS=((0,4),(4,8),(8,12),(12,16),(16,20),(20,24))


def _validate_contract(plan:Mapping[str,object])->None:
    if (
        not isinstance(plan,Mapping)
        or plan.get("schema_version")!=1
        or plan.get("contract_id")!=CONTRACT_ID
        or plan.get("state")!="PRE_ORIGINAL_OPERATION_RECORD_ACCESS_SOURCE_MISSING"
        or plan.get("original_calendar_run")!=37771342454
        or plan.get("utc_offset_hours")!=9
        or plan.get("time_zone")!="Asia/Seoul"
    ):
        raise ValueError("unrecognized source-unavailable operation-hours contract")
    sample=plan.get("predeclared_stations_and_pairs",{})
    if (
        sample.get("original_day_pair_count")!=41
        or sample.get("local_clock_bins_hours")!=[list(b) for b in BINS]
        or sample.get("minimum_functional_hours_in_EACH_4h_bin")!=3.
        or sample.get("matched_pair_requires_both_full_calendar_dates") is not True
        or sample.get("no_selection_on_species_detection_rows") is not True
    ):
        raise ValueError("original station-hour eligibility gates changed")
    src=plan.get("source_record_contract",{})
    if (
        src.get("source_archive_bytes_available") is not False
        or src.get("source_independent_operation_lineage_verified") is not False
        or src.get("utc_offset_hours",9)!=9
        or src.get("allowed_region_prefixes")!=["UJ1","UJ2"]
        or src.get("zero_detection_station_retained_in_operation_frame") is not True
    ):
        raise ValueError("source-outcome independent admission status changed")


def _station(value:object)->str:
    if not isinstance(value,str) or not value.strip():
        raise ValueError("missing station physical identity")
    id=value.strip()
    if not (id.startswith("UJ1") or id.startswith("UJ2")):
        raise ValueError("unknown protected-site region station prefix")
    return id


def _when(value:object, field:str)->datetime:
    if not isinstance(value,str):
        raise ValueError(f"{field} must be ISO8601 offset-aware string")
    try:
        dt=datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} does not parse as ISO8601") from exc
    if (
        dt.tzinfo is None or
        dt.utcoffset()!=timedelta(hours=9) or
        dt.tzinfo is None
    ):
        raise ValueError(f"{field} must encode original +09:00 camera time")
    return dt.astimezone(KST)


def _read_intervals(
    rows:Sequence[Mapping[str,object]],
    start_label:str,end_label:str,
)->dict[str,list[tuple[datetime,datetime]]]:
    by_station=defaultdict(list)
    if not isinstance(rows,(list,tuple)):
        raise ValueError("source operation rows must be an explicit list")
    for record in rows:
        if not isinstance(record,Mapping):
            raise ValueError("operation record must be mapping")
        if set(record)!={"Station",start_label,end_label}:
            raise ValueError("operation record must use exact source-validated keys")
        station=_station(record["Station"])
        a=_when(record[start_label],start_label)
        b=_when(record[end_label],end_label)
        if a>=b:
            raise ValueError("nonpositive source operation interval")
        by_station[station].append((a,b))
    return by_station


def _merged(intervals:list[tuple[datetime,datetime]]
            )->list[tuple[datetime,datetime]]:
    result=[]
    for start,end in sorted(intervals):
        if result and start<=result[-1][1]:
            result[-1]=(result[-1][0],max(end,result[-1][1]))
        else:
            result.append((start,end))
    return result


def _intersect_seconds(
    intervals:list[tuple[datetime,datetime]],
    start:datetime,end:datetime,
)->float:
    if not intervals: return 0.
    return sum(max(0.,(min(b,end)-max(a,start)).total_seconds())
               for a,b in intervals)


def _fully_contained(
    downtime:list[tuple[datetime,datetime]],
    operation:list[tuple[datetime,datetime]],
)->bool:
    # Every interval endpoint and all its interior must lie inside
    # one merged continuous operating interval. Prevent repairing an
    # out-of-bounds downtime record after any observed animal outcomes.
    for a,b in downtime:
        if not any(x<=a and b<=y for x,y in operation):
            return False
    return True


def _six_hour_bins(
    day:date,
    operation:list[tuple[datetime,datetime]],
    downtime:list[tuple[datetime,datetime]],
)->tuple[float,...]:
    result=[]
    for h0,h1 in BINS:
        start=datetime.combine(day,time(hour=h0),KST)
        end=(datetime.combine(day+timedelta(days=1),time.min,KST)
             if h1==24 else datetime.combine(day,time(hour=h1),KST))
        covered=_intersect_seconds(operation,start,end)
        lost=_intersect_seconds(downtime,start,end)
        available=(covered-lost)/3600.
        if available< -1e-9 or available>4.+1e-9:
            raise ValueError("downtime and deployment overlap inconsistent")
        result.append(max(0.,min(4.,available)))
    return tuple(result)


def summarize_mirror_camera_hour_support(
    original_calendar_plan:Mapping[str,object],
    frozen_operation_plan:Mapping[str,object],
    deployments:Sequence[Mapping[str,object]],
    outages:Sequence[Mapping[str,object]],
)->dict[str,Any]:
    """Experimental dry-run ONLY on normalized independent original logs.

    A structural count can still be generated on synthetic records but
    never attests actual independence/accuracy of the original EcoBank
    source. The source is currently missing; no claim about actual
    82 Uljin station support follows from any example output.
    """
    _validate_contract(frozen_operation_plan)
    calendar=generate_preoutcome_2022_mirror_calendar(
        original_calendar_plan
    )
    pairs=calendar["matched_dates"]
    if len(pairs)!=41:
        raise ValueError("original mirror calendar cannot be altered")
    original=_read_intervals(
        deployments,"DeploymentStart","DeploymentEnd"
    )
    inactive=_read_intervals(outages,"DowntimeStart","DowntimeEnd")
    if not original:
        raise ValueError("no independently recorded camera deployment intervals")
    if set(inactive)-set(original):
        raise ValueError("downtime mentions camera absent from original deployment roster")
    a={station:_merged(intervals) for station,intervals in original.items()}
    b={station:_merged(inactive.get(station,[])) for station in original}
    if any(not _fully_contained(b[station],a[station]) for station in a):
        raise ValueError("recorded downtime extends outside original operation")
    predeclared=frozen_operation_plan["predeclared_stations_and_pairs"]
    minimum=predeclared["minimum_functional_hours_in_EACH_4h_bin"]
    all_days={
        date.fromisoformat(pair[key])
        for pair in pairs for key in ("ascending_date","descending_date")
    }
    available={}
    for station in a:
        available[station]={
            day:_six_hour_bins(day,a[station],b[station])
            for day in all_days
        }
    sites_by_group={"UJ1":set(),"UJ2":set()}
    pair_support=defaultdict(int)
    station_pair_numbers=[]
    for station in sorted(a):
        region="UJ1" if station.startswith("UJ1") else "UJ2"
        sites_by_group[region].add(station)
        supported=0
        for pair in pairs:
            start=date.fromisoformat(pair["ascending_date"])
            end=date.fromisoformat(pair["descending_date"])
            if (
                all(h+1e-12>=minimum for h in available[station][start])
                and all(h+1e-12>=minimum for h in available[station][end])
            ):
                supported+=1
                pair_support[region]+=1
        station_pair_numbers.append((region,supported))
    summary={}
    for region in ("UJ1","UJ2"):
        counts=[count for label,count in station_pair_numbers if label==region]
        summary[region]={
            "registered_source_station_count":len(sites_by_group[region]),
            "station_day_pairs_with_both_dates_meeting_hourly_coverage":
                pair_support[region],
            "stations_with_at_least_one_source_eligible_date_pair":
                sum(n>=1 for n in counts),
            "stations_with_all_41_source_eligible_pairs":
                sum(n==41 for n in counts),
        }
    return {
        "schema_version":1,
        "method":"uljin_operation_only_mirror_hour_support_v0",
        "status":"SYNTHETIC_OPERATION_INPUT_COUNTS_NOT_EMPIRICAL_ELIGIBILITY",
        "original_unchanged_astronomical_date_pairs":len(pairs),
        "frozen_minimum_hours_per_each_four_hour_bin":minimum,
        "original_source_region_counts":summary,
        "total_normalized_input_stations":len(a),
        "original_EcoBank_v1p1_operation_logs_verified":False,
        "operation_metadata_independent_of_photos_attested":False,
        "species_detection_data_opened":False,
        "animal_activity_or_hysteresis_result_estimated":False,
        "per_station_identifiers_emitted":False,
        "real_Uljin_camera_support_claimed":False,
        "qualified_primary_ODSP_result":False,
        "earlier_41_pair_calendar_reclassified":False,
    }
