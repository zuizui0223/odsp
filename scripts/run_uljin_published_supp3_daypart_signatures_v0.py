#!/usr/bin/env python3
"""Calculate biological contrasts from the authentic *published aggregate* TSV.

This does NOT import the original NIE EcoBank event/operation ZIP and CANNOT
compute station-stratified, original 41 matched day pairs, detector-q adjusted
or causal ecological effects. The estimands are descriptive, whole-period,
civil-twilight-based, and post-outcome exploratory.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from itertools import combinations

from inspect_uljin_published_supp3_aggregate_v0 import download, verified_zip_members

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_PUBLISHED_SUPPL3_DAYPART_SIGNATURE_V0_CONTRACT.json"
PERIODS=("daytime","crepuscular","nighttime")
TOTAL_N=4623


def _close(a:float,b:float, *,tol:float=1e-7)->bool:
    return abs(a-b) <= tol * max(1,abs(b))


def evaluate(contract:dict, archive:bytes)->dict:
    if (contract.get("schema_version")!=1
        or contract.get("contract_id")!="uljin_published_supp3_whole_period_rate_signature_v0"
        or contract.get("stage")!="POST_SOURCE_EXPOSURE_EXPLORATORY_REANALYSIS_NOT_PREREGISTERED"
        or contract.get("original_physical_camera_station_operation_exposure_confirmed") is not False
        or contract.get("original_2022_fixed_41_matched_pairs_analyzed") is not False
        or contract.get("inferential_p_value_permitted") is not False):
        raise ValueError("HOLD_WRONG_PUBLISHED_POST_OUTCOME_SOURCE_CONTRACT")
    _,datasets=verified_zip_members(archive)
    if len(datasets)!=1 or datasets[0]["status"]!="PUBLISHED_AGGREGATE_TABLE_ONLY":
        raise ValueError("HOLD_SOURCE_NOT_SAFE_AGGREGATE_TABLE")
    table=datasets[0]
    if table["member_name"]!=contract["source"]["member"]:
        raise ValueError("HOLD_WRONG_PUBLISHED_SUPPL3_MEMBER")
    expected_headers=["Species","diel_period","n","n_total","prop_pct","hours_total","detections_per_hour","detections_per_100h"]
    if table["columns"]!=expected_headers:
        raise ValueError("HOLD_UNEXPECTED_PUBLISHED_AGGREGATE_SCHEMA")
    species=contract["species"]
    if set(species)!= {"Long-tailed goral","Siberian roe deer","Water deer","Wild boar"}:
        raise ValueError("HOLD_FOUR_TAXA_NOT_PRESERVED")
    if contract["prescribed_diel_classes"]!=list(PERIODS) or table["row_count"]!=len(species)*len(PERIODS):
        raise ValueError("HOLD_INVALID_PUBLISHED_DAYPART_ROSTER")

    records={}
    for row in table["rows"]:
        sp=row["Species"]
        period=row["diel_period"]
        if sp not in species or period not in PERIODS or (sp,period) in records:
            raise ValueError("HOLD_DUPLICATE_OR_OUT_OF_SCOPE_SOURCE_ROW")
        try:
            count=int(row["n"])
            n_total=int(row["n_total"])
            percent=float(row["prop_pct"])
            hours=float(row["hours_total"])
            rateh=float(row["detections_per_hour"])
            rate100=float(row["detections_per_100h"])
        except (ValueError,TypeError) as e:
            raise ValueError("HOLD_NONNUMERIC_PUBLISHED_TABLE_FIELD") from e
        if (count<0 or n_total!=species[sp]
            or not math.isfinite(hours) or hours<=0
            or not _close(hours,float(contract["published_period_hours"][period]))
            or not _close(rateh,count/hours)
            or not _close(rate100,count*100/hours)
            or abs(percent-count/n_total*100)>.055):
            raise ValueError("HOLD_INCONSISTENT_PUBLISHED_SOURCE_RATE")
        records[(sp,period)]={"n":count,"rate100":rate100,"hours":hours}
    if len(records)!=12 or sum(x["n"] for x in records.values())!=contract["published_source_total_detections"]:
        raise ValueError("HOLD_PUBLISHED_12_CELL_TOTAL_MISMATCH")
    for sp,total in species.items():
        if sum(records[(sp,p)]["n"] for p in PERIODS)!=total:
            raise ValueError("HOLD_PUBLISHED_SPECIES_TOTAL_MISMATCH")
    per_hours={p:float(contract["published_period_hours"][p]) for p in PERIODS}
    sum_hours=sum(per_hours.values())
    if not _close(sum_hours,9288.0) or not _close(sum_hours,contract["published_period_duration_hour_sum"]):
        raise ValueError("HOLD_PUBLISHED_CALENDAR_DURATION_SUM_MISMATCH")

    profiles=[]
    for sp in species:
        d,c,n=[records[(sp,p)]["rate100"] for p in PERIODS]
        profile={
            "species":sp,
            "period_counts":{p:records[(sp,p)]["n"] for p in PERIODS},
            "detections_per_100_published_calendar_period_hours":{p:round(records[(sp,p)]["rate100"],8) for p in PERIODS},
            "night_to_day_published_period_rate_ratio":round(n/d,8),
            "crepuscular_to_day_published_period_rate_ratio":round(c/d,8),
        }
        profiles.append(profile)
    comparisons=[]
    for a,b in combinations(profiles,2):
        ratio=a["night_to_day_published_period_rate_ratio"]/b["night_to_day_published_period_rate_ratio"]
        comparisons.append({
            "species_a":a["species"],
            "species_b":b["species"],
            "ratio_of_night_day_rate_ratios":round(ratio,8),
            "absolute_log_ratio":round(abs(math.log(ratio)),8),
            "significance_claimed":False,
        })
    most=max(comparisons,key=lambda x:x["absolute_log_ratio"])
    return {
       "status":"REPRODUCED_PUBLISHED_DAYPART_POOLED_DESCRIPTIVE_SIGNATURE_ONLY",
       "source_doi":contract["source"]["doi"],
       "independently_verified_published_zip_md5":True,
       "published_supplement_member":table["member_name"],
       "species_count":4,"diel_categories":list(PERIODS),
       "published_aggregate_rows":12,
       "reproduced_total_events":sum(x["n"] for x in records.values()),
       "published_hours_per_period":per_hours,
       "sum_published_period_hours":round(sum_hours,6),
       "calendar_24h_day_equivalent":round(sum_hours/24,6),
       "original_hourly_camera_operation_verified":False,
       "per_physical_station_effort_adjustment_claimed":False,
       "frozen_original_41_day_pairs_tested":False,
       "civil_twilight_is_NOT_daylight_edge_of_original_H1":True,
       "species_profiles":profiles,
       "six_pairwise_night_to_day_rate_ratio_comparisons":comparisons,
       "posthoc_largest_descriptive_night_day_divergence":most,
       "site_clustered_uncertainty_available":False,
       "inferential_p_value_computed":False,
       "latent_activity_or_competition_claimed":False
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--offline-zip",type=Path)
    args=p.parse_args()
    try:
        raw=args.offline_zip.read_bytes() if args.offline_zip else download()
        result=evaluate(json.loads(CONTRACT.read_text()),raw)
    except Exception as error:
        result={"status":"HOLD_PUBLISHED_SUPPL3_DAYPART_COMPARISON","error_class":type(error).__name__,
                "biological_claim_computed":False}
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
