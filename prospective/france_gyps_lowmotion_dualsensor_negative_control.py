#!/usr/bin/env python3
"""Explore low-motion negative-control altitude identity in French Gyps.

NOT a new biological replication: same source as opened 2019-2021 flight
positive, newly predefined low-motion speed ≤1m/s and exact original
height-unaware 28-bird source roster. Opens low-motion native heights only
after the separate low-motion horizontal support receipt admits >=10 birds.
Reuses the unmodified original MEDGULL D1 scorer and two-field correction.
"""
from __future__ import annotations

import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter
from pathlib import Path

from . import france_gyps_2019_dualsensor_identity as original
from . import france_gyps_lowmotion_source_gate as source

LOWMOTION_STAGE="FRANCE_GYPS_LOWMOTION_5KM_OTHER_DAY_SOURCE_GATE_V1"
LOWSPEED=(0.,1.)
MAX_EARLIEST_DATES=3
SOURCE_PREHEIGHT_RUN=40535137506
SOURCE_FLIGHT_RESULT_RUN=39716885648


def verify_source_gates(low,high,flight_results):
    birds=source.original_preheight_bird_roster(high)
    if low.get("analysis")!=LOWMOTION_STAGE or low.get(
            "independent_native_height_values_opened") is not False:
        raise ValueError("No admitted outcome-blind low-motion source result")
    if low.get("source_MD5")!=source.ORIGINAL_MD5:
        raise ValueError("Original source checksum drift")
    if low.get("original_previous_flight_eligible_bird_roster_sha256")!=source.PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA:
        raise ValueError("Previous preheight flight bird population changed")
    eligible=set(low.get("original_eligible_lowmotion_bird_IDs") or ())
    if len(eligible)!=low.get("original_eligible_lowmotion_birds"):
        raise ValueError("Number of source-eligible low-motion biological birds drift")
    if not eligible<=birds:
        raise ValueError("Negative-control ID isn't in original 28-bird flight cohort")
    digest=hashlib.sha256("\n".join(sorted(eligible)).encode()).hexdigest()
    if digest!=low.get("lowmotion_eligible_bird_ID_sha256"):
        raise ValueError("Previously frozen low-motion source roster changed")
    if flight_results.get("analysis")!="FRENCH_GYPS_2019_2021_GPS_VS_BARO_5KM_INDIVIDUAL_HEIGHT_SHAPE_V1":
        raise ValueError("Original flight endpoint identity drift")
    if flight_results.get("terminal")!="paired_sensor_robust_individual_height_shape":
        raise ValueError("Prior endpoint not the archived positive flight result")
    if flight_results.get("preheight_bird_roster_sha256")!=source.PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA:
        raise ValueError("Original flight cohort not same source")
    if flight_results.get("source_archive_md5")!=source.ORIGINAL_MD5:
        raise ValueError("Original flight archive checksum changed")
    expected=bool(len(eligible)>=source.MIN_BIRDS)
    if low.get("admitted_for_separately_frozen_negative_control") is not expected:
        raise ValueError("Contradiction in source's separate low-motion acceptance")
    return eligible


def native_lowmotion_first_heights(path,original_flight_roster):
    """Exact same source speed/x-y/time filter as previous no-height gate.

    It is called ONLY after source eligibility has passed. Every accepted first
    event supplies BOTH original GPS MSL and native barometric height strings,
    regardless of whether those strings are parseable.
    """
    chosen={}
    native_counts=Counter()
    source.check_immutable_source(path)
    with zipfile.ZipFile(path) as z:
        members=sorted(
            [x for x in z.infolist() if not x.is_dir()
             and "Vulturestracks_" in x.filename and x.filename.endswith(".csv")
             and not x.filename.startswith("__MACOSX/")],
            key=lambda x:x.filename)
        if len(members)!=9:raise ValueError("Expected nine years/season source GPS tables")
        for member in members:
            year=next((y for y in sorted(source.YEARS) if member.filename.endswith(y+".csv")),None)
            if year is None:raise ValueError("Unknown source year")
            with z.open(member) as inner,io.TextIOWrapper(inner,encoding="utf-8-sig",errors="replace",newline="") as f:
                reader=csv.reader(f)
                hdr=next(reader)
                index={name:i for i,name in enumerate(hdr)}
                required=source.FIELDS|{original.GPS_COLUMN,original.BARO_COLUMN}
                if not required<=set(index):raise ValueError("Native source height or motion/quality metadata missing")
                def item(row,key):
                    i=index[key]
                    return row[i] if i<len(row) else ""
                for row in reader:
                    bird=item(row,"individual-local-identifier").strip()
                    if bird not in original_flight_roster:continue
                    if item(row,"individual-taxon-canonical-name").strip()!=source.SOURCE_TAXON:
                        continue
                    if item(row,"visible").strip().lower()=="false" or (
                        item(row,"import-marked-outlier").strip().lower() in ("true","1","yes","y")
                    ):continue
                    stamp=item(row,"timestamp").strip()
                    try:
                        yy=int(stamp[:4]);mm=int(stamp[5:7]);dd=int(stamp[8:10])
                        hh=int(stamp[11:13]);minute=int(stamp[14:16])
                    except (ValueError,TypeError):
                        continue
                    if str(yy)!=year or not (1<=mm<=12 and 1<=dd<=31 and
                          0<=hh<24 and 0<=minute<60):
                        continue
                    lon=source.numeric(item(row,"location-long"))
                    lat=source.numeric(item(row,"location-lat"))
                    speed=source.numeric(item(row,"ground-speed"))
                    if lon is None or lat is None or speed is None:
                        continue
                    if not(-180<=lon<=180 and -85<=lat<=85 and
                           LOWSPEED[0]<=speed<=LOWSPEED[1]):
                        continue
                    key=(bird,stamp[:10],hh*12+minute//5)
                    if key not in chosen or stamp<chosen[key][0]:
                        chosen[key]=(
                          stamp,lon,lat,
                          item(row,original.GPS_COLUMN),
                          item(row,original.BARO_COLUMN),
                          item(row,"gps:hdop"),item(row,"gps:satellite-count")
                        )
                    native_counts["lowmotion_before_fiveminute"]+=1
            print("Low motion height source 2019-21 season",member.filename,
                  "preselected_first5",len(chosen),flush=True)
    return chosen,native_counts


def test_results(source_zip,low,original_preheight,original_flight,outfolder):
    eligible=verify_source_gates(low,original_preheight,original_flight)
    out={
        "analysis":"FRANCE_GYPS_2019_2021_LOWMOTION_5KM_GPS_BARO_NEGATIVE_CONTROL_V1",
        "source_doi":"10.48579/PRO/IOSZNM",
        "source_zip_md5":source.ORIGINAL_MD5,
        "previous_flight_D1_outcome_run":SOURCE_FLIGHT_RESULT_RUN,
        "new_lowmotion_preheight_gate_run":SOURCE_PREHEIGHT_RUN,
        "status":"unavailable",
        "low_motion_speed_m_s":list(LOWSPEED),
        "motion_proxy_caution":"≤1m/s native GPS ground-speed is not a confirmed on-ground or stationary behavioural state",
        "exploratory_negative_control_not_new_confirmation":True,
        "original_flight_result_left_unchanged":True,
        "previous_highspeed_final_D1_birds":27,
        "original_flight_roster_sha":source.PRESCREEN_ORIGINAL_FLIGHT_BIRD_IDS_SHA,
        "lowmotion_original_eligibility":{
           "birds":len(eligible),
           "bird_days":low.get("lowmotion_eligible_bird_days"),
           "five_minute_source_events":low.get("lowmotion_eligible_scored_five_minute_events"),
           "roster_sha":low.get("lowmotion_eligible_bird_ID_sha256")
        },
        "sensor_results":{},
        "claim_boundary":"Low-motion source shares source tags/roost context with flight and is not a matched behavioural experiment; even if supported cannot alone determine what proportion of flight signal is tag or terrain artifact."
    }
    outfolder.mkdir(parents=True,exist_ok=True)
    if not low.get("admitted_for_separately_frozen_negative_control"):
        out["reason"]="frozen_nonheight_low_motion_5km_source_below_10_birds"
    else:
        original_flight_roster=source.original_preheight_bird_roster(original_preheight)
        source.check_immutable_source(source_zip)
        fixed,native_audit=native_lowmotion_first_heights(source_zip,original_flight_roster)
        if len(fixed)!=low.get("all_source_lowmotion_five_minute_events"):
            raise ValueError("Source's altitude-unaware earliest low-motion first-fix count changed")
        actual_ids={bird for bird,day,bin5 in fixed}
        if not eligible<=actual_ids:raise ValueError("Source low-motion bird IDs lost after opening height")
        GPS,BARO,quality=original.paired_profiles(fixed,eligible)
        out["native_low_motion_quality"]=quality
        out["source_native_filter_counts"]=dict(native_audit)
        if GPS is None:
            out["reason"]=quality.get("reason","below_fixed_dual_sensor_80pct_quality")
        else:
            original.check_two_native_sensor_same_sessions(GPS,BARO)
            matched={}
            for sensor,profiles in (("GPS",GPS),("BAROMETRIC",BARO)):
                study,draws=original.score_sensor(profiles,sensor,randomizations=999)
                out["sensor_results"][sensor]=study
                if draws:
                    with (outfolder/(sensor+"_lowmotion_D1_999_day_null.csv")).open("w",newline="") as f:
                        writer=csv.DictWriter(f,fieldnames=list(draws[0]))
                        writer.writeheader();writer.writerows(draws)
            original.two_sensor_family(out["sensor_results"])
            out["same_bird_day_GPS_and_barometric_profiles"]=True
            if all(out["sensor_results"][kind]["terminal"]=="supported_own_bird_altitude_shape"
                   for kind in ("GPS","BAROMETRIC")):
                out["status"]="exploratory_lowmotion_both_native_heights_support_identity"
            elif any(out["sensor_results"][kind]["terminal"]=="unavailable"
                      for kind in ("GPS","BAROMETRIC")):
                out["reason"]="at_least_one_native_sensor_D1_permutation_or_bird_minimum_unavailable"
            else:
                out["status"]="exploratory_lowmotion_native_heights_not_both_supported"
            matched_birds=set(out["sensor_results"].get("GPS",{}).get("observed",{}).get("per_bird",{})) & set(
                original_flight["sensor_results"]["GPS"]["observed"]["per_bird"])
            out["descriptive_same_bird_flight_and_lowmotion"]={
                "n_same_birds":len(matched_birds),
                "shared_bird_id_sha256":hashlib.sha256("\n".join(sorted(matched_birds)).encode()).hexdigest(),
                "GPS_mean_lowmotion_gain":(
                    float(sum(out["sensor_results"]["GPS"]["observed"]["per_bird"][b]["gain"]
                         for b in matched_birds)/len(matched_birds)) if matched_birds else None
                ),
                "GPS_mean_original_flight_gain_over_same_birds":(
                    float(sum(original_flight["sensor_results"]["GPS"]["observed"]["per_bird"][b]["gain"]
                         for b in matched_birds)/len(matched_birds)) if matched_birds else None
                ),
                "not_comparable_as_matched_same_location_day":True,
            }
    (outfolder/"FRANCE_GYPS_LOWMOTION_DUAL_HEIGHT_NEGATIVE_CONTROL_RESULT_V1.json").write_text(
         json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":out["status"],"reason":out.get("reason"),
      "preheight_birds":len(eligible),
      "GPS_scored_birds":out.get("sensor_results",{}).get("GPS",{}).get("observed",{}).get("eligible_birds"),
      "barometric_scored_birds":out.get("sensor_results",{}).get("BAROMETRIC",{}).get("observed",{}).get("eligible_birds"),
      "GPS_Holm":out.get("sensor_results",{}).get("GPS",{}).get("holm_p_upper"),
      "BARO_Holm":out.get("sensor_results",{}).get("BAROMETRIC",{}).get("holm_p_upper"),
      "both_sensor_native_QC_valid_fraction":out.get("native_low_motion_quality",{}).get("source_firstfix_pair_complete_fraction")
    },sort_keys=True),flush=True)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",required=True,type=Path)
    p.add_argument("--lowmotion-preheight",required=True,type=Path)
    p.add_argument("--original-flight-preheight",required=True,type=Path)
    p.add_argument("--original-flight-result",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    opts=p.parse_args()
    source_data=json.loads(opts.lowmotion_preheight.read_text())
    old_preheight=json.loads(opts.original_flight_preheight.read_text())
    flight_result=json.loads(opts.original_flight_result.read_text())
    test_results(opts.source_zip,source_data,old_preheight,flight_result,opts.out)


if __name__=="__main__":
    main()
