#!/usr/bin/env python3
"""Outcome-opening adapter for frozen CERRA 2016 gull wind-context experiment.

Original archive, colony ID, weather quartiles and pre-height population must
match the already committed outcome-blind receipt before GPS altitude is read.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pyproj import Transformer

from .screen_zeebrugge_cerra_2016 import (
    SRC_NAME, SRC_MD5, REF_NAME, REF_MD5, ensure_md5,
    fetch_weather, reference_meta, safe_crosswalk, screen_fixes, xysupport, num,
)
from .zeebrugge_cerra_2016_wind_shape import (
    EDGES, pack, permute_wind_labels, score_packed
)

EXPECTED_SUPPORT="110e3db80e869f758b0660ca7ae6d059362074879bfd418b86bbea469f191379"
SEED=20261020
N_PERM=999
PRIMARY_BIRDS=10


def check_preoutcome(ref, first, id_labels, archived_receipt):
    if archived_receipt["height_or_biological_effect_opened"] is not False:
        raise ValueError("Not an uninspected pre-height source receipt")
    if archived_receipt["source_reference_md5"]!=REF_MD5 or archived_receipt["source_gps_md5"]!=SRC_MD5:
        raise ValueError("Pre-height archive identity mismatch")
    meta=reference_meta(ref)
    cross=safe_crosswalk(ref,id_labels)
    if not cross["accepted"] or cross["observed_distinct_birds"]!=69:
        raise ValueError("Exact bird-colony mapping changed")
    if meta["site_centers"]!=archived_receipt["reference"]["site_centers"]:
        raise ValueError("Colonies' reference locations changed")
    meteo,regimes=fetch_weather(meta["site_centers"])
    original=archived_receipt["regional_cerra"]
    if set(meteo)!=set(original):
        raise ValueError("Climate grid/site roster drift")
    for site,old in original.items():
        new=meteo[site]
        for key in ("response_grid_latitude","response_grid_longitude"):
            if abs(new[key]-old[key])>1e-5:
                raise ValueError("Frozen CERRA grid location drift")
        if old["days_valid_20plus_hours"]!=new["days_valid_20plus_hours"]:
            raise ValueError("Climate day coverage drift")
        for month,oldq in old["thresholds_by_month"].items():
            newq=new["thresholds_by_month"].get(month)
            if newq is None:
                raise ValueError("Frozen CERRA month lost")
            for key in ("q25","q75","n_calendar_days"):
                if abs(oldq[key]-newq[key])>1e-8:
                    raise ValueError("Frozen site-month wind quantile drift")
    support=xysupport(first,cross["site_by_bird"],regimes)
    if support["matched_wind_eligible_birds_sha256"]!=EXPECTED_SUPPORT:
        raise ValueError("Frozen source-ID/wind preheight roster drift")
    if support["wind_both_regimes_birds"]!=41:
        raise ValueError("Expected 41 initial altitude-blind wind candidates")
    return cross["site_by_bird"],meteo,regimes,support


def extract_height_from_frozen_events(source_file:Path,first:dict):
    """Earliest fix is chosen independently of altitude, never replaced."""
    selected={}
    with gzip.open(source_file,"rt",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        if "height-above-msl" not in set(reader.fieldnames or []):
            raise ValueError("Native numeric altitude field is absent")
        for row in reader:
            stamp=(row.get("timestamp") or "").strip()
            bird=(row.get("individual-local-identifier") or "").strip()
            if len(stamp)<16:continue
            try:
                hour=int(stamp[11:13])
                minute=int(stamp[14:16])
            except ValueError:
                continue
            key=(bird,stamp[:10],hour*12+minute//5)
            chosen=first.get(key)
            if chosen is None or chosen[0]!=stamp or key in selected:
                continue
            selected[key]=row.get("height-above-msl","")
    if len(selected)!=len(first):
        raise AssertionError("Cannot match altitude to all pre-height 5-minute events")
    converter=Transformer.from_crs("EPSG:4326","EPSG:32631",always_xy=True)
    events=defaultdict(list)
    missing=outside=valid=0
    for (bird,day,bin5),(stamp,lon,lat) in first.items():
        z=num(selected[bird,day,bin5])
        if z is None:
            missing+=1
            continue
        if z< -300 or z>3000:
            outside+=1
            continue
        east,north=converter.transform(lon,lat)
        if not(math.isfinite(east) and math.isfinite(north)):
            raise AssertionError("Originally valid x-y became invalid on projection")
        cell=(math.floor(east/5000),math.floor(north/5000))
        events[bird,day].append((cell,z))
        valid+=1
    rows=[]
    for (bird,day),day_events in sorted(events.items()):
        alt=np.asarray([z for cell,z in day_events],dtype=float)
        centered=alt-np.median(alt)
        b=np.searchsorted(EDGES,centered,side="right")-1
        profile=defaultdict(lambda:np.zeros(10,np.int64))
        for (cell,z),k in zip(day_events,b):
            profile[cell][k]+=1
        rows.append({"bird":bird,"day":day,"hists":dict(profile)})
    return rows,{
        "flight_5min_bins_before_height":len(first),
        "valid_height_fixes":valid,
        "height_missing_or_nonfinite":missing,
        "height_outside_fixed_range":outside,
        "valid_fraction":valid/len(first) if first else None,
        "valid_bird_day_sessions":len(rows),
    }


def calibrate(score,draws):
    vals=np.asarray([x["gain"] for x in draws if x["gain"] is not None],float)
    nbad=len(draws)-len(vals)
    count=int(np.sum(vals>=score-1e-12))
    return dict(requested=len(draws),valid=len(vals),unavailable=nbad,
        tail_ge_observed=count,p_lower=(1+count)/(len(draws)+1),
        p_upper=(1+count+nbad)/(len(draws)+1),
        null_mean=float(vals.mean()) if len(vals) else None,
        null_quantiles=np.quantile(vals,[.025,.5,.975]).tolist() if len(vals) else [],
        observed_minus_null_mean=float(score-vals.mean()) if len(vals) else None)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps",required=True,type=Path)
    p.add_argument("--reference",required=True,type=Path)
    p.add_argument("--source-receipt",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    ensure_md5(args.gps,SRC_MD5,SRC_NAME)
    ensure_md5(args.reference,REF_MD5,REF_NAME)
    prior=json.loads(args.source_receipt.read_text(encoding="utf-8"))
    with args.reference.open("rt",encoding="utf-8-sig",newline="") as f:
        ref=list(csv.DictReader(f))
    with gzip.open(args.gps,"rt",encoding="utf-8-sig",newline="") as f:
        first,labels,preflight=screen_fixes(csv.DictReader(f))
    sites,weather,regimes,support=check_preoutcome(ref,first,labels,prior)
    sessions,quality=extract_height_from_frozen_events(args.gps,first)
    report={
        "analysis":"ZEEBRUGGE_2016_CERRA_WIND_VERTICAL_SHAPE_V1",
        "preheight_support_run":39391834277,
        "source":"https://zenodo.org/records/22273603",
        "source_gps_md5":SRC_MD5,
        "source_ref_md5":REF_MD5,
        "preheight_41_bird_support_hash":EXPECTED_SUPPORT,
        "frozen_plan":"prospective/ZEEBRUGGE_2016_CERRA_WIND_SHAPE_TEST_FREEZE_V1.json",
        "quality":quality,
        "terminal":"unavailable",
        "scope":"observational colony-level CERRA wind; session-centered GPS altitude shape, not causal wind effect",
    }
    args.output.mkdir(parents=True,exist_ok=True)
    if quality["valid_fraction"] is None or quality["valid_fraction"]<.8:
        report["reason"]="frozen_altitude_quality_gate"
    else:
        packed=pack(sessions,sites,regimes)
        obs=score_packed(packed,regimes)
        report["observed"]=obs
        if obs["eligible_birds"]<PRIMARY_BIRDS:
            report["reason"]="fixed_wind_heldout_eligibility_below_10"
        else:
            rng=np.random.default_rng(SEED)
            draws=[]
            for i in range(N_PERM):
                newlabels=permute_wind_labels(regimes,weather,rng)
                stat=score_packed(packed,newlabels)
                valid=stat["eligible_birds"]>=PRIMARY_BIRDS and stat["mean_gain"] is not None
                draws.append(dict(draw=i+1,gain=stat["mean_gain"] if valid else None,
                  eligible_birds=stat["eligible_birds"],eligible_days=stat["eligible_bird_days"],
                  scored_fixes=stat["scored_fixes"]))
                if (i+1)%100==0:
                    print("CERRA wind permutation",i+1,flush=True)
            with (args.output/"wind_context_null_draws.csv").open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=list(draws[0]))
                w.writeheader();w.writerows(draws)
            cal=calibrate(obs["mean_gain"],draws)
            report["calibration"]=cal
            report["null_birds_range"]=[min(x["eligible_birds"] for x in draws),
                                        max(x["eligible_birds"] for x in draws)]
            if cal["valid"]<950:
                report["reason"]="frozen_permutation_support_gate"
            else:
                report["terminal"]=(
                    "supported_wind_context_transfer"
                    if cal["p_upper"]<.05 and cal["observed_minus_null_mean"]>0
                    else "wind_context_transfer_not_supported"
                )
    with (args.output/"ZEEBRUGGE_2016_CERRA_WIND_SHAPE_RESULT_V1.json").open("w") as f:
        json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
    if "observed" in report:
        with (args.output/"per_bird_wind_shape.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["bird","gain","low_days","high_days","scored_fixes"])
            w.writeheader()
            for bird,d in sorted(report["observed"]["per_bird"].items()):
                w.writerow(dict(bird=bird,**d))
    print(json.dumps(dict(terminal=report["terminal"],reason=report.get("reason"),
       valid_fraction=quality["valid_fraction"],
       birds=report.get("observed",{}).get("eligible_birds"),
       days=report.get("observed",{}).get("eligible_bird_days"),
       observed_gain=report.get("observed",{}).get("mean_gain"),
       null_valid=report.get("calibration",{}).get("valid"),
       null_p_upper=report.get("calibration",{}).get("p_upper"),
       excess=report.get("calibration",{}).get("observed_minus_null_mean")),
       sort_keys=True),flush=True)


if __name__=="__main__":
    main()
