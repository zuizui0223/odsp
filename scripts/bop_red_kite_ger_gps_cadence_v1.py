#!/usr/bin/env python3
"""Source-only timestamp cadence of already-known original German red-kite GPS.

Reads full, checksum-fixed public GPS bytes solely for UTC time-gap summaries.
No raw or hashed bird/year IDs, timestamp, lat/lon, sex/age, reproductive labels,
model output, or individual tracking history is printed or archived.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import datetime
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from scripts.bop_red_kite_german_gps_eligibility_v1 import _source_lines,_timestamp
from scripts.bop_red_kite_ger_gps_stage_attrition_v1 import _metadata_identity_map

CONTRACT=ROOT/"research/BOP_RED_KITE_GER_GPS_CADENCE_V1_CONTRACT.json"
HEADERS=ROOT/"BOP_RED_KITE_HEADER_ONLY_V1_FIRST_RECEIPT.json"
STAGE=ROOT/"BOP_RED_KITE_GER_GPS_STAGE_ATTRITION_V1_FIRST_RECEIPT.json"

def _frozen():
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    h=json.loads(HEADERS.read_text(encoding="utf-8"))
    s=json.loads(STAGE.read_text(encoding="utf-8"))
    f=c.get("predeclared_source_screen",{})
    z=c.get("source_files",[])
    if (
        c.get("contract_id")!="bop-redkite-original-GER-GPS-cadence-frozen-v1"
        or c.get("frozen_date")!="2026-11-18"
        or c.get("source_zenodo_doi")!="10.5281/zenodo.13736049"
        or [x.get("name") for x in z]!=["GER_indseasondata.csv","GER_trackingdata.csv"]
        or [x["size"] for x in z]!=[6456,53471439]
        or [x["md5"] for x in z]!=["bdf5445971195ca8cc27760d242b1563","ec5dd057fc6d704a09f15bbbffe00129"]
        or f.get("require_original_meta_159_year_ids_63_bird_ID_strings") is not True
        or f.get("require_original_500778_source_GPS_rows_and_full_MD5") is not True
        or f.get("require_geo_lon_strict_greater")!=9
        or f.get("require_geo_lat_strict_greater")!=50
        or f.get("require_UTC_DOY_start_inclusive")!=74
        or f.get("require_UTC_DOY_end_inclusive")!=191
        or f.get("only_positive_timestamp_deltas_within_same_year_id") is not True
        or f.get("zero_time_duplicates_counted_separately") is not True
        or [x["id"] for x in f["cohorts"]]!=[
            "all_linked_geo_season_years","source_primary_gt800_eligible_years"]
        or [x["min_fix_count"] for x in f["cohorts"]]!=[1,801]
        or [x["min_inclusive"] for x in f["time_gap_bins_seconds"]]!=[0,300,900,1800,2700,3300,3900,4500,7200]
        or [x["max_exclusive"] for x in f["time_gap_bins_seconds"]]!=[300,900,1800,2700,3300,3900,4500,7200,None]
        or s["observed_first"]["stages"][4]!=["S4_gt_800_valid_GPS_event_rows_after_S3",99,49,60,14]
        or c["biological_interpretation"]["red_kite_biological_terminal"]!="HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER"
        or c["biological_interpretation"]["BOP_historical_terminal"]!="empirical_state_prediction_mixed"
    ):
        raise ValueError("frozen original source cadence/source ID conditions drifted")
    if z[1]["name"]!="GER_trackingdata.csv" or z[0]["allowed_fields"]!=["year_id","bird_id"]:
        raise ValueError("source key or GPS whitelist modified")
    return c,h

def read_geo_season_GPS(lines,canonical:dict[str,str],gps_header:bytes)->tuple[dict[str,list[datetime]],dict]:
    first=next(lines,None)
    if first!=gps_header:
        raise ValueError("original GPS header not observed before data")
    groups=defaultdict(list)
    rows=invalid=unlinked=mismatch=selected=0
    for raw in lines:
        rows+=1
        try:
            rec=next(csv.reader([raw.decode("utf-8")],strict=True))
            if len(rec)!=7:
                raise ValueError("GPS schema deviates from seven columns")
            year,bird,when,x,y,_,_=rec
            dt=_timestamp(when)
            lat,lon=float(y),float(x)
            if not (year and bird and math.isfinite(lat) and math.isfinite(lon)
                    and -90<=lat<=90 and -180<=lon<=180):
                raise ValueError("missing or malformed original GPS coordinate")
        except (ValueError,UnicodeError,csv.Error,OverflowError):
            invalid+=1
            continue
        expected=canonical.get(year)
        if expected is None:
            unlinked+=1
            continue
        if expected!=bird:
            mismatch+=1
            continue
        if lon<=9 or lat<=50 or not (74<=dt.timetuple().tm_yday<=191):
            continue
        selected+=1
        groups[year].append(dt)
    counts={"original_GPS_physical_lines":rows,"malformed_GPS_rows":invalid,
            "rows_from_unlisted_season_ID":unlinked,"wrong_bird_ID_for_known_season_rows":mismatch,
            "geo_season_source_events":selected}
    return groups,counts

def summarize_intervals(groups:dict[str,list[datetime]],canonical:dict[str,str],
                        bin_specs:list[dict],cohorts:list[dict])->list[dict]:
    if [x["min_fix_count"] for x in cohorts]!=[1,801]:
        raise ValueError("source cadence cohorts may not be changed after opening original GPS")
    out=[]
    for cohort in cohorts:
        selected={y:t for y,t in groups.items() if len(t)>=cohort["min_fix_count"]}
        birdstrings={canonical[y] for y in selected}
        intervals=[]
        zero=0
        seasons_subhourly=0
        for year,ts in selected.items():
            ordered=sorted(ts)
            seen_short=False
            for before,after in zip(ordered,ordered[1:]):
                seconds=int((after-before).total_seconds())
                if seconds<0:
                    raise ValueError("unexpected negative gap after sorted timestamps")
                if seconds==0:
                    zero+=1
                    continue
                intervals.append(seconds)
                if seconds<3300:
                    seen_short=True
            if seen_short:
                seasons_subhourly+=1
        gaps=sorted(intervals)
        if not gaps:
            raise ValueError("cohort lacks any real positive GPS time interval")
        binnum=Counter()
        for seconds in gaps:
            found=next((b["id"] for b in bin_specs
                if seconds>=b["min_inclusive"] and
                (b["max_exclusive"] is None or seconds<b["max_exclusive"])),None)
            if found is None:
                raise ValueError("positive GPS time interval has no matching frozen bin")
            binnum[found]+=1
        n=len(gaps)
        def quantile(q):
            return round(gaps[max(0,math.ceil(n*q)-1)]/60,2)
        out.append({
            "cohort":cohort["id"],
            "selected_season_ID_strings":len(selected),
            "distinct_bird_ID_strings":len(birdstrings),
            "source_GPS_events_in_cohort":sum(map(len,selected.values())),
            "positive_consecutive_GPS_intervals":n,
            "zero_timestamp_duplicate_pairs":zero,
            "interval_bin_counts":{b["id"]:binnum[b["id"]] for b in bin_specs},
            "share_positive_gaps_under_55min":round(sum(t<3300 for t in gaps)/n,6),
            "share_positive_gaps_under_60min":round(sum(t<3600 for t in gaps)/n,6),
            "share_positive_gaps_55_to_65min":round(sum(3300<=t<3900 for t in gaps)/n,6),
            "season_ID_strings_with_any_under_55min_gap":seasons_subhourly,
            "global_nearest_rank_quantile_minutes":{"q10":quantile(.10),"q50":quantile(.50),"q90":quantile(.90)},
            "no_original_hourly_downsampler_identified":True,
        })
    return out

def run()->dict:
    c,h=_frozen()
    metadata=c["source_files"][0]
    metadata_head=h["verified_first_header"]["GER_indseasondata"]
    gps_head=h["verified_first_header"]["GER_trackingdata"]
    canonical,stats=_metadata_identity_map({
        "file":metadata["name"],
        "bytes":metadata["size"],
        "md5":metadata["md5"]},metadata_head)
    if len(canonical)!=159 or len(set(canonical.values()))!=63:
        raise ValueError("canonical original metadata count no longer 159/63")
    gps=c["source_files"][1]
    line=(",".join(gps_head["column_names"])+"\r\n").encode("utf-8")
    if hashlib.sha256(line).hexdigest()!=gps_head["header_sha256"]:
        raise ValueError("original GPS header integrity no longer matches provider")
    rows,counts=read_geo_season_GPS(iter(_source_lines({
        "filename":gps["name"],"bytes":gps["size"],"md5":gps["md5"]})),canonical,line)
    if counts["original_GPS_physical_lines"]!=500778 or counts["wrong_bird_ID_for_known_season_rows"]!=0:
        raise ValueError("original German GPS source count or exact season/bird mapping changed")
    cohorts=summarize_intervals(rows,canonical,
                c["predeclared_source_screen"]["time_gap_bins_seconds"],
                c["predeclared_source_screen"]["cohorts"])
    if [(z["selected_season_ID_strings"],z["distinct_bird_ID_strings"]) for z in cohorts]!=[(159,63),(99,49)]:
        raise ValueError("precommitted cohort dimensions not recovered; no new archive interpretation")
    return {
        "schema_version":1,"status":"SOURCE_GPS_CADENCE_OBSERVED_ONLY",
        "preaccess_contract_sha256":hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "original_provider_GER_metadata_and_GPS_MD5_verified":True,
        "source_event_funnel":counts,
        "fixed_interval_cohorts":cohorts,
        "archived_GER_source_strictly_one_fix_per_hour":all(
            z["season_ID_strings_with_any_under_55min_gap"]==0 for z in cohorts),
        "original_60min_downsampling_method_identified":False,
        "no_exact_timestamps_positions_or_IDs_exported":True,
        "no_breeding_label_values_accessed":True,
        "no_model_probabilities_or_animal_gains_scored":True,
        "BOP_historical_terminal":"empirical_state_prediction_mixed",
        "red_kite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    if args.out.resolve() in (CONTRACT.resolve(),HEADERS.resolve(),STAGE.resolve()):
        raise ValueError("must never overwrite original contract or first-source receipts")
    try:
        result=run()
    except (OSError,ValueError,UnicodeError,csv.Error,StopIteration) as exc:
        result={
            "schema_version":1,"status":"HOLD_GER_SOURCE_GPS_CADENCE",
            "error_type":type(exc).__name__,
            "no_exact_timestamps_positions_or_IDs_exported":True,
            "no_breeding_label_values_accessed":True,
            "no_model_probabilities_or_animal_gains_scored":True,
            "BOP_historical_terminal":"empirical_state_prediction_mixed",
            "red_kite_biological_terminal":"HOLD_NO_FROZEN_NEW_NEST_STATE_MODEL_OR_IDENTITY_ROSTER",
        }
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    if result["status"]!="SOURCE_GPS_CADENCE_OBSERVED_ONLY":
        raise SystemExit("SOURCE_GPS_CADENCE_HOLD: biological group inference remains frozen")

if __name__=="__main__":
    main()
