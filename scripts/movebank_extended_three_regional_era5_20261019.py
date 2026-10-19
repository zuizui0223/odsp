#!/usr/bin/env python3
"""Source-pinned matched-date regional ERA5 context for three additional
Movebank populations already qualifying under the original frozen GPS v0 rule.

Exploratory POST the movement outcomes; temperature/water values must never
be used to reselect animals, GPS dates, source files, or estimators. Preserve
and rereproduce old GPS group result BEFORE weather response is opened.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from scripts.movebank_native_ecology_20261019 import HERE, original_files, checksum_and_download
from scripts.movebank_regional_climate_link_20261019 import (
    locked_pairs, read_weather, link_weather, fixed_timezone, weather_rolling_30
)

BASE=HERE/"research"
CONTRACT=BASE/"MOVEBANK_EXTENSION_THREE_ERA5_DATE_CONTEXT_V0_20261019.json"
SOURCES=BASE/"MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_20261019.json"
ORIGINAL_OUTCOME=BASE/"MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_RESULT_20261019.json"
LABELS=("mule_deer_wyoming","white_tail_virginia","wolves_alberta")


def admission(source:dict, frozen:dict, prior:dict, provider_bitstream:dict)->dict:
    """A strict source gate, independent of any newly retrieved weather."""
    if source["label"] not in LABELS or frozen.get("doi")!=source["doi"]:
        raise ValueError("HOLD_FROZEN_THREE_EXTENSION_COHORT_CHANGED")
    if (source["taxon"] != prior["taxon"]
        or source["doi"] != prior["doi"]
        or prior["status"] != "exploratory_population_description"):
        raise ValueError("HOLD_PREVIOUS_GROUP_EFFECT_NOT_SUPPORTED")
    if (prior["eligible_individuals"]!=frozen["individuals"]
        or abs(prior["relative_effect"]-frozen["relative_log_speed"])>1e-12
        or abs(prior["day_component"]-frozen["day_component"])>1e-12
        or abs(prior["night_component"]-frozen["night_component"])>1e-12):
        raise ValueError("HOLD_PRIOR_MOVEMENT_OUTCOME_DRIFT")
    if (source["original_csv_bitstream_uuid"]!=provider_bitstream.get("bitstream_uuid")
        or frozen["source_md5"]!=source["original_csv_md5"]):
        raise ValueError("HOLD_SOURCE_BITSTREAM_ID_CHANGED")
    checksum=provider_bitstream.get("checksum") or {}
    if (checksum.get("checkSumAlgorithm","").upper()!="MD5"
        or checksum.get("value","").lower()!=frozen["source_md5"].lower()):
        raise ValueError("HOLD_ORIGINAL_PROVIDER_MD5_CHANGED")
    return {"original_source_md5_checked":True,"original_effect_metadata_checked":True}


def strict_movement_replication(main, counts, frozen):
    if main is None or abs(main-frozen["relative_log_speed"])>1e-10:
        raise ValueError("HOLD_ORIGINAL_GPS_EFFECT_RECOMPUTATION_MISMATCH")
    if counts["source_individuals"]!=frozen["individuals"]:
        raise ValueError("HOLD_ORIGINAL_INDIVIDUAL_SOURCE_COHORT_MISMATCH")
    if counts["included_calendar_pairs"]<=0:
        raise ValueError("HOLD_ORIGINAL_MATCHED_DATE_PAIRS_MISSING")
    return True


def summary_for_source(rec, pairs, source_mean, counts, site, weather, receipts):
    result={**rec, **counts,
        "status":"EXPLORATORY_ORIGINAL_SOURCE_MATCHED_ERA5_CONTEXT",
        "original_frozen_GPS_night_day_effect_reproduced":True,
        "original_source_mean_night_minus_day_falling_minus_rising":source_mean,
        "coarse_regional_reference_site":site["description"],
        "reference_grid_coordinates_public_and_coarse":[site["latitude"],site["longitude"]],
        "regional_climate_daily_source_receipts":receipts,
        "regional_climate_ERA5_timezone":fixed_timezone(site["longitude"]),
    }
    result.update(link_weather(pairs,weather))
    if result["status"]!="descriptive_coarse_region_weather_link":
        result["status"]="HOLD_NO_QUALIFIED_WEATHER_DATE_JOIN"
    else:
        result["status"]="EXPLORATORY_ORIGINAL_SOURCE_MATCHED_ERA5_CONTEXT"
    return result


def run(output_dir:Path)->dict:
    cfg=json.loads(CONTRACT.read_text(encoding="utf-8"))
    roster=json.loads(SOURCES.read_text(encoding="utf-8"))
    previous=json.loads(ORIGINAL_OUTCOME.read_text(encoding="utf-8"))
    if (cfg.get("id")!="MOVEBANK_GPS_THREE_EXTENDED_ERA5_MATCHED_DATE_V0_20261019"
        or roster.get("version")!="independent-published-source-extension-v0"
        or len(roster["sources"])!=8 or len(LABELS)!=3):
        raise ValueError("HOLD_PRIOR_PUBLIC_DATABASE_COHORT_NOT_FROZEN")
    source_index={p["label"]:p for p in roster["sources"]}
    prior_index={p["label"]:p for p in previous["sources"]}
    if len(source_index)!=8 or len(prior_index)!=8:
        raise ValueError("HOLD_FROZEN_EIGHT_SOURCE_ROSTER_UNIQUE_KEYS")
    output_dir.mkdir(parents=True,exist_ok=True)
    all_results=[]
    for label in LABELS:
        source=source_index[label]
        old=prior_index[label]
        expected=cfg["frozen_expected_results"][label]
        site=cfg["geographic_exposure"][label]
        rec={
            "label":label,
            "taxon":source["taxon"],
            "source_DOI":source["doi"],
            "source_GPS_mean_before_climate":expected["relative_log_speed"],
            "prior_source_n_individuals":expected["individuals"],
            "status":"HOLD_ORIGINAL_SOURCE_OR_ERA5_NOT_ADMITTED",
            "weather_biological_causality_estimated":False,
            "camera_data_or_sensor_q_mixed_into_GPS":False,
        }
        path=output_dir/(label+"_ORIGINAL_TEMPO.csv")
        try:
            fs=[x for x in original_files(source["package_uuid"])
                if x["bitstream_uuid"]==source["original_csv_bitstream_uuid"]]
            if len(fs)!=1:raise ValueError("HOLD_ORIGINAL_SOURCE_BITSTREAM_NOT_UNIQUE")
            rec.update(admission(source,expected,old,fs[0]))
            rec["source_integrity"]=checksum_and_download(fs[0],path)
            pairs,actual,counts=locked_pairs(path)
            strict_movement_replication(actual,counts,expected)
            # No climate is opened unless the original frozen GPS result has
            # been exactly reproduced on original checksum-validated bytes.
            dates=[d for animal in pairs for year in animal
                   for rising,falling,_ in year for d in (rising,falling)]
            if not dates:raise ValueError("HOLD_MATCHED_SOURCE_DATES_NOT_FOUND")
            weather,receipts=read_weather(site,min(dates),max(dates))
            rec=summary_for_source(rec,pairs,actual,counts,site,weather,receipts)
            if rec["status"]=="EXPLORATORY_ORIGINAL_SOURCE_MATCHED_ERA5_CONTEXT":
                if rec["individuals_with_complete_weather_and_displacement"]>counts["source_individuals"]:
                    raise ValueError("HOLD_WEATHER_REPLICATE_EXCEEDS_GPS_ANIMALS")
                if rec["missing_weather_date_pairs"]<0:
                    raise ValueError("HOLD_NEGATIVE_MISSINGNESS")
        except Exception as exc:
            rec.update(status="HOLD_ORIGINAL_SOURCE_OR_ERA5_NOT_ADMITTED",
                       error_type=type(exc).__name__,
                       error_message=str(exc)[:230],
                       environment_animal_result_claimed=False)
        finally:
            path.unlink(missing_ok=True)
        all_results.append(rec)
        print("EXTENDED_MOVEBANK_ERA5_MAMMAL",json.dumps(rec,sort_keys=True),flush=True)
    outcome={
        "status":"THREE_ADDITIONAL_ORIGINAL_SOURCE_REGIONAL_ERA5_GPS_CONTEXT",
        "epistemic_status":"Post-original-GPS-outcome exploratory regional climate context, not causal mammal thermal response or global meta-analysis",
        "original_eight_source_extension_reclassified":False,
        "source_files_requested":list(LABELS),
        "sources":all_results,
        "accepted_sources":sum(r["status"]=="EXPLORATORY_ORIGINAL_SOURCE_MATCHED_ERA5_CONTEXT" for r in all_results),
        "source_hold":sum(r["status"].startswith("HOLD_") for r in all_results),
        "original_three_source_ERA5_effects_reused_without_recalculation":True,
        "no_animal_GPS_location_ID_or_event_datetime_exported":True,
        "no_animal_latent_activity_or_causal_mechanism_identified":True,
        "not_six_independent_species_wide_effects":True,
    }
    (output_dir/"extension_three_mammal_matched_date_regional_era5.json").write_text(
        json.dumps(outcome,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return outcome


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    result=run(args.output_dir)
    print("MOVEBANK_THREE_MORE_ERA5_SUMMARY "+json.dumps({
        "accepted_sources":result["accepted_sources"],
        "source_hold":result["source_hold"],
        "sources":[{
            "label":r["label"],
            "status":r["status"],
            "eligible":r.get("individuals_with_complete_weather_and_displacement"),
            "temperature_delta":r.get("mean_falling_minus_rising_regional_temperature_c"),
            "p_minus_et0_delta":r.get("mean_falling_minus_rising_regional_p_minus_et0_30d_mm"),
            "GPS_effect":r.get("mean_observed_falling_minus_rising_relative_log1p_night_day_speed"),
        } for r in result["sources"]],
        "causal_inference":False
    },sort_keys=True))
    if result["accepted_sources"]==0:raise SystemExit(2)


if __name__=="__main__":
    main()
