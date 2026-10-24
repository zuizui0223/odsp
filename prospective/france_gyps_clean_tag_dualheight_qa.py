#!/usr/bin/env python3
"""POST-OUTCOME QA sensitivity: exclude nonbird geodesy and native tag alias.

The original French Gyps GPS/barometric 27-bird D1 test is retained intact.
Recompute both whole study donor models after excluding pre-identified source
QA aliases, NEVER merely subtract a high/low gain for the affected bird.

Uses EXACTLY the same 2019–21 native source ZIP, GPS 5min selection, 5km
projection, 10 centered height bins, D1 balanced day/bird weights, original
UTC-day whole-label nulls (999) and two-test Holm. Not new confirmation.
"""
from __future__ import annotations

import argparse,csv,hashlib,json
from pathlib import Path

from . import france_gyps_2019_dualsensor_identity as original

EXCLUDED={
    "Test géodésie ornitela",
    "2018-Causses-Ad-Peycare-HTK-182208",
    "2019-Causses-Ad-Mostuejouls-IIE-182008"
}
EXCLUDED_TAG="182208"
OLD_28_SHA="031d6226418cc0291a48d7d4eb44f1cae003df3a411ef3767a5229dbd45b1928"
CLEAN_27_SHA="d9feed17cd780ed1be1c5fcd275471a0f741dfa565aa5995cbd7d71841ded34c"
ORIGINAL_OUTCOME_RUN=39716885648
CLEAN_SOURCE_RUN=39720327589
EXPECTED_OLD_SCORED=27


def sha_ids(names):
    return hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()


def verify_preheight(old_preheight,original_crosswalk,clean_QA):
    old_ids=original.load_primary_gates(old_preheight,original_crosswalk)
    if len(old_ids)!=28 or sha_ids(old_ids)!=OLD_28_SHA:
        raise ValueError("Original 28 birds preheight roster changed")
    if clean_QA.get("numeric_native_GPS_height_values_read") is not False:
        raise ValueError("Clean source sample was not selected without altitude")
    if clean_QA.get("source_zip_md5")!=original.SOURCE_MD5:
        raise ValueError("Clean source was made on different native archive")
    if clean_QA["quarantined_nonbiological_animal_IDs"]!=["Test géodésie ornitela"]:
        raise ValueError("Expected exactly one source nonbird geodesy test")
    if clean_QA["tags_aliased_to_multiple_biological_bird_IDs"]!={EXCLUDED_TAG:sorted(EXCLUDED-{"Test géodésie ornitela"})}:
        raise ValueError("Historical source collision IDs changed, do not data-mine")
    source_ids=set(clean_QA["selected_animal_IDs"])
    if len(source_ids)!=29 or "Test géodésie ornitela" in source_ids:
        raise ValueError("Source correction did not produce 29 wild bird labels")
    old_qa_5km=set(clean_QA["horizontal_day_eligibility_by_cell_m"]["5000"]["admitted_bird_ids"])
    if old_ids!=old_qa_5km:
        raise ValueError("Noheight QA original 28 5km matched birds changed")
    clean=old_ids-EXCLUDED
    if len(clean)!=27 or sha_ids(clean)!=CLEAN_27_SHA:
        raise ValueError("Expected exact source-only 27-bird clean 5km roster")
    return clean


def check_historical_result(original_result,clean_ids):
    if original_result["terminal"]!="paired_sensor_robust_individual_height_shape":
        raise ValueError("Historical original dual-sensor status changed")
    if original_result["preheight_bird_roster_sha256"]!=OLD_28_SHA:
        raise ValueError("Historical original fixed 28 bird population changed")
    scored=set(original_result["sensor_results"]["GPS"]["observed"]["per_bird"])
    if len(scored)!=EXPECTED_OLD_SCORED:
        raise ValueError("Unexpected original height scoring population")
    if set(original_result["sensor_results"]["BAROMETRIC"]["observed"]["per_bird"])!=scored:
        raise ValueError("Historical GPS/baro not on same scored birds")
    overlap=scored&clean_ids
    if (len(overlap)!=26 or
        scored-clean_ids!={"2019-Causses-Ad-Mostuejouls-IIE-182008"}):
        raise ValueError("Expected original score/tag quarantined population overlap changed")
    return scored


def compare_sensors(sensors,previous):
    matched=set.intersection(*(set(sensors[name]["observed"]["per_bird"]) for name in ("GPS","BAROMETRIC")))
    old=set(previous["sensor_results"]["GPS"]["observed"]["per_bird"])
    matched_old=matched&old
    result={
      "final_clean_sensor_scored_birds":len(matched),
      "old_scored_birds_retained_exact":len(matched_old),
      "old_scored_birds_lost_exact":len(old-matched),
      "newly_scored_birds_after_clean_source":sorted(matched-old),
      "GPS_positive_raw_gain_birds":sum(
          rec["gain"]>0 for rec in sensors["GPS"]["observed"]["per_bird"].values()),
      "BARO_positive_raw_gain_birds":sum(
          rec["gain"]>0 for rec in sensors["BAROMETRIC"]["observed"]["per_bird"].values()),
      "same_bird_positive_both":sum(
          sensors["GPS"]["observed"]["per_bird"][b]["gain"]>0 and
          sensors["BAROMETRIC"]["observed"]["per_bird"][b]["gain"]>0 for b in matched),
      "recomputed_Holm_p_by_native_sensor":{name:sensors[name].get("holm_p_upper")
                                         for name in sensors},
      "original_historical_n27_Holm_p":{"GPS":previous["sensor_results"]["GPS"]["holm_p_upper"],
                                       "BAROMETRIC":previous["sensor_results"]["BAROMETRIC"]["holm_p_upper"]},
      "historical_old_result_reinterpreted_as_clean":False
    }
    return result


def run(zip_path,old_preheight,old_crosswalk,clean_noheight,old_outcome,outfolder):
    original.digest(zip_path)
    clean=verify_preheight(old_preheight,old_crosswalk,clean_noheight)
    check_historical_result(old_outcome,clean)
    first,count=original.original_first_records(zip_path)
    source_all={b for b,d,i in first}
    if len(source_all)!=30 or "Test géodésie ornitela" not in source_all:
        raise ValueError("Original ZIP no longer has 30 native labels plus test")
    reselected={key:v for key,v in first.items() if key[0] not in EXCLUDED}
    if len({key[0] for key in reselected})!=27:
        raise ValueError("Source QA exclusion did not produce 27 biological labels")
    if len(reselected)>len(first) or not clean<=set(k[0] for k in reselected):
        raise ValueError("Unexpected clean original source event selection")
    GPS,BARO,quality=original.paired_profiles(reselected,clean)
    result={
      "analysis":"FRANCE_GYPS_CLEAN_2019_2021_TAG_AND_NONBIRD_QUARANTINE_DUALHEIGHT_QA_V1",
      "source_doi":"10.48579/PRO/IOSZNM",
      "source_zip_md5":original.SOURCE_MD5,
      "noheight_original_source_run":39714803696,
      "source_noheight_clean_QA_run":CLEAN_SOURCE_RUN,
      "historical_source_height_run":ORIGINAL_OUTCOME_RUN,
      "clean_5km_original_height_unaware_roster_SHA256":CLEAN_27_SHA,
      "clean_preheight_birds":len(clean),
      "all_original_source_labels":len(source_all),
      "after_excluding_nonbirds_and_reused_tags":len({k[0] for k in reselected}),
      "excluded_exact_source_labels":sorted(EXCLUDED),
      "native_original_five_minute_fix_count":len(first),
      "clean_five_minute_fix_count":len(reselected),
      "unchanged_height_model":"MEDGULL D1 balanced; same 5km/ten centered bins/999 whole UTC-day relabelled null each native modality",
      "source_altitude_quality":quality,
      "classification":"POST_OUTCOME_SOURCE_QUALITY_SENSITIVITY",
      "native_sensor_physical_independence_proven":False,
      "source_parent_device_aliases_fully_resolved":False,
      "original_biological_endpoint_modified":False,
      "status":"unavailable",
      "sensor_results":{}
    }
    outfolder.mkdir(parents=True,exist_ok=True)
    if GPS is None or BARO is None:
        result["reason"]=quality.get("reason")
    else:
        original.check_two_native_sensor_same_sessions(GPS,BARO)
        for name,sessions in (("GPS",GPS),("BAROMETRIC",BARO)):
            s,draws=original.score_sensor(sessions,name)
            result["sensor_results"][name]=s
            if draws:
                with (outfolder/(name+"_CLEAN_SOURCE_999_day_null.csv")).open("w",newline="") as f:
                    w=csv.DictWriter(f,fieldnames=list(draws[0]))
                    w.writeheader();w.writerows(draws)
        original.two_sensor_family(result["sensor_results"])
        if all(result["sensor_results"][key]["terminal"]=="supported_own_bird_altitude_shape"
               for key in ("GPS","BAROMETRIC")):
            result["status"]="clean_source_QA_both_sensor_identity_retained"
        elif any(result["sensor_results"][key]["terminal"]=="unavailable"
                 for key in ("GPS","BAROMETRIC")):
            result["status"]="clean_source_QA_unavailable"
        else:
            result["status"]="clean_source_QA_not_both_supported"
        result["original_and_clean_bird_score_comparison"]=compare_sensors(
            result["sensor_results"],old_outcome)
    path=outfolder/"FRANCE_GYPS_CLEAN_TAG_QUARANTINE_DUALHEIGHT_QA_RESULT_V1.json"
    path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "status":result["status"],
      "clean_population_before_heights":len(clean),
      "clean_GPS_scored_birds":result["sensor_results"].get("GPS",{}).get("observed",{}).get("eligible_birds"),
      "clean_BARO_scored_birds":result["sensor_results"].get("BAROMETRIC",{}).get("observed",{}).get("eligible_birds"),
      "clean_GPS_gain":result["sensor_results"].get("GPS",{}).get("observed",{}).get("mean_gain"),
      "clean_BARO_gain":result["sensor_results"].get("BAROMETRIC",{}).get("observed",{}).get("mean_gain"),
      "clean_GPS_Holm":result["sensor_results"].get("GPS",{}).get("holm_p_upper"),
      "clean_BARO_Holm":result["sensor_results"].get("BAROMETRIC",{}).get("holm_p_upper"),
      "original27_result_changed":False
    },sort_keys=True),flush=True)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--original-preheight",required=True,type=Path)
    p.add_argument("--original-crosswalk",required=True,type=Path)
    p.add_argument("--corrected-noheight",required=True,type=Path)
    p.add_argument("--historical-dualheight",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    run(a.source,json.loads(a.original_preheight.read_text()),
        json.loads(a.original_crosswalk.read_text()),
        json.loads(a.corrected_noheight.read_text()),
        json.loads(a.historical_dualheight.read_text()),
        a.out)


if __name__=="__main__":
    main()
