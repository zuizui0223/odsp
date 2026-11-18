#!/usr/bin/env python3
"""Identity-matched German red-kite GPS attrition funnel, no breeding responses.

Reuse the fixed prior provider bytes/headers and GPS criteria. This funnel
asks *at what stage* 63 raw metadata bird-ID strings become 49 eligible,
without printing GPS positions, times, IDs or any nest/success values.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from scripts.bop_red_kite_raw_group_prefix_only_v1 import KeyPrefixCollector
from scripts.bop_red_kite_german_gps_eligibility_v1 import _source_lines,_timestamp

CONTRACT=ROOT/"research/BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_CONTRACT.json"
HEADERS=ROOT/"BOP_RED_KITE_HEADER_ONLY_V1_FIRST_RECEIPT.json"
GPS_FIRST=ROOT/"BOP_RED_KITE_GER_GPS_ELIGIBILITY_V1_FIRST_RECEIPT.json"


def _fixed():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    h=json.loads(HEADERS.read_text(encoding="utf-8"))
    first=json.loads(GPS_FIRST.read_text(encoding="utf-8"))
    m=c.get("method",{})
    src=c.get("authorized_source_files",[])
    if (
        c.get("contract_id")!="bop-redkite-german-gps-fixed-stage-attrition-v1"
        or c.get("frozen_date")!="2026-11-18"
        or [x["file"] for x in src]!=["GER_indseasondata.csv","GER_trackingdata.csv"]
        or src[0]["md5"]!="bdf5445971195ca8cc27760d242b1563"
        or src[1]["md5"]!="ec5dd057fc6d704a09f15bbbffe00129"
        or src[1]["bytes"]!=53471439
        or m.get("expected_original_GPS_v1_primary_S4_seasons")!=99
        or m.get("expected_original_GPS_v1_primary_S4_birds")!=49
        or m.get("fixes_minimum")!="strictly_more_than_800_events_before_any_new_hourly_thinning"
        or m.get("no_raw_ID_or_ID_hash_or_lat_lon_or_timestamp_in_output") is not True
        or c["interpretation"]["scientific_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or first["claim_ceiling"]["published_GER_eligible_99_63_not_reproduced"] is not True
    ):
        raise ValueError("frozen group-identification funnel or original first result was rewritten")
    return c,h,first


def _metadata_identity_map(spec:dict,head:dict)->tuple[dict[str,str],dict]:
    filename=spec["file"]
    scanner=KeyPrefixCollector({
        "key":filename,
        "bytes":spec["bytes"],
        "md5":spec["md5"],
        "header_columns":head["column_names"],
        "allowed_prefix_columns":["year_id","bird_id"],
    },head["header_sha256"])
    for line in _source_lines({"filename":filename,"bytes":spec["bytes"],"md5":spec["md5"]}):
        scanner.feed(line)
    stats=scanner.finish()
    if stats["distinct_bird_ID_strings"]!=63 or stats["distinct_year_ID_strings"]!=159:
        raise ValueError("metadata reference roster is not original 159 seasons / 63 bird strings")
    return scanner.season_owner,stats


def summarize_stages(meta:dict[str,str],gps_records,header:bytes)->dict:
    """Provider GPS record lines are only decoded inside this local runner."""
    first=next(gps_records,None)
    if first is None or first!=header:
        raise ValueError("original full-source GPS header bytes are not intact")
    raw_lines=0
    malformed=0
    unlinked_year=0
    inconsistent_bird=0
    valid_rows=0
    s1=set()
    s2=set()
    s3=set()
    valid_season_events=Counter()
    for raw in gps_records:
        raw_lines+=1
        try:
            rec=next(csv.reader([raw.decode("utf-8")],strict=True))
            if len(rec)!=7:
                raise ValueError("GPS columns wrong")
            yr,bird,time,lon,lat,_,_=rec
            when=_timestamp(time)
            x,y=float(lon),float(lat)
            if not (yr and bird and math.isfinite(x) and math.isfinite(y)
                    and -180<=x<=180 and -90<=y<=90):
                raise ValueError("GPS key/date/coordinate unavailable")
        except (ValueError,UnicodeError,csv.Error,OverflowError):
            malformed+=1
            continue
        if yr not in meta:
            unlinked_year+=1
            continue
        if meta[yr]!=bird:
            inconsistent_bird+=1
            continue
        valid_rows+=1
        s1.add(yr)
        if not (x>9 and y>50):
            continue
        s2.add(yr)
        if not (74<=when.timetuple().tm_yday<=191):
            continue
        s3.add(yr)
        valid_season_events[yr]+=1
    s4={k for k,v in valid_season_events.items() if v>800}
    keys=[set(meta),s1,s2,s3,s4]
    labels=[
        "S0_all_GER_metadata_seasons",
        "S1_any_valid_GPS_event_matching_exact_year_bird_pair",
        "S2_at_least_one_GPS_event_lat_gt_50_lon_gt_9",
        "S3_at_least_one_GPS_event_UTC_ordinal_DOY_74_through_191",
        "S4_gt_800_valid_GPS_event_rows_after_S3",
    ]
    rows=[]
    for i,(label,years) in enumerate(zip(labels,keys)):
        birds={meta[y] for y in years}
        prior_birds={meta[y] for y in keys[i-1]} if i else birds
        rows.append({
            "stage":label,"season_ID_strings":len(years),"bird_ID_strings":len(birds),
            "seasons_lost_from_previous_stage":len(keys[i-1])-len(years) if i else 0,
            "birds_lost_from_previous_stage":len(prior_birds-birds) if i else 0,
        })
    if not (s4<=s3<=s2<=s1<=set(meta)):
        raise ValueError("fixed monotone source eligibility stage nesting failed")
    return {
        "input_GPS_physical_lines":raw_lines,
        "invalid_missing_GPS_rows":malformed,
        "unknown_GPS_year_ID_rows":unlinked_year,
        "GPS_year_ID_with_different_bird_ID_rows":inconsistent_bird,
        "linked_valid_GPS_rows":valid_rows,
        "source_stage_funnel":rows,
        "source_primary_99_seasons_49_bird_strings_rechecked":(
            rows[-1]["season_ID_strings"]==99 and rows[-1]["bird_ID_strings"]==49
        ),
    }


def run():
    c,h,first=_fixed()
    metadata,meta_stats=_metadata_identity_map(c["authorized_source_files"][0],
                                             h["verified_first_header"]["GER_indseasondata"])
    gps=c["authorized_source_files"][1]
    gps_header=h["verified_first_header"]["GER_trackingdata"]
    expected_header=(",".join(gps_header["column_names"])+"\r\n").encode("utf-8")
    if hashlib.sha256(expected_header).hexdigest()!=gps_header["header_sha256"]:
        raise ValueError("source GPS header hash changed")
    stats=summarize_stages(metadata,
                           iter(_source_lines({"filename":gps["file"],"bytes":gps["bytes"],"md5":gps["md5"]})),
                           expected_header)
    if not stats["source_primary_99_seasons_49_bird_strings_rechecked"]:
        raise ValueError("fixed first GPS sample size drifted")
    return {
        "schema_version":1,
        "status":"SOURCE_ONLY_GER_GPS_STAGE_ATTRITION_RECORDED",
        "preaccess_funnel_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "provider_full_GPS_and_metadata_MD5_verified":True,
        "result":stats,
        "original_99_season_63_bird_publication_reconciled":False,
        "two_German_populations_authenticated":False,
        "GPS_exact_positions_or_times_logged":False,
        "bird_or_year_ID_strings_logged":False,
        "breeding_labels_accessed_or_parsed":False,
        "real_forecast_calibration_or_scoring_performed":False,
        "biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        "old_BOP_terminal":"empirical_state_prediction_mixed",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.resolve() in (CONTRACT.resolve(),HEADERS.resolve(),GPS_FIRST.resolve()):
        raise ValueError("refuse to overwrite source provenance files")
    try:
        result=run()
    except (OSError,ValueError,UnicodeError,csv.Error,StopIteration) as exc:
        result={
            "schema_version":1,
            "status":"HOLD_SOURCE_ONLY_GER_GPS_STAGE_ATTRITION",
            "error_type":type(exc).__name__,
            "GPS_exact_positions_or_times_logged":False,
            "bird_or_year_ID_strings_logged":False,
            "breeding_labels_accessed_or_parsed":False,
            "real_forecast_calibration_or_scoring_performed":False,
            "biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        }
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]!="SOURCE_ONLY_GER_GPS_STAGE_ATTRITION_RECORDED":
        raise SystemExit("SOURCE_STAGE_FUNNEL_HOLD: do not infer paper eligible group")
if __name__=="__main__":
    main()
