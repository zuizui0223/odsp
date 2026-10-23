#!/usr/bin/env python3
"""First independent seven-species duck GPS solar-daylength movement-speed test.

ALL response choices registered before numeric GPS ground.speed opened, at:
research/DUCK_GPS_2025_SOLAR_MATCHED_SPEED_V0_CONTRACT.json

This is sensor-reported movement speed, not animal activity time budgets,
photoperiod memory, or cross-ecosystem causal evidence. No source animal IDs,
raw source coordinates, timestamps or individual effect sizes are exported.
"""
from __future__ import annotations

import argparse
from collections import defaultdict,Counter
from datetime import datetime,date
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

from scripts.audit_2025_seven_duck_gps_daylength_source_v0 import (
    analyze as original_source_audit, schema_key, parse_original_time,
    date_support, PINNED_MD5, REQUIRED_FIELDS, interval_bin
)

SOURCE_ORIGINAL_GPS_ROWS=294683
SOURCE_SUPPORT_PREVIEW_INDIVIDUALS=36
SOURCE_SPECIES_COUNT=7
SOLSTICE_YEARS=None
SOURCE_COARSE_DEGREE=.5
SUN_APPARENT_ZENITH_DEGREES=90.833
K_MIN,K_MAX=7,160
DATE_FIXES_EACH_ZONE_MIN=3
DATE_RATIO_MIN=.5
DATE_RATIO_MAX=2.0
DAYLENGTH_MATCH_MAX_MINUTES=5.0
MIN_MATCHED_DATES_PER_GROUP=5
MAX_GROUND_SPEED_MPS=60.0
INDEPENDENT_SPECIES_N_MIN=5

def solar_params(when:datetime):
    day=when.timetuple().tm_yday
    leap=(when.year%4==0 and (when.year%100!=0 or when.year%400==0))
    length=366 if leap else 365
    fraction=(when.hour+when.minute/60+when.second/3600-12)/24
    gamma=2*math.pi/length*(day-1+fraction)
    equation=229.18*(.000075+.001868*math.cos(gamma)-.032077*math.sin(gamma)
          -.014615*math.cos(2*gamma)-.040849*math.sin(2*gamma))
    decl=(.006918-.399912*math.cos(gamma)+.070257*math.sin(gamma)
          -.006758*math.cos(2*gamma)+.000907*math.sin(2*gamma)
          -.002697*math.cos(3*gamma)+.00148*math.sin(3*gamma))
    return equation,decl

def is_daylight_at_GPS_UTC(when:datetime,lat:float,lon:float):
    equation,decl=solar_params(when)
    true_solar_min=(
        when.hour*60+when.minute+when.second/60+equation+4*lon
    )%1440
    ha=math.radians(true_solar_min/4-180)
    phi=math.radians(lat)
    coszen=(math.sin(phi)*math.sin(decl)+
            math.cos(phi)*math.cos(decl)*math.cos(ha))
    return coszen>=math.cos(math.radians(SUN_APPARENT_ZENITH_DEGREES))

def modeled_photoperiod_minutes(day:date,lat:float):
    noon=datetime(day.year,day.month,day.day,12)
    _,dec=solar_params(noon)
    phi=math.radians(lat)
    a=math.cos(math.radians(SUN_APPARENT_ZENITH_DEGREES))
    cosha=(a-math.sin(phi)*math.sin(dec))/(math.cos(phi)*math.cos(dec))
    if abs(cosha)>1:
        return None
    return 8*math.degrees(math.acos(cosha))

def _daily_valid_sampling(day):
    return (len(day["day"])>=DATE_FIXES_EACH_ZONE_MIN and
            len(day["night"])>=DATE_FIXES_EACH_ZONE_MIN)

def balanced_pair(falling:dict,rising:dict):
    for z in ("day","night"):
        nf=len(falling[z]);nr=len(rising[z])
        if min(nf,nr)<DATE_FIXES_EACH_ZONE_MIN: return False
        ratio=nf/nr
        if not DATE_RATIO_MIN<=ratio<=DATE_RATIO_MAX:
            return False
    return True

def one_to_one_source_datepairs(days:dict,median_lat:float):
    falling=[];rising=[]
    for (branch,d),counts in days.items():
        if not _daily_valid_sampling(counts):continue
        photoperiod=modeled_photoperiod_minutes(d,median_lat)
        if photoperiod is None:continue
        if branch=="falling":falling.append((d,photoperiod))
        else:rising.append((d,photoperiod))
    # Greedy global matching by astronomy distance then dates; one UTC date
    # used at most once. Sensor speed magnitude not used for pair selection.
    candidate=[]
    for f,fl in falling:
        for r,rl in rising:
            dd=abs(fl-rl)
            if dd<=DAYLENGTH_MATCH_MAX_MINUTES:
                candidate.append((dd,f,r))
    candidate.sort(key=lambda v:(v[0],v[1],v[2]))
    f_used=set();r_used=set();pairs=[]
    for mismatch,f,r in candidate:
        if f in f_used or r in r_used:continue
        if not balanced_pair(days[("falling",f)],days[("rising",r)]):continue
        f_used.add(f);r_used.add(r)
        pairs.append((f,r,mismatch))
    return pairs,{
        "both_zone_source_days_falling":len(falling),
        "both_zone_source_days_rising":len(rising),
        "astronomy_potential_datepairs":len(candidate),
        "duty_balanced_unique_datepairs":len(pairs)
    }

def night_minus_day_median_log1p(day:dict):
    return statistics.median(day["night"])-statistics.median(day["day"])

def species_summary(individual_effects:dict)->dict:
    x=list(individual_effects.values())
    n=len(x)
    loo=[
        statistics.mean(x[:i]+x[i+1:])
        for i in range(n) if n>1
    ]
    return {
        "n_distinct_independent_individuals":n,
        "individual_effect_mean":statistics.mean(x) if n else None,
        "individual_effect_median":statistics.median(x) if n else None,
        "individuals_positive_delta":sum(a>0 for a in x),
        "individuals_negative_delta":sum(a<0 for a in x),
        "individuals_exactly_zero_delta":sum(a==0 for a in x),
        "leave_one_animal_out_species_mean_range_NOT_confidence_interval":
            [min(loo),max(loo)] if loo else None,
        "species_descriptive_support_qualified":n>=INDEPENDENT_SPECIES_N_MIN,
    }

def run(path:Path)->dict:
    initial=original_source_audit(path)
    if (initial["source_total_GPS_fix_rows"]!=SOURCE_ORIGINAL_GPS_ROWS
        or initial["same_coarse_region_both_branch_supported_individuals_total"]
        !=SOURCE_SUPPORT_PREVIEW_INDIVIDUALS
        or len(initial["per_taxon_no_individual_locations_or_IDs"])
        !=SOURCE_SPECIES_COUNT):
        raise ValueError("HOLD_FIRST_SOURCE_294683_36_ORIGINAL_AUDIT_NOT_REPRODUCED")
    day_groups=defaultdict(
        lambda:defaultdict(lambda:{"day":[],"night":[]})
    )
    site_latitudes=defaultdict(list)
    source_speed_gt_60=0
    missing_speed=0
    checked_rows=0
    valid_speed_rows=0
    with path.open(newline="",encoding="utf-8-sig") as h:
        r=csv.DictReader(h)
        normalized={schema_key(x):x for x in (r.fieldnames or [])}
        columns={x:normalized[schema_key(x)] for x in REQUIRED_FIELDS}
        for row in r:
            checked_rows+=1
            study=row[columns["study.name"]].strip()
            ident=row[columns["individual.id"]].strip()
            taxon=row[columns["individual.taxon.canonical.name"]].strip()
            if not all((study,ident,taxon)):continue
            try:
                instant=parse_original_time(row[columns["timestamp"]])
                lat=float(row[columns["location.lat"]])
                lon=float(row[columns["location.long"]])
                speed=float(row[columns["ground.speed"]])
                if not (math.isfinite(lat) and math.isfinite(lon)
                        and math.isfinite(speed) and 0<=speed
                        and -90<=lat<=90 and -180<=lon<=180):
                    raise ValueError("invalid")
            except (ValueError,TypeError,KeyError):
                missing_speed+=1
                continue
            if speed>MAX_GROUND_SPEED_MPS:
                source_speed_gt_60+=1
                continue
            valid_speed_rows+=1
            out=date_support(study,ident,taxon,instant,lat,lon)
            if out is None:continue
            key,branch=out
            z="day" if is_daylight_at_GPS_UTC(instant,lat,lon) else "night"
            logspeed=math.log1p(speed)
            day_groups[key][(branch,instant.date())][z].append(logspeed)
            site_latitudes[key].append(lat)

    if checked_rows!=SOURCE_ORIGINAL_GPS_ROWS:
        raise ValueError("HOLD_SOURCE_ROWS_DRIFT_WHEN_OPENING_GPS_SPEED")
    grouped_summary=defaultdict(lambda:{
        "individuals":defaultdict(list),
        "supported_groups":0,"supported_pair_dates":0,
        "groups_with_both_branches_source_fixes":0,
        "datepair_coverage_source_candidates":0,
        "effect_group_sign_positive":0,"effect_group_sign_negative":0,
        "photoperiod_daylength_mismatch_minutes":[],
    })
    total_groups=len(day_groups)
    groups_with_5_matches=0
    for key,days in day_groups.items():
        study,ident,taxon,year,latcell,loncell=key
        lat=statistics.median(site_latitudes[key])
        pairs,support=one_to_one_source_datepairs(days,lat)
        st=grouped_summary[taxon]
        if support["both_zone_source_days_falling"] and support["both_zone_source_days_rising"]:
            st["groups_with_both_branches_source_fixes"]+=1
        st["datepair_coverage_source_candidates"]+=support["astronomy_potential_datepairs"]
        if len(pairs)<MIN_MATCHED_DATES_PER_GROUP:continue
        group_effects=[
            night_minus_day_median_log1p(days[("falling",f)])
            -night_minus_day_median_log1p(days[("rising",r)])
            for f,r,diff in pairs
        ]
        group_mean=statistics.mean(group_effects)
        st["supported_groups"]+=1
        st["supported_pair_dates"]+=len(pairs)
        st["effect_group_sign_positive"]+=group_mean>0
        st["effect_group_sign_negative"]+=group_mean<0
        st["photoperiod_daylength_mismatch_minutes"].extend([v[2] for v in pairs])
        st["individuals"][(study,ident)].append(group_mean)
        groups_with_5_matches+=1

    species=[]
    individual_species_min_support_count=0
    n_individuals_unique=set()
    for tax in sorted(x["published_source_taxon"] for x in initial["per_taxon_no_individual_locations_or_IDs"]):
        st=grouped_summary[tax]
        individual_effects={
            animal:statistics.mean(groupmeans)
            for animal,groupmeans in st["individuals"].items()
        }
        n_individuals_unique.update(st["individuals"])
        row={
            "published_source_taxon":tax,
            "eligible_individual_region_solstice_groups":st["supported_groups"],
            "matched_balanced_daylength_datepairs":st["supported_pair_dates"],
            "both_branches_with_day_and_night_FIX_group_count":
                st["groups_with_both_branches_source_fixes"],
            "number_of_datepair_astro_candidates_before_matching":
                st["datepair_coverage_source_candidates"],
            "median_absolute_matched_photoperiod_mismatch_minutes":
                (statistics.median(st["photoperiod_daylength_mismatch_minutes"])
                 if st["photoperiod_daylength_mismatch_minutes"] else None),
            **species_summary(individual_effects)
        }
        individual_species_min_support_count+=row["species_descriptive_support_qualified"]
        species.append(row)

    return {
        "status":"INDEPENDENT_GPS_SOLAR_PHASE_MATCHED_SENSOR_SPEED_EXPLORATORY",
        "source":"https://zenodo.org/records/16940654",
        "source_original_md5":PINNED_MD5,
        "source_only_support_run":"https://github.com/zuizui0223/odsp/actions/runs/39090010649",
        "source_GPS_fix_rows_replayed":checked_rows,
        "source_groups_individual_0p5deg_solstice_with_any_speed":total_groups,
        "speed_rows_in_source_valid_0_to_60mps":valid_speed_rows,
        "source_speed_value_invalid_or_missing":missing_speed,
        "source_speed_values_over_60mps_excluded":source_speed_gt_60,
        "minimum_source_day_and_night_fixes_per_matched_UTC_day":DATE_FIXES_EACH_ZONE_MIN,
        "sensor_fix_balance_between_season_branches":[DATE_RATIO_MIN,DATE_RATIO_MAX],
        "actual_astronomical_daylength_max_difference_minutes":
            DAYLENGTH_MATCH_MAX_MINUTES,
        "minimum_unique_valid_datepairs_to_estimate_indiv_cell_year":
            MIN_MATCHED_DATES_PER_GROUP,
        "all_original_seven_taxa_species_results":species,
        "total_individuals_with_matched_duty_balanced_GPS_sensor_speed_outcomes":
            len(n_individuals_unique),
        "taxa_with_at_least_five_independent_individuals":
            individual_species_min_support_count,
        "comparison_to_Serengeti_camera_scale":"Different observation modality and taxon, NOT the original camera encounter odds.",
        "no_raw_source_GPS_coordinates_animals_or_datetimes_exported":True,
        "source_battery_sampling_and_fix_duty_unequal_potentially_confounded":True,
        "no_individual_behavioral_activity_or_endogenous_photoperiod_memory_identified":True,
        "no_independent_region_population_pvalues_or_true_animal_movement_causes_inferred":True
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    try:
        outcome=run(a.input)
    except (OSError,KeyError,ValueError,TypeError,IndexError) as exc:
        outcome={
            "status":"HOLD_GPS_SOURCE_OR_PRE_FROZEN_SOLAR_SAMPLING_RULE_FAILED",
            "exception_type":type(exc).__name__,
            "no_biological_GPS_ground_speed_result_inferred":True
        }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(outcome,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "status":outcome["status"],
        "source_rows":outcome.get("source_GPS_fix_rows_replayed"),
        "matched_individuals":outcome.get(
            "total_individuals_with_matched_duty_balanced_GPS_sensor_speed_outcomes"),
        "taxa_5plus_individuals":outcome.get(
            "taxa_with_at_least_five_independent_individuals"),
        "taxa":[
            {k:r.get(k) for k in (
                "published_source_taxon",
                "eligible_individual_region_solstice_groups",
                "matched_balanced_daylength_datepairs",
                "n_distinct_independent_individuals",
                "individual_effect_mean","individual_effect_median",
                "individuals_positive_delta","individuals_negative_delta",
                "species_descriptive_support_qualified"
            )} for r in outcome.get("all_original_seven_taxa_species_results",[])
        ],
        "latent_true_activity":False
    },sort_keys=True))
    if outcome["status"].startswith("HOLD"):
        raise SystemExit(2)

if __name__=="__main__":main()
