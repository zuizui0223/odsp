#!/usr/bin/env python3
"""POST-OUTCOME France Gyps 5km CERRA solar/wind day-context height-shape audit.

Previous source study 5km 28-bird/dual GPS+bariosensor height identity
results were already opened in an earlier source workflow. THIS IS A NEW
EXPLORATORY climate-conditioned association, not new confirmatory evidence.

One regional CERRA day has the SAME regime for all birds; all nulls shuffle
whole CALENDAR date labels synchronously within year-month across all birds.
"""
from __future__ import annotations
import argparse,csv,json,hashlib,math
from collections import defaultdict
from pathlib import Path
import numpy as np

from . import france_gyps_2019_dualsensor_identity as old
from .france_gyps_CERRA_day_height_kernel import (
  pack_profiles,score,calibrate
)

EXPECTED_FRANCE_MD5="b18cc8004d311d19ff24060f655178bf"
FIXED_5KM_BIRDS=28
SHA_5KM="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
SOURCE_CERRA_PREHEIGHT_RUN=39924080855
N_NULL=999
MIN_NULL=950
MIN_BIRDS=10
RNG_SEED=20261023
SENSORS=("GPS","BAROMETRIC")
METRICS=("solar","wind")


def date_label_map_to_sessions(packed,one_date_label):
    return np.asarray([
        0 if one_date_label.get(day)=="low" else
        1 if one_date_label.get(day)=="high" else -1
        for bird,day in packed["bird_days"]
    ],dtype=np.int64)


def shuffle_full_calendar_days(site_labels,rng):
    by_month=defaultdict(list)
    for day in site_labels:
        by_month[day[:7]].append(day)
    result={}
    for month,dates in sorted(by_month.items()):
        days=sorted(dates)
        labels=[site_labels[d] for d in days]
        shuffled=rng.permutation(len(days))
        for i,day in enumerate(days):
            result[day]=labels[int(shuffled[i])]
    return result


def verify_external_weather(r):
    if (r["analysis"]!="FRANCE_GYPS_2019_2021_CERRA_DAY_CONTEXT_XY_NO_HEIGHT_V1"
        or r["source_original_GPS_zip_md5"]!=EXPECTED_FRANCE_MD5
        or r["prior_5km_biological_roster_hash"]!=SHA_5KM
        or r["numeric_GPS_height_read"] is not False
        or r["numeric_baro_height_read"] is not False):
        raise ValueError("Previously frozen new climate metadata is not original outcome-blind source")
    if r["source_support"]["solar"]["n_eligible_birds"]<MIN_BIRDS:
        raise ValueError("Primary solar source failed minimum ten birds; cannot rescue")
    if r["location_WGS84"]!=[44.2,3.25]:
        raise ValueError("CERRA independent site coordinate changed")
    return True


def protect_older_source(preheight,cross):
    ids=old.load_primary_gates(preheight,cross)
    if len(ids)!=FIXED_5KM_BIRDS:
        raise ValueError("Previously observed France dual source biological bird roster drift")
    return ids


def run(source,source_meta,source_cross,external_weather,outdir):
    prior=json.loads(source_meta.read_text())
    cross=json.loads(source_cross.read_text())
    weather=json.loads(external_weather.read_text())
    verify_external_weather(weather)
    accepted=protect_older_source(prior,cross)
    old.digest(source)
    first,source_counts=old.original_first_records(source)
    src_gps,src_baro,qc=old.paired_profiles(first,accepted)
    if src_gps is None:
        raise ValueError("Original 80pct both-native source height QC failed; no rescue")
    old.check_two_native_sensor_same_sessions(src_gps,src_baro)
    if (qc["joint_5min_GPS_fixes_for_scoring"]!=417821 or
        qc["fixed_eligible_birds_after_paired_qc"]!=28):
        raise ValueError("Previously reported GPS/barometric same-event source QC drift")

    sessions={}
    for sensor,olddata in (("GPS",src_gps),("BAROMETRIC",src_baro)):
        sessions[sensor]=[
            {"bird":row["animal"],"day":row["day"],"hists":row["hist"]}
            for row in olddata
        ]
    outdir.mkdir(parents=True,exist_ok=True)
    result={}
    nullfiles=[]
    for metric in METRICS:
        by_date=weather["all_climate_labels"][metric]
        originally_eligible=set(weather["source_support"][metric]["bird_ids"])
        panel={}
        packed={}
        for sensor in SENSORS:
            data=sessions[sensor]
            labels={(row["bird"],row["day"]):(
                  0 if by_date.get(row["day"])=="low" else
                  1 if by_date.get(row["day"])=="high" else -1)
                  for row in data}
            packed[sensor]=pack_profiles(data,labels)
            observed=score(packed[sensor])
            entry={
              "metric":metric,"sensor":sensor,
              "terminal":"unavailable",
              "reason":None,
              "observed":observed,
              "minimum_n_birds":MIN_BIRDS,
              "independent_CERRA_label_calendar_days":len(by_date),
              "source_preheight_climate_eligible_birds":len(originally_eligible),
            }
            # New native quality and 50-target-day threshold may cause fewer
            # eligible biological birds than original no-height screen.
            if observed["eligible_birds"]<MIN_BIRDS:
                entry["reason"]="native_paired_height_and_day_context_below_ten_birds"
            panel[sensor]=entry

        rng=np.random.default_rng(RNG_SEED+(0 if metric=="solar" else 100))
        draws={sensor:[] for sensor in SENSORS}
        if any(panel[s]["observed"]["eligible_birds"]>=MIN_BIRDS for s in SENSORS):
            for i in range(N_NULL):
                shuffled=shuffle_full_calendar_days(by_date,rng)
                for sensor in SENSORS:
                    entry=panel[sensor]
                    if entry["observed"]["eligible_birds"]<MIN_BIRDS:
                        continue
                    z=score(packed[sensor],date_label_map_to_sessions(packed[sensor],shuffled))
                    valid=z["eligible_birds"]>=MIN_BIRDS and z["mean_gain"] is not None
                    draws[sensor].append({
                      "draw":i+1,"mean_gain":z["mean_gain"] if valid else None,
                      "eligible_birds":z["eligible_birds"],
                      "eligible_bird_days":z["eligible_bird_days"],
                      "scored_fixes":z["scored_fixes"]
                    })
                if (i+1)%200==0:print("French 5km CERRA",metric,"day-block null",i+1,flush=True)
        for sensor in SENSORS:
            entry=panel[sensor]
            if entry["observed"]["eligible_birds"]<MIN_BIRDS:
                continue
            dist=draws[sensor]
            if len(dist)!=N_NULL:raise AssertionError("999 required climate date permutations missing")
            entry["calibration"]=calibrate(entry["observed"],dist)
            if entry["calibration"]["valid"]<MIN_NULL:
                entry["reason"]="fewer_than_950_valid_whole_calendar_day_nulls"
            else:
                entry["terminal"]="exploratory_tested_before_Holm"
            csvname=f"{metric}_{sensor}_CERRA_dateblock_null.csv"
            with (outdir/csvname).open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=list(dist[0]))
                w.writeheader();w.writerows(dist)
            nullfiles.append(csvname)
        result[metric]=panel

    family={(metric,sensor):result[metric][sensor]
            for metric in METRICS for sensor in SENSORS}
    def pinput(key):
        r=family[key]
        return r.get("calibration",{}).get("p_upper",1.0) \
           if r["terminal"]=="exploratory_tested_before_Holm" else 1.0
    ordered=sorted(family,key=lambda k:(pinput(k),k))
    adjusted=0.
    for index,key in enumerate(ordered):
        entry=family[key]
        p=pinput(key)
        entry["family_p_placeholder"]=p
        adjusted=max(adjusted,min(1.,p*(len(ordered)-index)))
        entry["Holm_exploratory_p_upper"]=adjusted
        if entry["terminal"]=="exploratory_tested_before_Holm":
            cal=entry["calibration"]
            supported=(cal["observed_minus_null_mean"] is not None and
                       cal["observed_minus_null_mean"]>0 and adjusted<.05)
            entry["terminal"]="supported_exploratory_environmental_shape" if supported \
              else "not_supported_exploratory_environmental_shape"
    payload={
        "analysis":"FRENCH_GYPS_2019_2021_CERRA_SOLAR_WIND_5KM_DUAL_HEIGHT_POSTHOC_V1",
        "source_DOI":"10.48579/PRO/IOSZNM",
        "source_zip_md5":EXPECTED_FRANCE_MD5,
        "prior_original_GPS_and_BARO_individuality_run":39716885648,
        "prior_independent_CERRA_source_run":SOURCE_CERRA_PREHEIGHT_RUN,
        "source_France_5km_bird_SHA":SHA_5KM,
        "model_grain_m":5000,
        "original_same_GPS_target_fixes_both_sensors":True,
        "family_size":4,
        "weather_day_shuffle":"Whole calendar day synchronised across ALL source birds within original year-month; 999 draws",
        "previous_height_results_opened_before_new_weather_hypothesis":True,
        "scope":"POST_OUTCOME EXPLORATORY, cannot identify causal thermal/wind flight effects or individual-specific reaction",
        "paired_sensor_quality":{k:v for k,v in qc.items() if k!="per_day_sensor_agreement_descriptive"},
        "panels":result,
        "output_null_files":nullfiles,
    }
    (outdir/"FRANCE_GYPS_CERRA_SOLAR_WIND_5KM_DUAL_HEIGHT_POSTHOC_RESULT_V1.json").write_text(
        json.dumps(payload,indent=2,sort_keys=True)+"\n"
    )
    print(json.dumps({
        "scientific_scope":"POST_OUTCOME EXPLORATORY",
        "study_birds_preheight":len(accepted),
        "n_original_paired_fixes":qc["joint_5min_GPS_fixes_for_scoring"],
        "panels":{
           metric+"_"+sensor:{
              "birds":result[metric][sensor]["observed"]["eligible_birds"],
              "days":result[metric][sensor]["observed"]["eligible_bird_days"],
              "raw_gain":result[metric][sensor]["observed"]["mean_gain"],
              "null_valid":result[metric][sensor].get("calibration",{}).get("valid"),
              "null_excess":result[metric][sensor].get("calibration",{}).get("observed_minus_null_mean"),
              "Holm_p":result[metric][sensor].get("Holm_exploratory_p_upper"),
              "status":result[metric][sensor]["terminal"]
           } for metric in METRICS for sensor in SENSORS}
        },sort_keys=True),flush=True)
    return payload


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--preheight-original",type=Path,required=True)
    p.add_argument("--old-crosswalk",type=Path,required=True)
    p.add_argument("--CERRA-source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.source,args.preheight_original,args.old_crosswalk,args.CERRA_source,args.out)


if __name__=="__main__":
    main()
