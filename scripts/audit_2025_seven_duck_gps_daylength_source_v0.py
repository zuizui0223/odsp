#!/usr/bin/env python3
"""Source-only seven dabbling duck species GPS feasibility and date support.

Verify original first-party Zenodo MD5. Read original timestamp/coordinates
transiently to test SAME INDIVIDUAL × same 0.5-degree coarse region × Dec
solstice year on both increasing/falling daylength. NEVER analyze numerical
GPS speed values, emit location/time/individual IDs or infer behavior.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime,date
import hashlib
import json
import math
from pathlib import Path

SOURCE_DOI="10.5281/zenodo.16940654"
SOURCE_URL="https://zenodo.org/records/16940654/files/250823_LNU_dabbling_ducks_hourly.csv?download=1"
PINNED_MD5="1972d0ef08b83c2b88a169ba07bb48b3"
MAX_FILE_BYTES=60_000_000
REQUIRED_FIELDS=(
    "study.name","individual.id","individual.taxon.canonical.name",
    "timestamp","location.long","location.lat","ground.speed"
)
MIN_DATE_EACH_BRANCH=7
MIN_SPEED_FIXES_EACH_BRANCH=15
MIN_N_INDEPENDENT_INDIVIDUALS=10
MIN_SPECIES=2
MIN_COARSE_CELLS=2
DAY_K_MIN=7
DAY_K_MAX=160
COARSE_DEGREE=0.5

def schema_key(x:str)->str:
    return "".join(c for c in x.casefold() if c.isalnum())

def pinned_md5(path:Path)->str:
    if path.stat().st_size>MAX_FILE_BYTES:
        raise ValueError("HOLD_ORIGINAL_GPS_FILE_SIZE_EXCEEDS_BUDGET")
    digest=hashlib.md5()
    with path.open("rb") as h:
        for c in iter(lambda:h.read(1024*1024),b""):
            digest.update(c)
    if digest.hexdigest()!=PINNED_MD5:
        raise ValueError("HOLD_ORIGINAL_GPS_MD5_MISMATCH")
    return digest.hexdigest()

def solstice_branch(d:date,lat:float):
    if abs(lat)<1.0:return None
    year=d.year if d.month>=7 else d.year-1
    k=(d-date(year,12,21)).days
    if not (DAY_K_MIN<=abs(k)<=DAY_K_MAX):return None
    north=lat>=1
    # Northern hemisphere decreasing daylength before Dec solstice.
    # Southern hemisphere increasing daylength before Dec solstice.
    rising=(k>0) if north else (k<0)
    return year,"rising" if rising else "falling"

def date_support(study,animal,taxon,instant,lat,lon):
    v=solstice_branch(instant.date(),lat)
    if not v:return None
    year,branch=v
    if not (-90<=lat<=90 and -180<=lon<=180):return None
    lat_cell=math.floor(lat/COARSE_DEGREE)
    lon_cell=math.floor(lon/COARSE_DEGREE)
    key=(study,animal,taxon,year,lat_cell,lon_cell)
    return key,branch

def interval_bin(hours:float)->str:
    if hours<=0:return "duplicate_or_nonincreasing"
    if hours<=1.5:return "0-1.5"
    if hours<=3:return "1.5-3"
    if hours<=6:return "3-6"
    if hours<=12:return "6-12"
    return ">12"

def parse_original_time(value:str)->datetime:
    # Original Movebank source specifies UTC. Drop no timezone conversion.
    v=value.strip()
    if v.endswith("Z"):v=v[:-1]
    t=datetime.fromisoformat(v)
    if t.tzinfo is not None:
        raise ValueError("HOLD_TIMEZONE_AWARE_RAW_SOURCE_NOT_EXPECTED")
    return t

def analyze(path:Path)->dict:
    md5=pinned_md5(path)
    rows_total=0
    invalid_time=invalid_location=0
    speed_nonmissing=Counter()
    total_species=Counter()
    individual_members=defaultdict(set)
    fix_times=defaultdict(list)
    cells=defaultdict(lambda:{
        "rising":{"dates":set(),"speed_fixes":0,"all_fixes":0},
        "falling":{"dates":set(),"speed_fixes":0,"all_fixes":0}
    })
    with path.open(newline="",encoding="utf-8-sig") as h:
        r=csv.DictReader(h)
        header=r.fieldnames or []
        normalized={schema_key(n):n for n in header}
        missing=[n for n in REQUIRED_FIELDS if schema_key(n) not in normalized]
        if missing:
            raise ValueError("HOLD_REQUIRED_PUBLIC_GPS_SCHEMA_MISSING")
        columns={n:normalized[schema_key(n)] for n in REQUIRED_FIELDS}
        for row in r:
            rows_total+=1
            study=row[columns["study.name"]].strip()
            animal=row[columns["individual.id"]].strip()
            taxon=row[columns["individual.taxon.canonical.name"]].strip()
            if not (study and animal and taxon):continue
            total_species[taxon]+=1
            individual_members[taxon].add((study,animal))
            try:
                instant=parse_original_time(row[columns["timestamp"]])
            except (ValueError,TypeError):
                invalid_time+=1
                continue
            fix_times[(study,animal)].append(instant)
            try:
                lat=float(row[columns["location.lat"]])
                lon=float(row[columns["location.long"]])
                if not (math.isfinite(lat) and math.isfinite(lon)):
                    raise ValueError("nonfinite")
            except (ValueError,TypeError):
                invalid_location+=1
                continue
            speed=row[columns["ground.speed"]]
            # Source-only binary availability, never use speed magnitude as response.
            try:
                speed_available=speed is not None and math.isfinite(float(speed)) and float(speed)>=0
            except (ValueError,TypeError):
                speed_available=False
            if speed_available:speed_nonmissing[taxon]+=1
            support=date_support(study,animal,taxon,instant,lat,lon)
            if support is None:continue
            key,branch=support
            record=cells[key][branch]
            record["dates"].add(instant.date())
            record["all_fixes"]+=1
            if speed_available:record["speed_fixes"]+=1

    gap_bins=Counter()
    negative_time_gap_anomalies=0
    for times in fix_times.values():
        times.sort()
        for prev,cur in zip(times,times[1:]):
            hours=(cur-prev).total_seconds()/3600
            if hours<0:negative_time_gap_anomalies+=1
            gap_bins[interval_bin(hours)]+=1

    support_summary=defaultdict(lambda:{
        "individuals":set(),"eligible_groups":0,"coarse_covered_cells":set(),
        "date_pairs_upper_bound":0,"speed_fixes_in_both":0,
    })
    eligible_source_individuals=set()
    eligible_source_cells=set()
    for key,parts in cells.items():
        study,animal,taxon,year,latcell,loncell=key
        up=parts["rising"];down=parts["falling"]
        if (len(up["dates"])<MIN_DATE_EACH_BRANCH
            or len(down["dates"])<MIN_DATE_EACH_BRANCH
            or up["speed_fixes"]<MIN_SPEED_FIXES_EACH_BRANCH
            or down["speed_fixes"]<MIN_SPEED_FIXES_EACH_BRANCH):continue
        v=support_summary[taxon]
        v["individuals"].add((study,animal))
        v["coarse_covered_cells"].add((latcell,loncell))
        v["eligible_groups"]+=1
        v["date_pairs_upper_bound"]+=min(len(up["dates"]),len(down["dates"]))
        v["speed_fixes_in_both"]+=up["speed_fixes"]+down["speed_fixes"]
        eligible_source_individuals.add((study,animal))
        eligible_source_cells.add((latcell,loncell))
    species_out=[]
    for taxon in sorted(total_species):
        support=support_summary[taxon]
        species_out.append({
            "published_source_taxon":taxon,
            "original_fix_rows":int(total_species[taxon]),
            "individual_ID_count":len(individual_members[taxon]),
            "GPS_ground_speed_nonmissing_row_count":int(speed_nonmissing[taxon]),
            "both_branch_same_0p5deg_individual_cycle_groups":support["eligible_groups"],
            "distinct_individuals_with_both_branch_support":len(support["individuals"]),
            "approximate_both_branch_matched_date_count_upper_bound_not_actual_photoperiod_matches":
                support["date_pairs_upper_bound"],
            "approximate_supported_fixed_speed_observation_count":support["speed_fixes_in_both"],
            "number_of_0p5degree_cells_with_support":len(support["coarse_covered_cells"])
        })
    supported_species=sum(x["distinct_individuals_with_both_branch_support"]>0 for x in species_out)
    ready=(len(eligible_source_individuals)>=MIN_N_INDEPENDENT_INDIVIDUALS
           and supported_species>=MIN_SPECIES and len(eligible_source_cells)>=MIN_COARSE_CELLS)
    return {
        "status":("ORIGINAL_SOURCE_TIMESTAMP_AND_BRANCH_FEASIBILITY_VERIFIED"
                  if ready else "ORIGINAL_SOURCE_VERIFIED_BUT_SAME_INDIVIDUAL_BRANCH_FEASIBILITY_HOLD"),
        "source_url":SOURCE_URL,"source_doi":SOURCE_DOI,
        "source_original_md5":md5,"source_file_size":path.stat().st_size,
        "source_header_columns_only":header,
        "source_total_GPS_fix_rows":rows_total,
        "records_with_invalid_UTC_time":invalid_time,
        "records_with_invalid_GPS_latlong":invalid_location,
        "original_fix_interval_binned_counts":dict(gap_bins),
        "per_taxon_no_individual_locations_or_IDs":species_out,
        "same_coarse_region_both_branch_supported_individuals_total":len(eligible_source_individuals),
        "same_coarse_region_both_branch_supported_species":supported_species,
        "same_coarse_region_both_branch_supported_cells":len(eligible_source_cells),
        "calendar_and_sensor_eligibility_rule":{
            "UTC_date_solstice_k_days":[DAY_K_MIN,DAY_K_MAX],
            "minimum_distinct_UTC_dates_per_branch":MIN_DATE_EACH_BRANCH,
            "minimum_valid_original_speed_fix_rows_per_branch":MIN_SPEED_FIXES_EACH_BRANCH,
            "coarse_same_geo_cell_size_degrees":COARSE_DEGREE,
            "publication_corroboration":"Original dataset itself is published 2025 and source only; this does not establish photoperiod date matching, activity or comparative behavior."
        },
        "GPS_speed_values_as_animal_behavior_analyzed":False,
        "raw_locations_individual_IDs_or_exact_time_exported":False,
        "actual_matched_daylength_or_true_GPS_sampling_effort_calibrated":False,
        "independent_biome_animal_hysteresis_or_global_generality_proven":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    try:
        result=analyze(a.input)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        result={
            "status":"HOLD_ORIGINAL_DUCK_GPS_SOURCE_AUTHENTICITY_OR_SCHEMA",
            "exception_type":type(exc).__name__,
            "no_GPS_animal_movement_outcome_claimed":True
        }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "status":result["status"],"source_fix_rows":result.get("source_total_GPS_fix_rows"),
        "supported_individuals":result.get("same_coarse_region_both_branch_supported_individuals_total"),
        "supported_species":result.get("same_coarse_region_both_branch_supported_species"),
        "species":result.get("per_taxon_no_individual_locations_or_IDs"),
        "behavior_analyzed":False
    },sort_keys=True))
    if result["status"].startswith("HOLD_ORIGINAL_DUCK_GPS_SOURCE_AUTHENTICITY"):
        raise SystemExit(2)

if __name__=="__main__":main()
