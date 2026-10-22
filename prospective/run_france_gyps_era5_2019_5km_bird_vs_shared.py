#!/usr/bin/env python3
"""French wild Gyps 2019-21: own versus population-SHARED ERA5 wind response.

New ecological contrast was frozen after the original 5km individual
height-shape results were opened: ALWAYS LABEL THIS POST-OUTCOME EXPLORATORY.
Target group exactly the 25 birds admitted by INDEPENDENT altitude-blind
ERA5/5km source support. All 27 identity-unambiguous birds can be donors.

Same target 5-minute events, same native GPS+baro paired source support, 5km
EPSG6933, monthly regional wind Q25/Q75. The permutation operates over WHOLE
regional UTC CALENDAR DAYS, synchronously across ALL birds, not per-bird labels.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np

from . import france_gyps_era5_2019_5km_preheight_gate as source
from . import france_gyps_2019_dualsensor_identity as old_height
from . import france_wind_context_height_kernel as height_kernel
from . import france_species_shared_regional_wind_kernel as common_kernel

SOURCE_SHA=source.gps.SOURCE_MD5
CANDIDATE25_SHA="0528f4c8cff551ccc43a65d97f661b0f01a2529b9f355012770057e227e5d6f0"
WIND_CALENDAR_SHA="fd1cc44366f25429184eb7560097b90c8f44024b91d3beb3e4244dd79123cf74"
SOURCE_5KM_SHA="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
TAG_ALIAS="182208"
GPS_MIN=-500.0
GPS_MAX=7000.0
MIN_JOINT_SOURCE=.8
MIN_JOINT_DAY=.5
MIN_DAY_EVENTS=20
MIN_BIRDS=10
MIN_PERM_VALID=950
N_PERM=999
SEED=20261022


def validate_noheight_receipt(d):
    if d.get("analysis")!="FRANCE_GYPS_2019_2021_ERA5_WIND_5KM_SOURCE_ADMISSION_V1":
        raise ValueError("New ERA5 source identity changed")
    if d.get("source_zip_md5")!=SOURCE_SHA:
        raise ValueError("Original archive identity changed")
    if d.get("no_altitude_values_accessed_this_analysis") is not True:
        raise ValueError("The wind source gate was not altitude-blind")
    m=d["source_preheight_reinspection"]
    if (m["prior_GPS_first5min_fix_count"]!=source.SOURCE_5MIN
        or m["prior_preheight_5km_bird_sha"]!=SOURCE_5KM_SHA
        or m["distinct_biological_bird_ids_after_quarantine"]!=27
        or m["source_first5min_after_tag_quarantine"]!=726993
        or m["excluded_bird_count"]!=2):
        raise ValueError("Original dummy/tag collision source Q/A drift")
    aliases=m["tag_collision_by_native_id"]
    if set(aliases)!={TAG_ALIAS} or len(aliases[TAG_ALIAS])!=2:
        raise ValueError("Previously frozen ambiguous tag ID has changed")
    w=d["independent_ERA5_regional_wind"]
    if w["n_calendar_days"]!=1096 or w["per_calendar_day_state_sha256"]!=WIND_CALENDAR_SHA:
        raise ValueError("Monthly source ERA5 weather drift")
    p=d["population"]
    group=p["5km_shared_species_wind_reference_support"]
    if (group["birds"]!=25 or group["bird_days"]!=1844
        or group["selected_GPS_fixes"]!=59616
        or group["bird_IDs_sha256"]!=CANDIDATE25_SHA
        or group["admitted"] is not True):
        raise ValueError("Previously altitude-blind 25-bird shared reference gate drift")
    return set(group["bird_IDs"]),set(aliases[TAG_ALIAS])


def calendar_states(d):
    wind,weather=source.get_era5()
    if (weather["n_calendar_days"]!=1096
        or weather["per_calendar_day_state_sha256"]!=WIND_CALENDAR_SHA):
        raise ValueError("Original independently-sampled UTC CERRA/ERA5 wind exposure changed")
    for year,v in weather["year_coverage"].items():
        if v["complete_days"] not in (365,366):
            raise ValueError("Missing ERA5 wind calendar year days: "+year)
    return wind,weather


def permute_calendar_days(wind,rng):
    """Calendar date shared by all birds; full year-month wind counts fixed."""
    by_month=defaultdict(list)
    for day in wind:
        by_month[day[:7]].append(day)
    changed=dict(wind)
    for month,keys in sorted(by_month.items()):
        keys.sort()
        if len(keys)>1:
            scrambled=rng.permutation(np.asarray([wind[d] for d in keys],
                              dtype=np.int64))
            for day,state in zip(keys,scrambled):
                changed[day]=int(state)
    return changed


def original_native_source_selected(zippath,source_clean,aliases):
    # Uses the original previously executed native GPS + BARO decoder.
    # Selection was made by source/UTC/XY BEFORE any height QA (and rechecked).
    old_height.digest(zippath)
    original,_=old_height.original_first_records(zippath)
    cleaned={key:row for key,row in original.items()
             if key[0] not in aliases and key[0]!= "Test géodésie ornitela"}
    if len(cleaned)!=726993 or len(source_clean)!=len(cleaned):
        raise ValueError("Source/tag-clean GPS first-event population drift")
    for key,(_,lon,lat,hdop,sat,tag) in source_clean.items():
        v=cleaned.get(key)
        if v is None:
            raise ValueError("Source-selected individual/day/5min key changed")
        if v[0]!=source_clean[key][0] or v[1]!=lon or v[2]!=lat:
            raise ValueError("Source-selected first GPS timestamp/x/y changed")
    return cleaned


def paired_profiles(all_first,candidate25):
    """Never replace a missing GPS height by a later source fix.

    All 27 native identity-unambiguous birds (not only target 25) contribute
    to species-shared references, but only 25 eligible IDs can be targets.
    """
    by_day=defaultdict(list)
    nraw=Counter()
    q=Counter()
    for (bird,day,k),(_,lon,lat,g_raw,b_raw,hdop,sat) in all_first.items():
        nraw[bird,day]+=1
        g=old_height.asfloat(g_raw)
        b=old_height.asfloat(b_raw)
        if g is None: q["missing_nonfinite_GPS"]+=1
        if b is None: q["missing_nonfinite_BARO"]+=1
        if g is not None and not GPS_MIN<=g<=GPS_MAX:
            q["GPS_outside_frozen_native_height_range"]+=1
        if b is not None and not GPS_MIN<=b<=GPS_MAX:
            q["BARO_outside_frozen_native_height_range"]+=1
        if g is None or b is None or not (
            GPS_MIN<=g<=GPS_MAX and GPS_MIN<=b<=GPS_MAX):
            q["paired_invalid"]+=1
            continue
        q["paired_good"]+=1
        x,y=source.gps.PROJECTOR.transform(lon,lat)
        if not(math.isfinite(x) and math.isfinite(y)):
            raise ValueError("Frozen XY projection failed on native paired altitude")
        cell=(math.floor(x/5000),math.floor(y/5000))
        by_day[bird,day].append((cell,g,b))
    paired_fraction=q["paired_good"]/len(all_first)
    quality={
       "selected_5min_original_tag_clean":len(all_first),
       "paired_native_GPS_and_BARO_valid":q["paired_good"],
       "paired_native_source_quality_fraction":paired_fraction,
       "height_QC_counts":dict(q),
       "target_birds_from_altitude_blind_gate":len(candidate25),
       "native_vertical_units":"GPS height-above-msl and bar:barometric-height in source; each bird-day median centered",
       "native_barometric_pressure_height_sensor_independence_verified":False
    }
    if paired_fraction<MIN_JOINT_SOURCE:
        quality["reason"]="source_paired_GPS_and_BARO_height_fraction_below_80pct"
        return None,None,quality
    GPS=[];BARO=[]
    nonempty_day_count=0
    source_days_skipped_low_frac=0
    source_days_skipped_under_20=0
    for (bird,day),rows in sorted(by_day.items()):
        if len(rows)/nraw[bird,day] <MIN_JOINT_DAY:
            source_days_skipped_low_frac+=1
            continue
        if len(rows)<MIN_DAY_EVENTS:
            source_days_skipped_under_20+=1
            continue
        g=np.asarray([r[1] for r in rows],dtype=np.float64)
        b=np.asarray([r[2] for r in rows],dtype=np.float64)
        gi=height_kernel.center_bins(g)
        bi=height_kernel.center_bins(b)
        gh=defaultdict(lambda:np.zeros(10,dtype=np.int64))
        bh=defaultdict(lambda:np.zeros(10,dtype=np.int64))
        for (cell,_,_),g_bin,b_bin in zip(rows,gi,bi):
            gh[cell][int(g_bin)]+=1
            bh[cell][int(b_bin)]+=1
        GPS.append({"bird":bird,"day":day,"hists":dict(gh)})
        BARO.append({"bird":bird,"day":day,"hists":dict(bh)})
        nonempty_day_count+=1
    if len(GPS)!=len(BARO):
        raise AssertionError("Sensor source cohort profiles differ")
    for a,b in zip(GPS,BARO):
        if (a["bird"],a["day"],set(a["hists"]))!=(
            b["bird"],b["day"],set(b["hists"])):
            raise AssertionError("GPS and baro sessions differ on same source events")
        if any(int(a["hists"][c].sum())!=int(b["hists"][c].sum()) for c in a["hists"]):
            raise AssertionError("GPS and BARO models would evaluate different GPS event sets")
    quality["paired_bird_days_ge20"]=nonempty_day_count
    quality["paired_bird_days_fraction_below_half"]=source_days_skipped_low_frac
    quality["paired_bird_days_under_20"]=source_days_skipped_under_20
    quality["available_target_bird_days"]=sum(r["bird"] in candidate25 for r in GPS)
    return GPS,BARO,quality


def fixed_target_score(s,targets):
    subset={bird:r for bird,r in s["per_bird"].items() if bird in targets}
    if not subset:
        return {"mean_gain":None,"eligible_birds":0,"eligible_bird_days":0,
                "scored_fixes":0,"per_bird":{}}
    return {
       "mean_gain":float(np.mean([v["gain"] for v in subset.values()])),
       "eligible_birds":len(subset),
       "eligible_bird_days":sum(v["low_days"]+v["high_days"] for v in subset.values()),
       "scored_fixes":sum(v["scored_fixes"] for v in subset.values()),
       "per_bird":subset
    }


def rerandomization(packed,shared_context,source_calendar,targets,seed=SEED,n=N_PERM):
    from .france_species_shared_regional_wind_kernel import score_shared_vs_bird
    rng=np.random.default_rng(seed)
    draws=[]
    for k in range(n):
        perm=permute_calendar_days(source_calendar,rng)
        labels=np.asarray([perm.get(day,-1) for bird,day in packed["bird_days"]],
                          dtype=np.int64)
        data=fixed_target_score(score_shared_vs_bird(packed,shared_context,labels),
                                targets)
        valid=data["eligible_birds"]>=MIN_BIRDS and data["mean_gain"] is not None
        draws.append({
           "draw":k+1,
           "mean_gain":data["mean_gain"] if valid else None,
           "eligible_birds":data["eligible_birds"],
           "eligible_bird_days":data["eligible_bird_days"],
           "scored_fixes":data["scored_fixes"]
        })
        if (k+1)%100==0:
            print("ERA5 shared-calendar-date null",k+1,"of",n,flush=True)
    return draws


def calibrate(observed,draws):
    good=np.asarray([r["mean_gain"] for r in draws
             if r["mean_gain"] is not None and math.isfinite(r["mean_gain"])],
             dtype=np.float64)
    bad=len(draws)-len(good)
    d={
      "requested":len(draws),"valid":len(good),"unavailable":bad,
      "null_eligible_birds_range":[min(r["eligible_birds"] for r in draws),
                                  max(r["eligible_birds"] for r in draws)],
      "p_upper":1.0
    }
    if not len(good) or observed["mean_gain"] is None:return d
    count=int((good>=observed["mean_gain"]-1e-14).sum())
    return {**d,
       "null_mean":float(good.mean()),
       "null_quantiles_025_50_975":[float(v) for v in np.quantile(good,[.025,.5,.975])],
       "observed_minus_null_mean":float(observed["mean_gain"]-good.mean()),
       "null_ge_observed":count,
       "p_lower":(1+count)/(len(draws)+1),
       "p_upper":(1+count+bad)/(len(draws)+1)
    }


def sensors_holm(panel):
    raw={name:(row.get("calibration",{}).get("p_upper",1.0)
                if row["terminal"]=="exploratory_evaluated" else 1.0)
         for name,row in panel.items()}
    adjusted=0.
    for k,name in enumerate(sorted(raw,key=lambda z:(raw[z],z))):
        adjusted=max(adjusted,min(1.,raw[name]*(len(raw)-k)))
        panel[name]["holm_p_upper"]=adjusted
        panel[name]["holm_family_p"]=raw[name]
        if panel[name]["terminal"]=="exploratory_evaluated":
            cal=panel[name]["calibration"]
            if cal["observed_minus_null_mean"]>0 and adjusted<.05:
                panel[name]["terminal"]="exploratory_bird_specific_wind_context_extra_predictability"
            else:
                panel[name]["terminal"]="exploratory_bird_specific_wind_context_not_supported"
    return panel


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--ERA5-preheight-receipt",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)

    original=json.loads(args.ERA5_preheight_receipt.read_text())
    target_birds,alias_birds=validate_noheight_receipt(original)
    assert len(target_birds)==25

    # Confirm one immutable source population and the same ERA5 day states
    # BEFORE reading native height values from this previously opened source.
    noheight, nonheight_source=source.source_meta(args.source_zip)
    if len(noheight)!=726993:
        raise ValueError("Previously quarantine-tag-clean source cohort drift")
    actual_calendar,weather_manifest=calendar_states(original)
    rebuilt=source.score_structural(noheight,actual_calendar)
    original_block=original["population"]["5km_shared_species_wind_reference_support"]
    if rebuilt["5km_shared_species_wind_reference_support"]!=original_block:
        raise ValueError("Source and observed ERA5 25bird target population preheight support drift")
    if not target_birds.issubset({b for b,d,k in noheight}):
        raise ValueError("One or more frozen target birds missing from source nonheight GPS")
    print("ORIGINAL 25BIRD SOURCE ROSTER/FIXES/ERA5 COMPLETE AND FROZEN",flush=True)

    selected=original_native_source_selected(args.source_zip,noheight,alias_birds)
    paired_GPS,paired_BARO,quality=paired_profiles(selected,target_birds)
    result={
      "analysis":"FRANCE_GYPS_2019_2021_ERA5_5KM_BIRD_VS_SHARED_WIND_V1",
      "mode":"post_prior_height_exploratory_wind_context_comparison",
      "source":"https://doi.org/10.48579/PRO/IOSZNM",
      "source_zip_md5":SOURCE_SHA,
      "original_old_identity_outcome_run":39716885648,
      "original_nonheight_quality_run":39720327589,
      "ERA5_nonheight_source_run":39723205971,
      "weather_calendar_sha256":WIND_CALENDAR_SHA,
      "frozen25_preheight_ID_SHA256":CANDIDATE25_SHA,
      "source_clean_altitude_independent_wind_roster":True,
      "source_physically_distinct_GPS_and_BARO_sensors_proven":False,
      "source_ERA5_wind_local_5km":False,
      "evidence_not_independent_of_historical_France_identity":True,
      "permutation":"Synchronous all-bird calendar-date Wstar-low/high labels exchanged within year-month",
      "quality":quality,
      "sensor_results":{},
      "terminal":"unavailable",
    }
    if paired_GPS is None:
        result["reason"]=quality.get("reason","native_paired_height_invalid")
    else:
        labels={(bird,day):actual_calendar.get(day,-1)
                for bird,day in [(r["bird"],r["day"]) for r in paired_GPS]}
        packs={
         "GPS":height_kernel.pack_profiles(paired_GPS,labels),
         "BAROMETRIC":height_kernel.pack_profiles(paired_BARO,labels)
        }
        ref_names=list(packs)
        ref=packs["GPS"]
        other=packs["BAROMETRIC"]
        if (ref["birds"]!=other["birds"]
            or ref["bird_days"]!=other["bird_days"]
            or not np.array_equal(ref["index"],other["index"])
            or not np.array_equal(ref["labels"],other["labels"])
            or not np.array_equal(ref["other_support"],other["other_support"])):
            raise ValueError("Original 5km GPS and barometric target record indices differ")
        context=common_kernel.build_shared_context(ref)
        null_calendar_seed=[permute_calendar_days(actual_calendar,np.random.default_rng(SEED+i))
                            for i in range(0)]  # Source permutation is later generated once per draw.
        source_result={}
        null_draws={k:[] for k in packs}
        for sensor,pack in packs.items():
            observed=fixed_target_score(
               common_kernel.score_shared_vs_bird(pack,context),target_birds)
            row={"observed":observed,"terminal":"unavailable","reason":None}
            source_result[sensor]=row
            if observed["eligible_birds"]<MIN_BIRDS:
                row["reason"]="less_than_10_target_birds_after_native_joint_height_and_common_wind_support"
        # Use SAME calendar dates/order/seed for paired GPS/baro to preserve
        # matched paired-sensor biological and meteorological support.
        active={sensor:p for sensor,p in packs.items()
                if source_result[sensor]["reason"] is None}
        if active:
            rng=np.random.default_rng(SEED)
            for k in range(N_PERM):
                perm=permute_calendar_days(actual_calendar,rng)
                perm_labels=np.asarray(
                    [perm.get(day,-1) for bird,day in ref["bird_days"]],
                    dtype=np.int64)
                for sensor,pack in active.items():
                    all_scores=common_kernel.score_shared_vs_bird(pack,context,perm_labels)
                    score=fixed_target_score(all_scores,target_birds)
                    valid=score["eligible_birds"]>=MIN_BIRDS and score["mean_gain"] is not None
                    null_draws[sensor].append({
                        "draw":k+1,
                        "mean_gain":score["mean_gain"] if valid else None,
                        "eligible_birds":score["eligible_birds"],
                        "eligible_bird_days":score["eligible_bird_days"],
                        "scored_fixes":score["scored_fixes"]
                    })
                if (k+1)%100==0:
                    print("FRENCH_GYPS_REGIONAL_WIND_CALENDAR_RANDOMIZATION",k+1,flush=True)
            for sensor,ds in null_draws.items():
                if not ds:continue
                cal=calibrate(source_result[sensor]["observed"],ds)
                source_result[sensor]["calibration"]=cal
                if cal["valid"]<MIN_PERM_VALID:
                    source_result[sensor]["reason"]="frozen_valid_ERA5_calendar_null_below_950"
                else:
                    source_result[sensor]["terminal"]="exploratory_evaluated"
                with (args.out/(sensor+"_ERA5_5km_own_vs_shared_wind_999_calendar_null.csv")).open("w",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=list(ds[0]))
                    w.writeheader();w.writerows(ds)
        result["sensor_results"]=sensors_holm(source_result)
        if all(result["sensor_results"][s]["terminal"]!="unavailable"
            for s in packs):
            result["terminal"]="exploratory_paired_native_sensor_regional_wind_response_comparison_completed"
        else:
            result["terminal"]="unavailable"
    output=args.out/"FRANCE_GYPS_2019_2021_ERA5_5KM_BIRD_VS_SHARED_WIND_RESULT_V1.json"
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
       "terminal":result["terminal"],
       "joint_native_height_valid_fraction":quality["paired_native_source_quality_fraction"],
       "sensor_results":{k:{
         "terminal":v["terminal"],
         "reason":v.get("reason"),
         "n_birds":v.get("observed",{}).get("eligible_birds"),
         "n_days":v.get("observed",{}).get("eligible_bird_days"),
         "raw_gain":v.get("observed",{}).get("mean_gain"),
         "null_valid":v.get("calibration",{}).get("valid"),
         "null_excess":v.get("calibration",{}).get("observed_minus_null_mean"),
         "holm_p_upper":v.get("holm_p_upper")
       } for k,v in result["sensor_results"].items()}
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
