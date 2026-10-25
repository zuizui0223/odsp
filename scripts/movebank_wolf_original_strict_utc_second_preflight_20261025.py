#!/usr/bin/env python3
"""ONLY test one hypothesized malformed UTC timestamp pattern in original wolves.

Canonical Movebank parser failed all 23,604 rows despite original source ID
and coordinates being present. Strictly interpret ONLY
YYYY-MM-DD HH:MM:<one digit second>Z to normalized UTC with a LEADING ZERO in
seconds. No other suffix/date repair, no movement speed, original ID/position
or timestamp export, no new ecological response.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter,defaultdict
from datetime import date,datetime,timezone
import json
import math
from pathlib import Path
import re

from scripts.movebank_native_ecology_20261019 import (
    original_files,checksum_and_download,parse_time,solar_period,greedy_pairs
)
from scripts.movebank_same_taxon_three_source_only_20261025 import (
    contract_sources,source_metadata_gate
)

PATTERN=re.compile(r"^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}):(\d)Z$")
SOURCE_EXPECTED_ROWS=23604
SOURCE_LABEL="wolves_yellowstone"

def parse_one_digit_source_UTC(value:str):
    original=parse_time(value)
    if original is not None:return original,"ORIGINAL_ALREADY_ISO"
    s=(value or "").strip()
    m=PATTERN.fullmatch(s)
    if m is None:return None,"NOT_STRICT_ONE_DIGIT_UTC_Z"
    candidate=f"{m.group(1)}T{m.group(2)}:0{m.group(3)}+00:00"
    try:
        stamp=datetime.fromisoformat(candidate).astimezone(timezone.utc).replace(tzinfo=None)
        return stamp,"UTC_ONE_DIGIT_SECONDS_Z_REPAIRED"
    except ValueError:
        return None,"INVALID_DATE_TIME_AFTER_STRICT_Z_REPAIR"

def calendar_only_stream(path:Path):
    count=Counter()
    by_ind_day=defaultdict(lambda:{"day":0,"night":0})
    by_ind_lat=defaultdict(lambda:[0.,0])
    suffix_counts=Counter()
    with path.open(newline="",encoding="utf-8-sig") as h:
        rd=csv.DictReader(h)
        cols={x.lower().strip():x for x in rd.fieldnames or []}
        required={
            "ts":"timestamp",
            "ind":"individual-local-identifier",
            "lat":"location-lat",
            "lon":"location-long",
        }
        if any(v not in cols for v in required.values()):
            return {
                "status":"HOLD_ORIGINAL_GPS_REQUIRED_COLUMNS_MISSING",
                "missing_column_types":[k for k,v in required.items() if v not in cols],
            }
        for row in rd:
            count["original_rows"]+=1
            raw=(row.get(cols["timestamp"]) or "").strip()
            timestamp,category=parse_one_digit_source_UTC(raw)
            count[category]+=1
            if category=="NOT_STRICT_ONE_DIGIT_UTC_Z":
                suffix=raw[-1:] or "NONE"
                suffix_counts["LAST_IS_Z" if suffix=="Z" else "LAST_NOT_Z"]+=1
            ind=(row.get(cols["individual-local-identifier"]) or "").strip()
            try:
                lat=float(row[cols["location-lat"]])
                lon=float(row[cols["location-long"]])
                pos_ok=math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180
            except (TypeError,ValueError):
                pos_ok=False
            if not ind or not pos_ok:
                count["original_rows_with_missing_source_ID_or_position"]+=1
                continue
            if timestamp is None:
                count["valid_original_position_but_unresolved_timestamp"]+=1
                continue
            count["fully_parseable_after_only_strict_UTC_second_normalization"]+=1
            d,p=solar_period(timestamp,lat,lon)
            by_ind_day[(ind,d)][p]+=1
            by_ind_lat[ind][0]+=lat
            by_ind_lat[ind][1]+=1
    qualified=defaultdict(dict)
    for (ind,d),counts in by_ind_day.items():
        if counts["day"]>=3 and counts["night"]>=3:
            qualified[(ind,d.year)][d]=counts
    source_individuals_with_valid_days=set()
    year_n_pairs=Counter()
    for (ind,year),days in qualified.items():
        if not days:continue
        source_individuals_with_valid_days.add(ind)
        mid=date(year,6,21)
        rising={d:v for d,v in days.items() if d<mid}
        falling={d:v for d,v in days.items() if d>mid}
        if rising:year_n_pairs["source_animal_years_with_increasing_branch"]+=1
        if falling:year_n_pairs["source_animal_years_with_decreasing_branch"]+=1
        if rising and falling:year_n_pairs["animal_years_with_both_original_branches"]+=1
        if by_ind_lat[ind][1]<=0:continue
        lat=by_ind_lat[ind][0]/by_ind_lat[ind][1]
        if lat<=0:continue
        pairs=greedy_pairs(rising,falling,lat)
        if pairs:year_n_pairs["animal_years_with_ge1_5min_astro_matched_daypairs"]+=1
        if len(pairs)>=5:year_n_pairs["animal_years_with_ge5_matched_daypairs"]+=1
        if len(pairs)>=10:year_n_pairs["animal_years_with_ge10_matched_daypairs"]+=1
        year_n_pairs["maximum_observed_single_animal_year_datepairs"]=max(
            len(pairs),year_n_pairs["maximum_observed_single_animal_year_datepairs"]
        )
    fully_valid=count["fully_parseable_after_only_strict_UTC_second_normalization"]
    usable=(fully_valid==SOURCE_EXPECTED_ROWS and
            count["original_rows"]==SOURCE_EXPECTED_ROWS)
    return {
        "status":("STRICT_SINGLE_DIGIT_SECOND_Z_SOURCE_TIME_RECOVERED"
                  if usable else "HOLD_NOT_ALL_ORIGINAL_SOURCE_TIME_STRICTLY_RECOVERED"),
        "original_source_rows_expected":SOURCE_EXPECTED_ROWS,
        "original_source_row_status_counts":dict(count),
        "unrecognized_source_end_suffix_classes_only":dict(suffix_counts),
        "individuals_with_at_least_one_day_night_sampled_day":len(source_individuals_with_valid_days),
        "same_individual_year_observation_opportunity":dict(year_n_pairs),
        "gps_displacement_magnitudes_read":False,
        "gps_activity_or_ecological_hysteresis_estimated":False,
        "precise_original_timestamps_lats_lons_and_individuals_exported":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    s=next(z for z in contract_sources() if z["label"]==SOURCE_LABEL)
    destination=a.output_dir/"ORIGINAL_WOLF_SOURCE_NOT_TO_EXPORT.csv"
    try:
        origin=source_metadata_gate(s,original_files(s["package_uuid"]))
        download=checksum_and_download(origin,destination)
        out=calendar_only_stream(destination)
        out["original_provider_MD5_exact"]=s["checksum_md5"]
        out["original_download_provider_checksum_verified"]=download["provider_checksum_verified"]
    except Exception as exc:
        out={"status":"HOLD_ORIGINAL_WOLF_SOURCE_OR_STRICT_TIMESTAMP_DIAGNOSTIC",
             "exception_type":type(exc).__name__,"error_message":str(exc)[:150],
             "no_animal_activity_or_GPS_displacement_values_opened":True}
    finally:
        destination.unlink(missing_ok=True)
    (a.output_dir/"wolf_strict_UTC_single_digit_seconds_source_only_20261025.json").write_text(
        json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("WOLF_STRICT_UTC_SOURCE_ONLY "+json.dumps(out,sort_keys=True),flush=True)

if __name__=="__main__":main()
