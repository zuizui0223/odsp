#!/usr/bin/env python3
"""Post-outcome DEM-referenced French Gyps height identity sensitivity.

DO NOT call this an independent ecological replication: the same GPS/barometric
native height outcomes were previously opened in run 39716885648.

Uses the exact frozen 28-bird source roster, first 5-min GPS records and native
paired-height validation, then subtracts the original archive's DEM at those
same GPS positions. Never rescue poor source DEM coverage by altering grid,
days, altitude bins, sensor variables, birds or study seasons.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,zipfile
from collections import Counter,defaultdict
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

from . import france_gyps_2019_dualsensor_identity as original
from . import medgull_sensitivity as d1

DEM_MEMBER="windTurbineAvoidance/Data/RawData/Elevation_Causses.tif"
DEM_BYTES=45336059
DEM_CRC32=0xd7b033fb
MIN_DEM_VALID_FRACTION=.80
RNG_SEED=20261025
DRAW_N=999
MIN_N_VALID=950
MIN_BIRDS=10

def read_dem_metadata(path):
    with rasterio.open(path) as ds:
        if ds.crs is None or ds.count!=1:
            raise ValueError("Archived original Causses DEM lacks known single-band CRS")
        return {
            "crs_wkt":ds.crs.to_wkt(),
            "crs_epsg":ds.crs.to_epsg(),
            "width":ds.width,"height":ds.height,
            "affine":list(ds.transform)[:6],
            "pixel_size_projected_units":[ds.res[0],ds.res[1]],
            "native_nodata":ds.nodata,
            "data_type":ds.dtypes[0],
            "bounds":[ds.bounds.left,ds.bounds.bottom,ds.bounds.right,ds.bounds.top],
            "band_count":ds.count,
            "native_vertical_datum":"NOT_ESTABLISHED_FROM_TIFF_CRS",
        }


def verify_original_primary(preheight,crosswalk,original_height):
    birds=original.load_primary_gates(preheight,crosswalk)
    if len(birds)!=28:
        raise ValueError("Original frozen 28-source-bird roster changed")
    if original_height.get("terminal")!="paired_sensor_robust_individual_height_shape":
        raise ValueError("Original previously opened paired-height outcome absent")
    if original_height["preheight_bird_roster_sha256"]!=original.FRENCH5_SHA:
        raise ValueError("Original paired-height test no longer tied to source roster")
    if original_height["source_archive_md5"]!=original.SOURCE_MD5:
        raise ValueError("Original GPS/barometric archive source checksum drifted")
    for sensor in ("GPS","BAROMETRIC"):
        s=original_height["sensor_results"][sensor]
        if s["observed"]["eligible_birds"]!=27 or s["observed"]["eligible_bins"]!=364520:
            raise ValueError("Original 27-bird identical source GPS-fix study drifted")
        if s["terminal"]!="supported_own_bird_altitude_shape":
            raise ValueError("Original source sensor result category drifted")
    return birds


def sample_dem_for_source(dempath, chosen, original_birds, chunk_size=50000):
    """Return DEM MSL-like heights keyed by immutable native source 5min event.

    DEM coverage computed from original first-selected X/Y, NEVER native GPS or
    barometric altitude availability, preserving an independent geography gate.
    """
    keys=[k for k in chosen if k[0] in original_birds]
    dem={} ; count=Counter()
    report=read_dem_metadata(dempath)
    if not keys:raise ValueError("Original 28 bird source GPS events not found")
    with rasterio.open(dempath) as raster:
        transform=Transformer.from_crs("EPSG:4326",raster.crs,always_xy=True)
        for begin in range(0,len(keys),chunk_size):
            group=keys[begin:begin+chunk_size]
            xs=np.array([chosen[k][1] for k in group],float)
            ys=np.array([chosen[k][2] for k in group],float)
            px,py=transform.transform(xs,ys)
            iterable=raster.sample(zip(px,py),indexes=[1],masked=True)
            for key,elev in zip(group,iterable):
                val=elev[0]
                if np.ma.is_masked(val):
                    dem[key]=None
                    count["masked_or_outside_dem"]+=1
                    continue
                height=float(val)
                if not math.isfinite(height) or (raster.nodata is not None and
                         np.isclose(height,raster.nodata)):
                    dem[key]=None
                    count["nonfinite_or_nodata_dem"]+=1
                    continue
                dem[key]=height
                count["valid_dem_elevation"]+=1
            if len(dem)!=begin+len(group):
                raise AssertionError("DEM pixel sampler skipped native XY fix")
    report["original_source_events_eligible_28_birds"]=len(keys)
    report["valid_dem_events"]=count["valid_dem_elevation"]
    report["fraction_geographically_covered"]=count["valid_dem_elevation"]/len(keys)
    report["dem_missing_reasons"]=dict(count)
    report["dem_cover_gate_admitted"]=report["fraction_geographically_covered"]>=MIN_DEM_VALID_FRACTION
    report["native_height_values_used_for_dem_coverage"]=False
    report["native_sensor_independence_proven"]=False
    return dem,report


def terrain_subtracted_source(chosen, dem, original_birds):
    """Keep SAME native source events where DEM is valid; no replacement fixes."""
    converted={}
    counts=Counter()
    for k,z in chosen.items():
        if k[0] not in original_birds:continue
        ground=dem.get(k)
        counts["eligible_source_first_fix"]+=1
        if ground is None:
            counts["without_independent_dem"]+=1
            continue
        ts,lon,lat,gps,baro,hdop,sat=z
        g=original.asfloat(gps)
        b=original.asfloat(baro)
        if g is None or not original.HEIGHT_MIN<=g<=original.HEIGHT_MAX:
            gg=None;counts["native_GPS_missing_or_outside_fixed_bounds"]+=1
        else:gg=g-ground
        if b is None or not original.HEIGHT_MIN<=b<=original.HEIGHT_MAX:
            bb=None;counts["native_BARO_missing_or_outside_fixed_bounds"]+=1
        else:bb=b-ground
        if gg is not None and not original.HEIGHT_MIN<=gg<=original.HEIGHT_MAX:
            gg=None;counts["GPS_AGL_proxy_outside_fixed_bounds"]+=1
        if bb is not None and not original.HEIGHT_MIN<=bb<=original.HEIGHT_MAX:
            bb=None;counts["BARO_AGL_proxy_outside_fixed_bounds"]+=1
        converted[k]=(ts,lon,lat,gg,bb,hdop,sat)
        counts["source_fixes_dem_available"]+=1
    if counts["eligible_source_first_fix"]!=len(dem):
        raise AssertionError("DEM geographic cohort not exactly frozen 28 source birds")
    return converted,dict(counts)


def score_one_agl_sensor(sessions,sensor):
    x=d1.pack(sessions)
    observed=d1.evaluate(x,1,"balanced")
    report={"sensor":sensor,
            "terminal":"unavailable",
            "observed":{k:v for k,v in observed.items() if k!="day_scored_bins"}}
    if observed["eligible_birds"]<MIN_BIRDS:
        report["reason"]="fewer_than_10_scored_birds_after_original_dem_coverage"
        return report,[]
    rng=np.random.default_rng(RNG_SEED)
    null=[]
    for i in range(DRAW_N):
        shuffled=d1.permute_labels(x,rng)
        scores=d1.evaluate(x,1,"balanced",labels=shuffled)
        valid=scores["eligible_birds"]>=MIN_BIRDS and scores["mean_gain"] is not None
        null.append({"draw":i+1,
                     "gain":scores["mean_gain"] if valid else None,
                     "eligible_birds":scores["eligible_birds"],
                     "eligible_days":scores["eligible_days"],
                     "eligible_bins":scores["eligible_bins"]})
        if (i+1)%200==0:print("DEM_AGL",sensor,"source permutations",i+1,flush=True)
    cal=d1.calibrate(observed["mean_gain"],[r["gain"] for r in null],DRAW_N)
    report["calibration"]=cal
    if cal["valid"]<MIN_N_VALID:
        report["reason"]="fewer_than_950_of_999_valid_day_label_exchanges"
    else:report["terminal"]="tested_before_two_source_Holm"
    return report,null


def apply_fixed_two_sensor_holm(s):
    order=sorted(s,key=lambda sensor:
        s[sensor].get("calibration",{}).get("p_upper",1)
        if s[sensor]["terminal"]=="tested_before_two_source_Holm" else 1)
    running=0.
    for i,name in enumerate(order):
        r=s[name]
        family=(r.get("calibration",{}).get("p_upper",1)
                if r["terminal"]=="tested_before_two_source_Holm" else 1.)
        running=max(running,min(1.,(len(s)-i)*family))
        r["family_p_value"]=family
        r["Holm_p_upper"]=running
        if r["terminal"]=="tested_before_two_source_Holm":
            support=(r["calibration"]["observed_minus_valid_null_mean"]>0 and
                     running<.05)
            r["terminal"]="AGL_shape_identity_supported" if support else "AGL_shape_identity_not_supported"
    return s


def descriptive_cross_sensor_comparison(source_sensor_results, original_height):
    # Same sensor gain is compared per bird; this is a POST-OUTCOME descriptive
    # concordance check and never an independent biological p-value.
    out={}
    for sensor,new in source_sensor_results.items():
        now=new["observed"].get("per_bird",{})
        before=original_height["sensor_results"][sensor]["observed"]["per_bird"]
        both=sorted(set(now)&set(before))
        y=[now[b]["gain"] for b in both]
        x=[before[b]["gain"] for b in both]
        rho=None
        if len(both)>=3 and np.std(x)>0 and np.std(y)>0:
            rho=float(np.corrcoef(x,y)[0,1])
        out[sensor]={
            "same_birds_in_old_and_dem_corrected_result":len(both),
            "correlation_original_MSL_gain_vs_dem_corrected_AGL_gain":rho,
            "original_bird_positive_gains_in_common":sum(before[b]["gain"]>0 for b in both),
            "dem_corrected_bird_positive_gains_in_common":sum(now[b]["gain"]>0 for b in both),
            "outcome_stage":"POST_OUTCOME_DESCRIPTIVE"
        }
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--original-dem",type=Path,required=True)
    p.add_argument("--preheight-receipt",type=Path,required=True)
    p.add_argument("--source-crosswalk",type=Path,required=True)
    p.add_argument("--original-height-result",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)

    old_source=json.loads(a.preheight_receipt.read_text())
    old_cross=json.loads(a.source_crosswalk.read_text())
    old_height=json.loads(a.original_height_result.read_text())
    original.digest(a.source)
    birds=verify_original_primary(old_source,old_cross,old_height)
    first,_=original.original_first_records(a.source)
    dem,surface=sample_dem_for_source(a.original_dem,first,birds)
    result={
        "analysis":"FRANCE_GYPS_2019_2021_TERRAIN_AGL_TWO_SENSOR_SENSITIVITY_V1",
        "source_doi":"10.48579/PRO/IOSZNM",
        "source_original_zip_md5":original.SOURCE_MD5,
        "source_original_dem_member":DEM_MEMBER,
        "source_original_dem_crc32":f"{DEM_CRC32:08x}",
        "source_original_dem_uncompressed_bytes":DEM_BYTES,
        "original_5km_bird_roster_sha256":original.FRENCH5_SHA,
        "original_GPS_and_BARO_identity_run":39716885648,
        "post_outcome_diagnostic_only":True,
        "native_vertical_datum_agreement_proven":False,
        "DEM_metadata_and_coverage":surface,
        "terminal":"unavailable",
        "source_sensor_results":{}
    }
    if not surface["dem_cover_gate_admitted"]:
        result["reason"]="original_geographic_dem_coverage_below_frozen_80percent"
    else:
        corrected,sourceQC=terrain_subtracted_source(first,dem,birds)
        result["AGL_proxy_source_quality"]=sourceQC
        gps,baro,quality=original.paired_profiles(corrected,birds)
        result["paired_dem_corrected_altitude_quality"]= {
            k:v for k,v in quality.items() if k!="per_day_sensor_agreement_descriptive"
        }
        if gps is None:
            result["reason"]=quality.get("reason","paired_source_quality_unavailable")
        else:
            original.check_two_native_sensor_same_sessions(gps,baro)
            for name,sessions in (("GPS",gps),("BAROMETRIC",baro)):
                scored,draws=score_one_agl_sensor(sessions,name)
                result["source_sensor_results"][name]=scored
                if draws:
                    with (a.out/(name+"_DEM_AGL_posthoc_D1_null.csv")).open("w",newline="") as f:
                        writer=csv.DictWriter(f,fieldnames=list(draws[0]))
                        writer.writeheader();writer.writerows(draws)
            apply_fixed_two_sensor_holm(result["source_sensor_results"])
            result["original_vs_DEM_AGL_descriptive"]=descriptive_cross_sensor_comparison(
                result["source_sensor_results"],old_height)
            complete=all(result["source_sensor_results"][name]["terminal"]==
                        "AGL_shape_identity_supported" for name in ("GPS","BAROMETRIC"))
            result["terminal"]=(
                "both_AGL_proxy_sensor_shifts_supported_exploratory" if complete
                else "terrain_Agl_robust_identity_not_established"
            )
    fname=a.out/"FRANCE_GYPS_2019_2021_DEM_AGL_POSTHOC_RESULT_V1.json"
    fname.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "source_dem_coverage_fraction":surface["fraction_geographically_covered"],
        "source_dem_crs":surface["crs_epsg"],
        "terrain_gate_admitted":surface["dem_cover_gate_admitted"],
        "terminal":result["terminal"],
        "reason":result.get("reason"),
        "new_AGL_sensors":{
            name:{
              "birds":s["observed"]["eligible_birds"],
              "days":s["observed"]["eligible_days"],
              "fixes":s["observed"]["eligible_bins"],
              "raw_gain":s["observed"]["mean_gain"],
              "null_excess":s.get("calibration",{}).get("observed_minus_valid_null_mean"),
              "p_holm":s.get("Holm_p_upper"),
              "status":s["terminal"]
            } for name,s in result["source_sensor_results"].items()
        }
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
