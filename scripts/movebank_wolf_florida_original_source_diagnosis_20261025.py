#!/usr/bin/env python3
"""Explain why two public GPS sources yielded no same-photoperiod comparison.

Source-validation-only diagnosis of original Yellowstone wolves and Florida
white-tailed deer (previous 3-source file roster). NO GPS displacements,
movement speeds, original marked IDs or precise track coordinates/times
are exported. Provider ORIGINAL UUID and MD5 are checked; no repair/retuning.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter,defaultdict
from datetime import date
import json
import math
from pathlib import Path

from scripts.movebank_native_ecology_20261019 import (
    HERE,original_files,checksum_and_download,parse_time,
    solar_period,daylength,greedy_pairs
)
from scripts.movebank_same_taxon_three_source_only_20261025 import (
    contract_sources,source_metadata_gate
)

LABELS=("wolves_yellowstone","white_tail_florida")

def timestamp_structure(raw):
    """No original actual dates/times emitted, only lexical schema shape."""
    text=(raw or "").strip()[:45]
    def char(x):
        if x.isdigit():return "9"
        if x.isalpha():return "A"
        return x
    return "".join(char(x) for x in text)

def columns(c):
    names=list(c or [])
    def col(*opts):
        return next((n for n in names if n.lower().strip() in opts),None)
    return {
        "time":col("timestamp","event-date","eventdate"),
        "ind":col("individual-local-identifier","individual-id","animal-id",
                  "individual local identifier"),
        "lat":col("location-lat","location-latitude","latitude"),
        "lon":col("location-long","location-longitude","longitude")
    }

def inspect_failure_modes(path):
    counts=Counter()
    time_patterns=Counter()
    valid_days=defaultdict(lambda:{"day":0,"night":0})
    lat_sum=defaultdict(lambda:[0.,0])
    year_month=Counter()
    with path.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        schema=columns(reader.fieldnames)
        if any(x is None for x in schema.values()):
            return {"status":"HOLD_REQUIRED_GPS_CANONICAL_COLUMNS_MISSING",
                    "required_column_presence":{k:v is not None for k,v in schema.items()},
                    "original_source_data_rows_scanned":0}
        for row in reader:
            counts["rows"]+=1
            raw=row.get(schema["time"],"")
            ts=parse_time(raw)
            ind=(row.get(schema["ind"]) or "").strip()
            try:
                lat=float(row.get(schema["lat"],""))
                lon=float(row.get(schema["lon"],""))
                valid_location=(math.isfinite(lat) and math.isfinite(lon)
                                and -90<=lat<=90 and -180<=lon<=180)
            except (TypeError,ValueError):
                valid_location=False
            if ts is None:
                counts["invalid_or_missing_timestamp"]+=1
                time_patterns[timestamp_structure(raw)]+=1
            else:
                counts["parseable_timestamp"]+=1
            if not ind:counts["missing_source_individual_identifier"]+=1
            else:counts["present_source_individual_identifier"]+=1
            if not valid_location:counts["invalid_or_missing_original_WGS84_position"]+=1
            else:counts["parseable_original_WGS84_position"]+=1
            if ts is None or not ind or not valid_location:
                counts["non_admitted_source_rows"]+=1
                continue
            counts["fully_valid_source_rows"]+=1
            year_month[(ts.year,ts.month)]+=1
            d,p=solar_period(ts,lat,lon)
            valid_days[(ind,d)][p]+=1
            lat_sum[ind][0]+=lat
            lat_sum[ind][1]+=1
    eligible=defaultdict(dict)
    months_by_year=defaultdict(set)
    for (ind,d),parts in valid_days.items():
        if parts["day"]>=3 and parts["night"]>=3:
            eligible[(ind,d.year)][d]=parts
            months_by_year[d.year].add(d.month)
    with_dates=Counter()
    by_year_obs=defaultdict(dict)
    for (ind,yr),days in eligible.items():
        if not days:continue
        pivot=date(yr,6,21)
        rising={d:v for d,v in days.items() if d<pivot}
        falling={d:v for d,v in days.items() if d>pivot}
        with_dates["individual_years_with_either_branch"]+=1
        if rising:with_dates["individual_years_with_rising"]+=1
        if falling:with_dates["individual_years_with_falling"]+=1
        if rising and falling:with_dates["individual_years_with_both_branches"]+=1
        lat=lat_sum[ind][0]/lat_sum[ind][1]
        if lat>0:
            datepairs=greedy_pairs(rising,falling,lat)
            if datepairs:with_dates["individual_years_with_ge1_matched_dates"]+=1
            if len(datepairs)>=5:with_dates["individual_years_with_ge5_matched_dates"]+=1
            if len(datepairs)>=10:with_dates["individual_years_with_ge10_matched_dates"]+=1
            with_dates["largest_same_individual_year_matched_date_pairs"]=max(
                with_dates["largest_same_individual_year_matched_date_pairs"],len(datepairs))
    return {
        "status":"ORIGINAL_SOURCE_ONLY_GPS_SCHEMA_AND_SAMPLING_DIAGNOSTIC",
        "source_row_reason_counts":dict(counts),
        "invalid_timestamp_lexical_shapes_ONLY_no_dates":
            [{"shape":shape,"count":n} for shape,n in time_patterns.most_common(5)],
        "source_observed_calendar_year_count_with_some_day_night_admission":
            len(months_by_year),
        "source_years_with_admissible_both_zone_dates_count":
            len(months_by_year),
        "source_animal_year_calendar_opportunity":dict(with_dates),
        "original_speed_or_movement_intervals_inspected":False,
        "original_GPS_ID_coordinates_timestamps_exported":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    opts=p.parse_args()
    opts.output_dir.mkdir(parents=True,exist_ok=True)
    sources={x["label"]:x for x in contract_sources()}
    results=[]
    for label in LABELS:
        source=sources[label]
        output={"source_label":label,"original_provider_MD5":source["checksum_md5"],
                "status":"HOLD_SOURCE_SCHEMA_DIAGNOSTIC_FAILED",
                "animal_ecological_effect_computed":False}
        tmp=opts.output_dir/("diagnostic_"+label+".csv")
        try:
            f=source_metadata_gate(source,original_files(source["package_uuid"]))
            result=checksum_and_download(f,tmp)
            output.update(original_file_verified=result,
                          source_diagnostic=inspect_failure_modes(tmp),
                          status="SOURCE_ONLY_DIAGNOSTIC_COMPLETED")
        except Exception as exc:
            output.update(error_type=type(exc).__name__,reason=str(exc)[:190])
        finally:
            tmp.unlink(missing_ok=True)
        results.append(output)
        print("NEW_GPS_SOURCE_SCHEMA_DIAG "+json.dumps(output,sort_keys=True),flush=True)
    receipt={"status":"WOLF_AND_DEER_SOURCE_ONLY_ROOT_CAUSE",
             "source_originals":[x["source_label"] for x in results],
             "sources":results,
             "no_GPS_displacement_or_behaviour_calculated":True,
             "no_original_animals_GPS_coordinates_or_timestamp_exported":True,
             "no_alternative_source_data_or_matching_rules_used":True}
    (opts.output_dir/"wolf_and_deer_original_source_only_diagnostic_20261025.json").write_text(
        json.dumps(receipt,sort_keys=True,indent=2)+"\n")

if __name__=="__main__":
    main()
