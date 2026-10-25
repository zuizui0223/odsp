#!/usr/bin/env python3
"""First numeric same-taxonomy new-source GPS trial; original study files only.
Prior three-source source-calendar receipt verified byte-for-byte before data.
Wolves/Florida deer calendar-ineligible sources explicitly HOLD. New Alberta
elk numerical movement strictly uses the unchanged previous analyze_file().
No source individual ID, exact position or event times exported.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download,inspect_csv
from scripts.movebank_same_taxon_three_source_only_20261025 import (
    contract_sources,source_metadata_gate,taxonomy_source_only_summary
)
from scripts.movebank_solar_movement_20261019 import analyze_file

PINNED_SOURCE_SHA="f4b884a36dd109b01db04a55ea9a81ccd413d74271febd6e90f1da15b11eda4f"
CONTRACT=HERE/"research/MOVEBANK_THREE_NEW_SAME_TAXON_GPS_EFFECT_V0_20261025.json"
OLD_FIRST=HERE/"research/MOVEBANK_SOLAR_MOVEMENT_V0_RESULT_20261019.json"
OLD_OTHER=HERE/"research/MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_RESULT_20261019.json"

def source_gate(path:Path):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PINNED_SOURCE_SHA:
        raise ValueError("HOLD_ORIGINAL_SOURCE_CALENDAR_RECEIPT_HASH_CHANGED")
    source=json.loads(raw)
    candidates=contract_sources()
    if (source["status"]!="EXTERNAL_SAME_TAXON_MAMMAL_GPS_SOURCE_ONLY_CALENDAR_AUDIT"
        or [r["label"] for r in source["sources"]]!=[r["label"] for r in candidates]
        or [r["source_calendar_feasibility"]["individual_years_ge_10_pairs"] for r in source["sources"]]!=[0,0,235]
        or any(r["status"]!="SOURCE_ONLY_CALENDAR_FEASIBILITY_VERIFIED" for r in source["sources"])):
        raise ValueError("HOLD_ORIGINAL_SOURCE_CALENDAR_SUPPORT_DRIFT")
    return candidates,source["sources"]

def old_cohort_gate():
    contract=json.loads(CONTRACT.read_text())
    if contract["id"]!="MOVEBANK_THREE_FROZEN_SAME_TAXON_NEW_SOURCE_GPS_EFFECT_V0_20261025":
        raise ValueError("HOLD_NEW_SOURCE_RESPONSE_CONTRACT_DRIFT")
    previous={
        r["label"]:r for r in
        json.loads(OLD_FIRST.read_text())["sources"]
        +json.loads(OLD_OTHER.read_text())["sources"]
    }
    result={}
    for candidate in contract["comparisons"]:
        old=previous[candidate["baseline"]]
        n=old.get("n_individuals",old.get("eligible_individuals"))
        if (n!=candidate["initial_n"] or old["taxon"]!=candidate["taxon"]
            or abs(old["relative_effect"]-candidate["initial_delta"])>1e-12):
            raise ValueError("HOLD_PREVIOUS_SAME_SPECIES_SOURCE_RESPONSE_DRIFT")
        result[candidate["label"]]=candidate
    if len(result)!=3:raise ValueError("HOLD_THREE_ORIGINAL_SOURCE_PAIR_MAPPING")
    return result

def source_support_status(gate_row):
    data=gate_row["source_calendar_feasibility"]
    if data["valid_position_time_individual_rows"]==0:
        return "HOLD_ORIGINAL_GPS_LOCATION_OR_TIME_UNPARSEABLE"
    if data["individual_years_ge_10_pairs"]<5:
        return "INSUFFICIENT_SOURCE_BOTH_BRANCH_CALENDAR_OBSERVATIONS"
    return "SOURCE_ONLY_SOLAR_CALENDAR_READY"

def run(prior:Path,outdir:Path):
    candidates,gates=source_gate(prior)
    baselines=old_cohort_gate()
    outdir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for original,screen in zip(candidates,gates):
        baseline=baselines[original["label"]]
        status=source_support_status(screen)
        r={
            "label":original["label"],"taxon":original["taxon"],
            "source_DOI":original["doi"],"source_MD5":original["checksum_md5"],
            "source_preflight_status":status,
            "new_original_file_provider_MD5_verified":
                screen["original_download_integrity"]["provider_checksum_verified"],
            "source_only_calendar_individual_years_ge10":
                screen["source_calendar_feasibility"]["individual_years_ge_10_pairs"],
            "baseline_original_cohort":baseline["baseline"],
            "baseline_eligible_animals":baseline["initial_n"],
            "baseline_relative_movement":baseline["initial_delta"],
            "source_population_independence_verified":False,
            "new_GPS_movement_evaluated":False,
            "status":status
        }
        file=outdir/(original["label"]+"_ORIGINAL_MOVEBANK.csv")
        if status!="SOURCE_ONLY_SOLAR_CALENDAR_READY":
            rows.append(r)
            print("SAME_TAXON_BEHAVIOR_HOLD "+json.dumps(r,sort_keys=True),flush=True)
            continue
        try:
            meta=source_metadata_gate(original,original_files(original["package_uuid"]))
            r["original_file_source"]=checksum_and_download(meta,file)
            replay=inspect_csv(file)
            for key in ("csv_rows","valid_position_time_individual_rows",
                        "individual_years_ge_10_pairs","distinct_individuals_with_valid_fixes"):
                if replay[key]!=screen["source_calendar_feasibility"][key]:
                    raise ValueError("HOLD_PREVIOUS_SOURCE_ONLY_GPS_SCHEMA_OR_CALENDAR_DRIFT_"+key)
            tax=taxonomy_source_only_summary(file,original["taxon"])
            if tax.get("off_target_taxon_rows",0):
                raise ValueError("HOLD_ORIGINAL_SINGLE_SPECIES_SOURCE_RECLASSIFIED")
            effects=analyze_file(file)
            if effects["gps_rows"]!=replay["csv_rows"]:
                raise ValueError("HOLD_NEW_ORIGINAL_GPS_ROW_COUNT_CHANGED")
            qc={
                key:effects.get(key) for key in
                ("gps_rows","source_individuals","adjacent_intervals",
                 "qualified_same_solar_period_steps",
                 "individual_years_with_day_and_night_steps",
                 "individual_years_ge10_matched_days",
                 "individuals_ge10_matched_days_some_year")
            }
            r["new_source_GPS_QC"]=qc
            if effects.get("effect_status")!="exploratory_population_description":
                r["status"]="INSUFFICIENT_ORIGINAL_0P5_TO_2H_GPS_INTERVAL_SUPPORT"
            else:
                e=effects["effect"]
                r.update(
                    status="NEW_SAME_TAXON_ORIGINAL_GPS_SOURCE_EFFECT_EXPLORATORY",
                    new_GPS_movement_evaluated=True,
                    new_qualified_individual_animals=e["n_individuals"],
                    new_animal_effect_sign_positive=e["n_positive"],
                    new_animal_effect_sign_negative=e["n_negative"],
                    new_relative_NIGHT_minus_DAY_delta_log1p_kmh=
                        e["mean_falling_minus_rising_log1p_night_over_day_kmh"],
                    new_DAY_delta_log1p_kmh=e["mean_falling_minus_rising_day_log1p_kmh"],
                    new_NIGHT_delta_log1p_kmh=e["mean_falling_minus_rising_night_log1p_kmh"],
                    source_individual_bootstrap_95_percentile_NOT_species_CI=
                        e["individual_cluster_bootstrap_95_percentile"]
                )
                if abs(r["new_relative_NIGHT_minus_DAY_delta_log1p_kmh"]-
                       (r["new_NIGHT_delta_log1p_kmh"]-r["new_DAY_delta_log1p_kmh"]))>1e-10:
                    raise ValueError("HOLD_NEW_SOURCE_RELATIVE_DAY_NIGHT_IDENTITY")
                r["same_sign_as_previous_taxon_source"]=(
                    r["new_relative_NIGHT_minus_DAY_delta_log1p_kmh"]*baseline["initial_delta"]>0)
        except Exception as exc:
            r.update(status="HOLD_ORIGINAL_NUMERIC_GPS_SOURCE_FAILED",
                     error_type=type(exc).__name__,reason=str(exc)[:230],
                     new_GPS_movement_evaluated=False)
            for key in list(r):
                if key.startswith("new_") and key not in ("new_source_GPS_QC",
                   "new_original_file_provider_MD5_verified","new_GPS_movement_evaluated"):
                    r.pop(key,None)
            r.pop("same_sign_as_previous_taxon_source",None)
        finally:
            file.unlink(missing_ok=True)
        rows.append(r)
        print("SAME_TAXON_BEHAVIOR_RESULT "+json.dumps(r,sort_keys=True),flush=True)
    result={
        "status":"THREE_SAME_TAXON_SOURCES_ALL_DISPOSITIONS",
        "source_only_original_SHA256":PINNED_SOURCE_SHA,
        "source_only_original_run":40159378985,
        "sources":rows,
        "new_GPS_source_admitted_count":sum(x["status"]=="NEW_SAME_TAXON_ORIGINAL_GPS_SOURCE_EFFECT_EXPLORATORY" for x in rows),
        "source_or_sampling_HOLD_count":sum(x["status"]!="NEW_SAME_TAXON_ORIGINAL_GPS_SOURCE_EFFECT_EXPLORATORY" for x in rows),
        "no_new_animal_lat_lon_ID_timestamp_exported":True,
        "no_physiology_or_cross_region_causal_inference":True
    }
    (outdir/"three_same_taxon_new_GPS_effect_or_hold_20261025.json").write_text(
        json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("THREE_SAME_TAXON_SOURCE_OUTCOME_FINAL "+json.dumps({
        "admitted":result["new_GPS_source_admitted_count"],
        "holds":result["source_or_sampling_HOLD_count"],
        "results":[{"label":x["label"],"status":x["status"],
                    "original_n":x["baseline_eligible_animals"],
                    "new_n":x.get("new_qualified_individual_animals"),
                    "original_effect":x["baseline_relative_movement"],
                    "new_effect":x.get("new_relative_NIGHT_minus_DAY_delta_log1p_kmh")}
                    for x in rows]
    },sort_keys=True))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-source-only-receipt",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    result=run(a.original_source_only_receipt,a.output_dir)
    if result["new_GPS_source_admitted_count"]==0:
        raise SystemExit(2)

if __name__=="__main__":
    main()
