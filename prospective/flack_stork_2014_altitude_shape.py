#!/usr/bin/env python3
"""Independent 2014 50km nestling white-stork flight-height profile identity.

Uses unchanged MEDGULL day-balanced shape scoring kernel, with age-stratified
date-level whole-session identity-label nulls. Separate from prior 5km gull
estimator and no statement about causal wind response.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,io,json,math,zipfile
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from pyproj import Transformer
from . import medgull_sensitivity as engine
from . import stork_2014_xytime_source_screen as original

ZIP_NAME='Fall migration of white storks in 2014-gps.csv.zip'
GPS_MD5='c1fa0c4ca28d3fce5d61caaac36e87d2'
REFERENCE_NAME='Fall migration of white storks in 2014-reference-data.csv'
REFERENCE_MD5='116a3d82cd11e1bb4e16b32532725359'
PREHEIGHT_FINGERPRINT="a741d2e1bc13d91a49f30ddb2cd13af97db855fd8be3d6c407b75ce827d1ec7d"
EXPECTED_PREHEIGHT_FLIGHT_BIRDS=59
EXPECTED_PREHEIGHT_50KM_BIRDS=11
SEED=20261020
NULL_DRAWS=999
MIN_NULL_VALID=950
MIN_BIRDS=10
MIN_HEIGHT=-500.0
MAX_HEIGHT=6000.0
PROJECTION=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True)
CELL_M=50000


def check_source(zip_path:Path,reference:Path):
    original.check(zip_path,ZIP_NAME,GPS_MD5)
    original.check(reference,REFERENCE_NAME,REFERENCE_MD5)


def source_csv(zip_path:Path):
    z=zipfile.ZipFile(zip_path)
    members=[m for m in z.namelist() if m.lower().endswith(".csv") and not m.startswith("__MACOSX")]
    if len(members)!=1:
        z.close();raise ValueError("Expected one primary GPS CSV")
    bf=z.open(members[0])
    text=io.TextIOWrapper(bf,encoding="utf-8-sig",newline="")
    return z, text


def read_age(reference:Path):
    with reference.open("r",encoding="utf-8-sig",newline="") as fp:
        return original.read_reference(csv.DictReader(fp))


def verify_structural_gate(zip_path:Path,stage):
    z,t=source_csv(zip_path)
    try:
        # Reuse exact source-year and 50km scanner without changing any filter.
        if original.YEAR!=2014:
            raise ValueError('The source scanner year changed')
        pre=original.audit(csv.DictReader(t),stage)
    finally:
        t.close();z.close()
    q=pre["horizontal_support_by_grid_m"]["50000"]
    if (q["eligible_bird_id_fingerprint_sha256"]!=PREHEIGHT_FINGERPRINT
        or q["birds_with_2_scorable_shared_cell_days"]!=EXPECTED_PREHEIGHT_50KM_BIRDS
        or pre["GPS_time_speed_xy_rows"]["birds_with_thinned_flight"]!=EXPECTED_PREHEIGHT_FLIGHT_BIRDS):
        raise ValueError("Initial height-blind 2013 movement support drift")
    if not q["admitted"]:
        raise ValueError("New migratory horizontal support was not admitted")
    return pre


def extract_selected_altitude(zip_path:Path):
    z,t=source_csv(zip_path)
    earliest={}
    c=Counter()
    try:
        reader=csv.DictReader(t)
        native=set(reader.fieldnames or [])
        required={"timestamp","individual-local-identifier","location-long","location-lat",
                  "ground-speed","height-above-ellipsoid"}
        if not required<=native:
            raise ValueError("Native ellipsoid height / x-y / IDs unavailable")
        for r in reader:
            bird=(r.get("individual-local-identifier") or "").strip()
            if not bird:continue
            stamp=(r.get("timestamp") or "").strip()
            try:year,month,hour,minute=int(stamp[:4]),int(stamp[5:7]),int(stamp[11:13]),int(stamp[14:16])
            except (ValueError,TypeError):continue
            if year!=2014 or month not in (8,9,10,11) or not(0<=hour<24 and 0<=minute<60):
                continue
            if (r.get("visible") or "").strip().lower()=="false" or any(
                (r.get(k) or "").strip().lower() in ("true","1","yes")
                for k in ("import-marked-outlier","manually-marked-outlier")):
                continue
            try:
                lon,lat,speed=float(r["location-long"]),float(r["location-lat"]),float(r["ground-speed"])
            except (TypeError,ValueError):continue
            if not all(math.isfinite(v) for v in (lon,lat,speed)):
                continue
            if not (-180<=lon<=180 and -86<=lat<=86 and 5<=speed<=55):
                continue
            key=(bird,stamp[:10],hour*12+minute//5)
            if key not in earliest or stamp<earliest[key][0]:
                earliest[key]=(stamp,lon,lat,r.get("height-above-ellipsoid",""))
            c["raw_eligible_flight_events"]+=1
    finally:
        t.close();z.close()
    c["selected_5min_flight_fixes"]=len(earliest)
    if len(earliest)!=58971:
        raise ValueError("Frozen altitude-blind cohort size unexpectedly changed")

    daily=defaultdict(list)
    for (bird,day,bin5),(stamp,lon,lat,h_raw) in earliest.items():
        try:h=float(h_raw)
        except (ValueError,TypeError):
            c["native_height_missing"]+=1;continue
        if not math.isfinite(h):
            c["native_height_missing"]+=1;continue
        if not MIN_HEIGHT<=h<=MAX_HEIGHT:
            c["native_height_out_of_bounds"]+=1;continue
        east,north=PROJECTION.transform(lon,lat)
        if not(math.isfinite(east) and math.isfinite(north)):
            raise ValueError("Projection of previously valid horizontal position failed")
        cell=(math.floor(east/CELL_M),math.floor(north/CELL_M))
        daily[bird,day].append((cell,h))
        c["native_height_valid"]+=1

    sessions=[]
    for (bird,day),records in sorted(daily.items()):
        heights=np.asarray([z for cell,z in records],float)
        offset=np.median(heights)
        bins=np.searchsorted(engine.EDGES,heights-offset,side="right")-1
        hist=defaultdict(lambda:np.zeros(10,np.int64))
        for (cell,h),bi in zip(records,bins):
            if not 0<=bi<10:raise AssertionError("Invalid fixed 10-bin height")
            hist[cell][int(bi)]+=1
        sessions.append({"animal":bird,"day":day,"hist":dict(hist)})
    c["valid_sessions"]=len(sessions)
    c["altitude_valid_fraction"]=c["native_height_valid"]/len(earliest)
    return sessions,dict(c)


def labels_permuted_age_day(x,ages,rng):
    """Preserve each day's number of juvenile/adult labelled bird sessions."""
    labels=x["labels"].copy()
    age_by_id=[ages.get(name,"unknown") for name in x["ids"]]
    for ix in x["date_groups"]:
        slots=defaultdict(list)
        for k in ix:
            slots[age_by_id[int(labels[k])]].append(int(k))
        for indices in slots.values():
            if len(indices)>1:
                labels[indices]=rng.permutation(labels[indices])
    return labels


def age_counts(per_bird,ages):
    cnt=Counter()
    for bird in per_bird:cnt[ages.get(bird,"unknown")]+=1
    return dict(sorted(cnt.items()))


def run_primary(x,ages,draws=999):
    observed=engine.evaluate(x,1,"balanced")
    pre=engine.support(x,1)
    if not np.array_equal(pre["day_scored_bins"],observed["day_scored_bins"]):
        raise AssertionError("Preflight and observation score support differ")
    report={
        "observed":{k:v for k,v in observed.items() if k!="day_scored_bins"},
        "eligible_by_age":age_counts(observed["per_bird"],ages),
        "terminal":"unavailable",
        "original_5km_source_gate_restored":False
    }
    n=observed["eligible_birds"]
    known=sum(ages.get(b,"unknown") in ("nestling",) for b in observed["per_bird"])
    if n<MIN_BIRDS:
        report["reason"]="native_height_supported_birds_below_ten";return report,[]
    if known/n<.95:
        report["reason"]="unambiguous_age_crosswalk_below_95pct";return report,[]
    rng=np.random.default_rng(SEED)
    null=[]
    for i in range(draws):
        labels=labels_permuted_age_day(x,ages,rng)
        nfix,gains=engine.kernel(x,1,labels,True)
        stats=engine.summarise(x,nfix,gains[1],labels)
        valid=stats["eligible_birds"]>=MIN_BIRDS and stats["mean_gain"] is not None and math.isfinite(stats["mean_gain"])
        null.append({"draw":i+1,
            "gain":stats["mean_gain"] if valid else None,
            "eligible_birds":stats["eligible_birds"],
            "eligible_days":stats["eligible_days"],
            "labels_changed_fraction":float(np.mean(labels!=x["labels"]))})
        if (i+1)%100==0:print("Stork-age-null",i+1,flush=True)
    cal=engine.calibrate(observed["mean_gain"],[r["gain"] for r in null],draws)
    report["calibration"]=cal
    report["null_eligible_birds_range"]=[min(r["eligible_birds"] for r in null),max(r["eligible_birds"] for r in null)]
    report["mean_label_fraction_changed"]=float(np.mean([r["labels_changed_fraction"] for r in null]))
    if cal["valid"]<MIN_NULL_VALID or report["mean_label_fraction_changed"]<=0:
        report["reason"]="insufficient_age_stratified_null_support"
    else:
        report["terminal"]=("supported_50km_individual_height_shape"
            if cal["p_upper"]<.05 and cal["observed_minus_valid_null_mean"]>0
            else "not_supported_50km_individual_height_shape")
    return report,null


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gps-zip",type=Path,required=True)
    p.add_argument("--reference",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opt=p.parse_args()
    opt.out.mkdir(parents=True,exist_ok=True)
    check_source(opt.gps_zip,opt.reference)
    ages,metadata=read_age(opt.reference)
    pre=verify_structural_gate(opt.gps_zip,ages)
    sessions,q=extract_selected_altitude(opt.gps_zip)
    result={
        "analysis":"FLACK_STORK_2014_INDEPENDENT_50KM_VERTICAL_IDENTITY_V1",
        "source_doi":"10.5441/001/1.bj96m274","source_gps_md5":GPS_MD5,
        "source_ref_md5":REFERENCE_MD5,"source_year":2014,
        "preheight_fingerprint_verified":pre["horizontal_support_by_grid_m"]["50000"]["eligible_bird_id_fingerprint_sha256"],
        "preheight_source_run":39415189033,
        "preheight_5km_birds":pre["horizontal_support_by_grid_m"]["5000"]["birds_with_2_scorable_shared_cell_days"],
        "preheight_50km_birds":pre["horizontal_support_by_grid_m"]["50000"]["birds_with_2_scorable_shared_cell_days"],
        "preheight_100km_birds":pre["horizontal_support_by_grid_m"]["100000"]["birds_with_2_scorable_shared_cell_days"],
        "separate_migrant_scale_estimator":True,
        "altitude_observed_only_after_metadata_gate":True,
        "quality":q,
        "measurement_confound":"Uncalibrated GPS height above ellipsoid; matching 50km cells does not remove topography or device error",
        "terminal":"unavailable"
    }
    if q["altitude_valid_fraction"]<.8:
        result["reason"]="altitude_quality_below_80pct"
    else:
        x=engine.pack(sessions)
        outcome,draws=run_primary(x,ages,999)
        result.update(outcome)
        if draws:
            with (opt.out/"flack_stork_2014_date_null.csv").open("w",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=list(draws[0]))
                writer.writeheader();writer.writerows(draws)
        if "observed" in result:
            with (opt.out/"flack_stork_2014_per_bird_scores.csv").open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=["bird","age","days","bins","gain"])
                w.writeheader()
                for bird,v in sorted(result["observed"]["per_bird"].items()):
                    w.writerow({"bird":bird,"age":ages.get(bird,"unknown"),**v})
    (opt.out/"FLACK_STORK_2014_ALTITUDE_SHAPE_RESULT_V1.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "terminal":result["terminal"],"reason":result.get("reason"),
        "height_fraction":q["altitude_valid_fraction"],
        "scored_birds":result.get("observed",{}).get("eligible_birds"),
        "age_breakdown":result.get("eligible_by_age"),
        "bird_days":result.get("observed",{}).get("eligible_days"),
        "scored_fixes":result.get("observed",{}).get("eligible_bins"),
        "observed_gain":result.get("observed",{}).get("mean_gain"),
        "null_p_upper":result.get("calibration",{}).get("p_upper"),
        "null_valid":result.get("calibration",{}).get("valid"),
        "null_excess":result.get("calibration",{}).get("observed_minus_valid_null_mean")
    },sort_keys=True))


if __name__=="__main__":
    main()
