#!/usr/bin/env python3
"""Predeclared source-only German red-kite GPS season eligibility sensitivity.

The source GPS bytes necessarily contain real locations/timestamps and are read
inside the Actions runner, but no raw location, timestamp, individual or season
identifier is logged or persisted. NO nest/HR/success label is accessed.
This is not a published-paper exact replication or new forecast evaluation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from scripts.bop_red_kite_raw_group_prefix_only_v1 import (
    _load_contract as load_metadata_contract,
    _fetch_source as fetch_metadata_prefix,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"research/BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_CONTRACT.json"
HEADERS=ROOT/"BOP_RED_KITE_HEADER_ONLY_V1_FIRST_RECEIPT.json"

DATES=("fixed_2023_DOY_ordinal","actual_calendar_month_day")
THIN=("observed_source_events","unique_utc_hour_bin","rolling_3600_seconds")
MINIMUM=("strict_gt_800","inclusive_ge_800")


def _frozen():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    h=json.loads(HEADERS.read_text(encoding="utf-8"))
    f=c.get("frozen_filters",{})
    a=c.get("input_sources",[])
    intr=c.get("interpretation",{})
    if (c.get("contract_id")!="bop-redkite-german-gps-eligibility-12-fixed-rules-v1"
        or c.get("frozen_date")!="2026-11-18"
        or [s.get("filename") for s in a]!=["GER_trackingdata.csv","GER_indseasondata.csv"]
        or a[0]["bytes"]!=53471439
        or a[0]["md5"]!="ec5dd057fc6d704a09f15bbbffe00129"
        or a[0]["allowed_columns"]!=h["verified_first_header"]["GER_trackingdata"]["column_names"]
        or a[1]["md5"]!="bdf5445971195ca8cc27760d242b1563"
        or f.get("lat_wgs_strict_gt")!=50
        or f.get("long_wgs_strict_gt")!=9
        or f.get("ordinal_utc_DOY_inclusive")!=[74,191]
        or f.get("calendar_utc_month_day_inclusive")!=["03-15","07-10"]
        or f.get("time_reference")!="UTC"
        or f.get("thinning_arms")!=list(THIN)
        or f.get("date_arms")!=list(DATES)
        or f.get("minimum_location_arms")!=list(MINIMUM)
        or f.get("primary_a_priori")!="fixed_2023_DOY_ordinal__observed_source_events__strict_gt_800"
        or f.get("all_12_arm_results_reported_even_if_no_match") is not True
        or intr.get("scientific_terminal")!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or intr.get("no_reproductive_labels_accessed_or_parsed") is not True
        or intr.get("no_exact_GPS_positions_or_time_printed") is not True
        or intr.get("no_per_bird_ids_or_year_ids_emitted") is not True
    ):
        raise ValueError("prospectively frozen full-GPS access or 12-arm protocol drifted")
    return c,h


def _source_lines(spec):
    """Provider bytes are hashed in streaming memory, not saved on disk."""
    key=spec["filename"]
    url=f"https://zenodo.org/records/13736049/files/{key}?download=1"
    req=Request(url,headers={"User-Agent":"ODSP-BOP-redkite-eligibility-v1/1.0","Accept-Encoding":"identity"})
    md5=hashlib.md5()
    total=0
    pending=bytearray()
    with urlopen(req,timeout=90) as res:
        final=urlparse(res.geturl())
        if (final.scheme!="https"
            or final.hostname not in ("zenodo.org","www.zenodo.org")
            or "/13736049/" not in unquote(final.path)
            or key not in unquote(final.path)
            or int(res.status)!=200):
            raise ValueError("unexpected source URL redirect or HTTP status")
        while True:
            block=res.read(32768)
            if not block:
                break
            total+=len(block)
            if total>spec["bytes"]:
                raise ValueError("source content larger than frozen manifest")
            md5.update(block)
            pending.extend(block)
            while True:
                pos=pending.find(b"\n")
                if pos<0:
                    break
                yield bytes(pending[:pos+1])
                del pending[:pos+1]
            if len(pending)>16384:
                raise ValueError("one GPS physical row exceeds source-read safety budget")
    if pending:
        yield bytes(pending)
    if total!=spec["bytes"] or md5.hexdigest()!=spec["md5"]:
        raise ValueError("original official GPS full-file size/MD5 verification failed")


def _timestamp(s):
    # Treat explicit UTC and naive ISO timestamps as UTC; reject other timezone
    # interpretations by canonicalizing to UTC before calendar/ordinal selection.
    token=s.strip()
    if not token:
        raise ValueError("blank timestamp")
    if token.endswith(" UTC"):
        token=token[:-4]
    if token.endswith("Z"):
        token=token[:-1]+"+00:00"
    dt=datetime.fromisoformat(token)
    if dt.tzinfo is not None:
        dt=dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def selected_dates(dt:datetime):
    ordinal=74<=dt.timetuple().tm_yday<=191
    calendar=(3,15)<=(dt.month,dt.day)<=(7,10)
    return {"fixed_2023_DOY_ordinal":ordinal,"actual_calendar_month_day":calendar}


def thinning_counts(timestamps:list[datetime])->dict[str,int]:
    """Counts from in-memory original timestamps; no per-animal values returned."""
    sorted_times=sorted(timestamps)
    unique_hours=len({(t.year,t.month,t.day,t.hour) for t in sorted_times})
    last=None
    rolling=0
    for t in sorted_times:
        if last is None or (t-last).total_seconds()>=3600:
            rolling+=1
            last=t
    return {
        "observed_source_events":len(sorted_times),
        "unique_utc_hour_bin":unique_hours,
        "rolling_3600_seconds":rolling,
    }


def aggregate_arms(times:dict[str,dict[str,list[datetime]]],
                   season_to_bird:dict[str,str],threshold:int=800)->list[dict]:
    """Full prespecified 2 x 3 x 2 matrix; never choose best-matching arm."""
    out=[]
    for date_arm in DATES:
        for thin_arm in THIN:
            by_year={
                y:thinning_counts(ts)[thin_arm] for y,ts in times[date_arm].items()
            }
            for cutoff in MINIMUM:
                chosen=[
                    y for y,n in by_year.items()
                    if (n>threshold if cutoff=="strict_gt_800" else n>=threshold)
                ]
                if any(y not in season_to_bird for y in chosen):
                    raise ValueError("GPS season key changed across biological ID sources")
                arm=f"{date_arm}__{thin_arm}__{cutoff}"
                out.append({
                    "arm":arm,
                    "eligible_seasons":len(chosen),
                    "distinct_bird_ID_strings_in_eligible_seasons":len({season_to_bird[y] for y in chosen}),
                    "matches_paper_99_63_numbers_only":(
                        len(chosen)==99 and len({season_to_bird[y] for y in chosen})==63
                    ),
                    "not_formal_replication_even_if_matches":True,
                })
    return out


def audit_gps_rows(rows,columns:list[str],expected_header_sha256:str,
                   metadata_years:set[str],metadata_birds:set[str],threshold:int=800):
    """Input is raw physical GPS lines; output is an aggregate-only dictionary."""
    iterator=iter(rows)
    first=next(iterator,None)
    if first is None or hashlib.sha256(first).hexdigest()!=expected_header_sha256:
        raise ValueError("official raw GPS first-header SHA256 changed")
    if first!=(",".join(columns)+"\r\n").encode("utf-8"):
        raise ValueError("GPS provider header differs from original frozen header")
    times={x:defaultdict(list) for x in DATES}
    year_bird={}
    nrows=0
    malformed=0
    unlinked=0
    linked=0
    outside=0
    date_counts={d:0 for d in DATES}
    inconsistent=0
    for raw in iterator:
        nrows+=1
        try:
            line=raw.decode("utf-8")
            rec=next(csv.reader([line],strict=True))
            if len(rec)!=7:
                raise ValueError("GPS row does not have seven fixed columns")
            year_id,bird_id,timestamp,lon,lat,_,_=rec
            if not year_id or not bird_id:
                raise ValueError("GPS identity missing")
            when=_timestamp(timestamp)
            longitude=float(lon)
            latitude=float(lat)
            if not (math.isfinite(longitude) and math.isfinite(latitude)
                    and -180<=longitude<=180 and -90<=latitude<=90):
                raise ValueError("invalid GPS coordinates")
        except (ValueError,UnicodeError,csv.Error,OverflowError):
            malformed+=1
            continue
        if year_id not in metadata_years or bird_id not in metadata_birds:
            unlinked+=1
            continue
        linked+=1
        previous=year_bird.setdefault(year_id,bird_id)
        if previous!=bird_id:
            inconsistent+=1
        if not (longitude>9 and latitude>50):
            outside+=1
            continue
        flags=selected_dates(when)
        for date_arm in DATES:
            if flags[date_arm]:
                times[date_arm][year_id].append(when)
                date_counts[date_arm]+=1
    if inconsistent:
        raise ValueError("one GPS year_id maps to multiple bird ID strings")
    arms=aggregate_arms(times,year_bird,threshold)
    if len(arms)!=12:
        raise ValueError("did not report the entire preregistered 12-arm grid")
    return {
        "raw_GPS_physical_record_lines":nrows,
        "malformed_or_missing_GPS_fields":malformed,
        "records_unlinked_to_pinned_German_metadata":unlinked,
        "records_matching_pinned_German_metadata":linked,
        "linked_GPS_rows_outside_geo_bounds":outside,
        "linked_geographic_season_rows_by_rule":date_counts,
        "year_ID_to_multiple_bird_IDs_in_GPS":inconsistent,
        "all_12_prespecified_eligibility_arms":arms,
    }


def run():
    contract,h=_frozen()
    _,original_head=load_metadata_contract()
    meta=next(s for s in json.loads((ROOT/"research/BOP_RED_KITE_RAW_GROUP_PREFIX_ONLY_V1_CONTRACT.json").read_text(encoding="utf-8"))["input_files"]
              if s["key"]=="GER_indseasondata.csv")
    meta_header=original_head["verified_first_header"]["GER_indseasondata"]["header_sha256"]
    meta_stats,meta_birds,meta_years=fetch_metadata_prefix(meta,meta_header)
    if (meta_stats["physical_record_lines"]!=159
        or meta_stats["distinct_bird_ID_strings"]!=63
        or meta_stats["distinct_year_ID_strings"]!=159
        or meta_stats["source_full_file_md5_verified"] is not True):
        raise ValueError("original metadata identity source changed")
    gps=contract["input_sources"][0]
    header=h["verified_first_header"]["GER_trackingdata"]["header_sha256"]
    aggregates=audit_gps_rows(_source_lines(gps),gps["allowed_columns"],header,meta_years,meta_birds)
    return {
        "schema_version":1,
        "contract_id":contract["contract_id"],
        "preaccess_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "status":"GPS_SOURCE_ELIGIBILITY_SENSITIVITY_ONLY",
        "German_GPS_full_source_bytes_MD5_verified":True,
        "German_metadata_prefix_only_full_source_MD5_verified":True,
        "German_metadata_raw_year_IDs":159,
        "German_metadata_raw_bird_ID_strings":63,
        "GPS":aggregates,
        "primary_arm_prespecified":contract["frozen_filters"]["primary_a_priori"],
        "12_rule_grid_no_posthoc_selection":True,
        "published_German_99_63_eligible_identities_confirmed":False,
        "published_original_German_163_65_reconstructed":False,
        "original_NestTool_60min_thinning_reproduced_exactly":False,
        "GPS_positions_or_exact_times_emitted":False,
        "reproductive_labels_accessed_or_parsed":False,
        "group_rank_or_model_probabilities_scored":False,
        "biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "original_BOP_empirical_terminal":"empirical_state_prediction_mixed",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.resolve() in (CONTRACT.resolve(),HEADERS.resolve()):
        raise ValueError("refuse to overwrite frozen pre-access source files")
    try:
        result=run()
    except (OSError,ValueError,UnicodeError,csv.Error,StopIteration) as err:
        result={
            "schema_version":1,
            "status":"HOLD_GERMAN_GPS_SOURCE_OR_ELIGIBILITY",
            "error_type":type(err).__name__,
            "GPS_positions_or_exact_times_emitted":False,
            "reproductive_labels_accessed_or_parsed":False,
            "group_rank_or_model_probabilities_scored":False,
            "biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        }
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]!="GPS_SOURCE_ELIGIBILITY_SENSITIVITY_ONLY":
        raise SystemExit("GPS_ELIGIBILITY_HOLD: original source or data quality filter not established")

if __name__=="__main__":
    main()
