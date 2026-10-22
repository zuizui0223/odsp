#!/usr/bin/env python3
"""Gyps fulvus 2019-21 independently archived GPS & barometric height D1 test.

Source exact 28 biological bird IDs and XY/time admission was frozen with ZERO
height values inspected (GitHub Actions 39714803696). The original 2026 Gyps
studies' source/animal IDs are separately checked before this code may open
numeric native GPS and pressure-based heights.

We use exactly the same native GPS event for both sensors, center each source
bird-UTC-day by its own per-sensor median, and compare matched source
individuality using the previously executed MEDGULL D1-balanced kernel.
"""
from __future__ import annotations

import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
from pyproj import Transformer
from . import medgull_sensitivity as d1

SOURCE_NAME="windTurbineAvoidance.zip"
SOURCE_MD5="b18cc8004d311d19ff24060f655178bf"
SOURCE_SIZE=1093170227
NAME_PATTERN="Vulturestracks_"
FRENCH5_SHA="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
FRENCH5_BIRDS=28
TOTAL_SELECTED_SOURCE=742423
MIN_JOINT_FRACTION=.8
MIN_DAY_JOINT_FRACTION=.5
EVALUABLE_TARGET_DAY_MIN=50
HEIGHT_MIN=-500.0
HEIGHT_MAX=7000.0
SEED=20261022
N_DRAW=999
MIN_VALID=950
MIN_BIRDS=10
GPS_COLUMN="height-above-msl"
BARO_COLUMN="bar:barometric-height"
PROJECTOR=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)


def digest(path):
    if path.name!=SOURCE_NAME or path.stat().st_size!=SOURCE_SIZE:
        raise ValueError("Official source ZIP filename or archive bytes changed")
    md5=hashlib.md5()
    with path.open("rb") as fd:
        for p in iter(lambda:fd.read(1024*1024),b""):md5.update(p)
    if md5.hexdigest()!=SOURCE_MD5:
        raise ValueError("Exact preheight original GPS ZIP MD5 changed")


def asfloat(v):
    try:z=float(v)
    except (TypeError,ValueError):return None
    return z if math.isfinite(z) else None


def load_primary_gates(preheight,source_crosswalk):
    if (preheight.get("numeric_native_GPS_height_values_read") is not False or
        preheight["selected_native_GPS_five_minute_events"]!=TOTAL_SELECTED_SOURCE or
        preheight["selected_biological_animals"]!=30):
        raise ValueError("Previous source 30-bird 742423 5min admission drifted")
    block=preheight["horizontal_day_eligibility_by_cell_m"]["5000"]
    birds=set(block["admitted_bird_ids"])
    if len(birds)!=FRENCH5_BIRDS or block["source_bird_ID_sha256"]!=FRENCH5_SHA:
        raise ValueError("Source-native 28-bird original 5km roster changed")
    if (source_crosswalk["native_height_values_read"] is not False or
        source_crosswalk["source_independence_category"]!=
        "DIFFERENT_STUDY_NAMES_AND_ZERO_EXACT_SOURCE_ANIMAL_IDS" or
        source_crosswalk["exact_bird_id_overlap_across_both_2026_Gyps_parents"]!=0):
        raise ValueError("Source crosswalk found actual ID overlap or isn't outcome blind")
    return birds


def original_first_records(path):
    # The SAME base filter used by prospective/france_griffon_2019_xytime_preflight.py
    # is reproduced, and total records/historical bird IDs checked afterward.
    chosen={}
    bysource=Counter()
    with zipfile.ZipFile(path) as archive:
        files=[f for f in archive.infolist()
               if f.filename.rsplit("/",1)[-1].startswith(NAME_PATTERN)
               and f.filename.endswith(".csv")
               and not f.filename.startswith("__MACOSX/")]
        if len(files)!=9:raise ValueError("Expected all nine raw France source seasonal files")
        for file in sorted(files,key=lambda f:f.filename):
            with archive.open(file) as binary,io.TextIOWrapper(binary,encoding="utf-8-sig",errors="replace",newline="") as f:
                reader=csv.DictReader(f)
                cols=set(reader.fieldnames or ())
                required={"timestamp","individual-local-identifier",
                    "individual-taxon-canonical-name","location-long",
                    "location-lat","ground-speed","visible",
                    "import-marked-outlier",GPS_COLUMN,BARO_COLUMN,
                    "gps:hdop","gps:satellite-count","tag-local-identifier"}
                if not required<=cols:
                    raise ValueError("Expected independent instrument/source fields absent")
                for row in reader:
                    bird=(row["individual-local-identifier"] or "").strip()
                    if not bird or row["individual-taxon-canonical-name"].strip()!="Gyps fulvus":
                        continue
                    if (row["visible"] or "").strip().lower()=="false" or (
                        row["import-marked-outlier"] or "").strip().lower() in {"true","yes","y","1"}:
                        continue
                    ts=(row["timestamp"] or "").strip()
                    if len(ts)<16:continue
                    try:
                        year,month,day=int(ts[:4]),int(ts[5:7]),int(ts[8:10])
                        hour,minute=int(ts[11:13]),int(ts[14:16])
                    except (ValueError,TypeError):
                        continue
                    if year not in (2019,2020,2021) or not(0<=hour<24 and 0<=minute<60):
                        continue
                    try:lon,lat,speed=float(row["location-long"]),float(row["location-lat"]),float(row["ground-speed"])
                    except (TypeError,ValueError):continue
                    if not all(math.isfinite(z) for z in (lon,lat,speed)):
                        continue
                    if not (-180<=lon<=180 and -85<=lat<=85 and 5<=speed<=55):
                        continue
                    bysource["native_qualified_before_5min"]+=1
                    key=(bird,ts[:10],hour*12+minute//5)
                    if key not in chosen or ts<chosen[key][0]:
                        chosen[key]=(ts,lon,lat,row.get(GPS_COLUMN),
                                     row.get(BARO_COLUMN),row.get("gps:hdop"),
                                     row.get("gps:satellite-count"))
            print("Original ZIP season checked:",file.filename,
                  "5min unique",len(chosen),flush=True)
    if len(chosen)!=TOTAL_SELECTED_SOURCE:
        raise ValueError(f"Previous altitude-unaware five-minute selection changed: {len(chosen)}")
    if len({b for b,d,bin in chosen})!=30:
        raise ValueError("Previous 30-bird source cohort changed")
    return chosen,bysource


def paired_profiles(chosen,admitted):
    full=len(chosen)
    counts=Counter()
    bird_day_total=Counter()
    pair=defaultdict(list)
    # Source denominator includes ALL original 30 birds, before altitudes.
    for (bird,day,bin5),(ts,lon,lat,hg,hb,hdop,sat) in chosen.items():
        counts["first_GPS_fixes"]+=1
        if bird not in admitted:
            counts["original_non_eligible_bird_fixes"]+=1
        else:
            bird_day_total[bird,day]+=1
        gps=asfloat(hg);baro=asfloat(hb)
        if gps is None:counts["GPS_nonfinite_missing"]+=1
        elif not HEIGHT_MIN<=gps<=HEIGHT_MAX:counts["GPS_outside_fixed_range"]+=1
        if baro is None:counts["barometric_nonfinite_missing"]+=1
        elif not HEIGHT_MIN<=baro<=HEIGHT_MAX:counts["barometric_outside_fixed_range"]+=1
        if gps is None or baro is None or not(
            HEIGHT_MIN<=gps<=HEIGHT_MAX and HEIGHT_MIN<=baro<=HEIGHT_MAX):
            counts["paired_unavailable"]+=1
            continue
        counts["joint_valid_both"]+=1
        if bird not in admitted:continue
        east,north=PROJECTOR.transform(lon,lat)
        if not all(math.isfinite(z) for z in (east,north)):
            raise ValueError("Valid source x-y projection failed")
        cell=(math.floor(east/5000),math.floor(north/5000))
        pair[bird,day].append((cell,gps,baro,asfloat(hdop),asfloat(sat)))
    frac=counts["joint_valid_both"]/full
    report={
       "original_total_source_fixes":full,
       "source_firstfix_pair_complete_fraction":frac,
       "source_firstfix_qc_counts":dict(counts),
       "before_native_height_eligible_birds":len(admitted),
       "original_eligible_bird_days":len(bird_day_total),
       "all_original_eligible_ids_sha256":hashlib.sha256("\n".join(sorted(admitted)).encode()).hexdigest()
    }
    if frac<MIN_JOINT_FRACTION:
        report["reason"]="fixed_studywide_80percent_joint_sensor_quality_not_met"
        return None,None,report

    sessions_GPS=[];sessions_BARO=[]
    same_spatial_support=True
    source_day_paired_fixes=0
    per_day_summary=[]
    for (bird,day),rows in sorted(pair.items()):
        original_count=bird_day_total[bird,day]
        if len(rows)/original_count <MIN_DAY_JOINT_FRACTION:
            counts["source_days_below_50pct_joint_qc"]+=1
            continue
        if len(rows)<EVALUABLE_TARGET_DAY_MIN:
            counts["source_days_below_50_paired_events"]+=1
            continue
        g=np.asarray([z[1] for z in rows],dtype=float)
        b=np.asarray([z[2] for z in rows],dtype=float)
        gpsbins=d1.center_bins(g)
        barbins=d1.center_bins(b)
        gp=defaultdict(lambda:np.zeros(10,np.int64))
        bp=defaultdict(lambda:np.zeros(10,np.int64))
        for row,gi,bi in zip(rows,gpsbins,barbins):
            cell=row[0]
            gp[cell][int(gi)]+=1
            bp[cell][int(bi)]+=1
        sessions_GPS.append({"animal":bird,"day":day,"hist":dict(gp)})
        sessions_BARO.append({"animal":bird,"day":day,"hist":dict(bp)})
        source_day_paired_fixes+=len(rows)
        good=[(x[3],abs(x[1]-x[2])) for x in rows if x[3] is not None]
        mad=float(np.median(np.abs((g-np.median(g))-(b-np.median(b)))))
        pearson=float(np.corrcoef(g-np.median(g),b-np.median(b))[0,1]) if (
           len(rows)>2 and np.std(g)>0 and np.std(b)>0) else None
        per_day_summary.append({
          "bird":bird,"day":day,"paired_native_fixes":len(rows),
          "GPS_and_baro_centered_median_abs_difference_m":mad,
          "GPS_and_baro_same_fix_pearson":pearson,
          "median_hdop_when_both":float(np.median([x[3] for x in rows if x[3] is not None]))
             if any(x[3] is not None for x in rows) else None
        })
    report["fixed_eligible_bird_days_after_paired_qc_and_50fix"]=len(sessions_GPS)
    report["fixed_eligible_birds_after_paired_qc"]=len({s["animal"] for s in sessions_GPS})
    report["joint_5min_GPS_fixes_for_scoring"]=source_day_paired_fixes
    report["GPS_baro_same_target_event_support"]=True
    report["source_firstfix_qc_counts"]=dict(counts)
    report["per_day_sensor_agreement_descriptive"]=per_day_summary
    return sessions_GPS,sessions_BARO,report


def check_two_native_sensor_same_sessions(a,b):
    if len(a)!=len(b):raise ValueError("GPS/barometric source sessions differ")
    for x,y in zip(a,b):
        if x["animal"]!=y["animal"] or x["day"]!=y["day"] or set(x["hist"])!=set(y["hist"]):
            raise ValueError("GPS/baro bird-date-cell sessions misaligned")
        for cell in x["hist"]:
            if np.sum(x["hist"][cell])!=np.sum(y["hist"][cell]):
                raise ValueError("GPS/baro height source underlying native GPS fix set differs")


def score_sensor(sessions,sensor,randomizations=N_DRAW):
    x=d1.pack(sessions)
    observed=d1.evaluate(x,1,"balanced")
    out={
      "sensor":sensor,
      "observed":{k:v for k,v in observed.items() if k!="day_scored_bins"},
      "terminal":"unavailable",
      "reason":None
    }
    if observed["eligible_birds"]<MIN_BIRDS:
        out["reason"]="native_joint_paired_height_support_below_10_birds"
        return out,[]
    rng=np.random.default_rng(SEED)
    draws=[]
    for i in range(randomizations):
        shuffled=d1.permute_labels(x,rng)
        z=d1.evaluate(x,1,"balanced",labels=shuffled)
        valid=z["eligible_birds"]>=MIN_BIRDS and z["mean_gain"] is not None
        draws.append({
           "draw":i+1,"gain":z["mean_gain"] if valid else None,
           "eligible_birds":z["eligible_birds"],"eligible_days":z["eligible_days"],
           "eligible_bins":z["eligible_bins"]
        })
        if (i+1)%200==0:
            print("French Gyps",sensor,"original day-block null",i+1,flush=True)
    cal=d1.calibrate(observed["mean_gain"],[v["gain"] for v in draws],randomizations)
    out["calibration"]=cal
    if cal["valid"]<MIN_VALID:
        out["reason"]="frozen_min950_valid_day_relabelling_null_failed"
    else:
        out["terminal"]="tested_before_two_sensor_Holm"
    return out,draws


def two_sensor_family(panels):
    tests=sorted(panels)
    raw={}
    for sensor in tests:
        p=panels[sensor]
        raw[sensor]=p.get("calibration",{}).get("p_upper",1.) if p["terminal"]=="tested_before_two_sensor_Holm" else 1.
    ordered=sorted(tests,key=lambda n:(raw[n],n))
    adjusted=0
    for i,s in enumerate(ordered):
        adjusted=max(adjusted,min(1.,(len(ordered)-i)*raw[s]))
        item=panels[s]
        item["holm_p_upper"]=adjusted
        item["family_p_value"]=raw[s]
        if item["terminal"]=="tested_before_two_sensor_Holm":
            ok=item["calibration"]["observed_minus_valid_null_mean"]>0 and adjusted<.05
            item["terminal"]="supported_own_bird_altitude_shape" if ok else "not_supported_own_bird_altitude_shape"
    return panels


def run(zip_path,preheight,crosswalk,outfolder):
    digest(zip_path)
    birds=load_primary_gates(preheight,crosswalk)
    chosen,counts=original_first_records(zip_path)
    GPS,BARO,quality=paired_profiles(chosen,birds)
    output={
       "analysis":"FRENCH_GYPS_2019_2021_GPS_VS_BARO_5KM_INDIVIDUAL_HEIGHT_SHAPE_V1",
       "source_doi":"10.48579/PRO/IOSZNM",
       "source_archive_md5":SOURCE_MD5,
       "source_altitude_quality":quality,
       "preheight_bird_roster_sha256":FRENCH5_SHA,
       "source_noheight_gate_run":39714803696,
       "source_overlap_gate_run":39715960239,
       "original_medgull_kernel_used":True,
       "native_sensor_independence_proven":False,
       "terminal":"unavailable",
       "sensor_results":{},
       "claim_boundary":"Two height source columns concordant under a fixed 5km source D1 setup is robust to some sensor-specific error, but not proof of biological individuality independent of tag/terrain confounding."
    }
    outfolder.mkdir(parents=True,exist_ok=True)
    if GPS is None:
        output["reason"]=quality.get("reason")
    else:
        check_two_native_sensor_same_sessions(GPS,BARO)
        for sensor,records in [("GPS",GPS),("BAROMETRIC",BARO)]:
            score,draws=score_sensor(records,sensor)
            output["sensor_results"][sensor]=score
            if draws:
                path=outfolder/(sensor+"_native_height_D1_day_null.csv")
                with path.open("w",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=list(draws[0]))
                    w.writeheader();w.writerows(draws)
        two_sensor_family(output["sensor_results"])
        if all(output["sensor_results"][sensor]["terminal"]=="supported_own_bird_altitude_shape"
               for sensor in ("GPS","BAROMETRIC")):
            output["terminal"]="paired_sensor_robust_individual_height_shape"
        else:
            output["terminal"]="paired_sensor_not_established"
    (outfolder/"FRANCE_GYPS_2019_2021_GPS_BARO_DUAL_HEIGHT_RESULT_V1.json").write_text(
        json.dumps(output,indent=2,sort_keys=True)+"\n"
    )
    print(json.dumps({
       "terminal":output["terminal"],"reason":output.get("reason"),
       "paired_source_fraction":quality["source_firstfix_pair_complete_fraction"],
       "paired_bird_days":quality.get("fixed_eligible_bird_days_after_paired_qc_and_50fix"),
       "sensor_studies":{
           sensor:{
              "birds":z.get("observed",{}).get("eligible_birds"),
              "mean_gain":z.get("observed",{}).get("mean_gain"),
              "null_valid":z.get("calibration",{}).get("valid"),
              "holm_p":z.get("holm_p_upper"),
              "terminal":z["terminal"]
           } for sensor,z in output["sensor_results"].items()
       }
    },sort_keys=True),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--preheight-result",type=Path,required=True)
    p.add_argument("--source-crosswalk",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opt=p.parse_args()
    preheight=json.loads(opt.preheight_result.read_text())
    cross=json.loads(opt.source_crosswalk.read_text())
    run(opt.source,preheight,cross,opt.out)


if __name__=="__main__":
    main()
