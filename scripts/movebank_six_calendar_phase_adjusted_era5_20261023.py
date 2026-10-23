#!/usr/bin/env python3
"""Fixed post-outcome phase-distance adjustment for six original GPS/ERA5 cohorts.

Before any new result: replays exact ORIGINAL GPS source UUID/MD5, original
animal roster, pairs, relative and DAY/NIGHT algebra, original canonical ERA5
dated SHA256, old regional T and water means, and old 6 source thermal and
water slopes. ONE linear k distance-from-June21 adjustment only. No animal
IDs, precise GPS locations, raw event dates or individual effects exported.

This is a calendar co-trend diagnostic, never a temperature-causal model.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import statistics

from scripts.movebank_native_ecology_20261019 import (
    HERE, original_files, checksum_and_download
)
from scripts.movebank_regional_climate_link_20261019 import (
    locked_pairs, weather_rolling_30
)
from scripts.movebank_six_source_within_animal_era5_date_slopes_20261019 import (
    original_cohort_source_configuration, original_effect_guard, centered_slope,
)
from scripts.movebank_six_gps_thermal_day_night_component_20261022 import (
    LABELS, paired_source_day_night, pair_replay,
    archived_daily_weather, previous_regional_climate_guard,
    individual_nested_component_summary, summarize_original_animals,
    year_slopes
)

CONTRACT=HERE/"research/MOVEBANK_SIX_PHASE_ADJUSTED_GPS_ERA5_V0_20261023.json"
ORIGINAL=HERE/"research/MOVEBANK_SIX_THERMAL_DAY_NIGHT_COMPONENT_V0_20261022.json"
ORIGINAL_WEATHER_SHA="8b637760b9199e6e7f9f85e647b74658827525ed42d400bc06d44c6a4a14f05e"
PREDICTORS=("temp_C","water_per_100mm")
RESPONSES=("relative","day","night")
MIN_PAIRS=10
MIN_PHASE_SD=7.0
MIN_RESID_X_SD={"temp_C":.5,"water_per_100mm":.1}
MIN_DISTINCT_K=3
SLOPE_TOL=1e-9


def seasonal_distance_from_june_solstice(rising:date,falling:date)->float:
    if rising.year!=falling.year:
        raise ValueError("HOLD_ORIGINAL_NORTHERN_PAIR_STRADDLES_CALENDAR_YEARS")
    pivot=date(rising.year,6,21)
    if not rising<pivot<falling:
        raise ValueError("HOLD_ORIGINAL_PAIR_NOT_JUNE_SOLSTICE_STRADDLING")
    return ((pivot-rising).days+(falling-pivot).days)/2


def calendar_adjusted_ols(k:list[float], x:list[float], y:list[float],
                          kind:str) -> dict:
    """FWL residualize x AND y on intercept+linear original solstice distance.

    Null support never causes a regression with invented zeros. This is not
    thermal mediation or a population-level sampling-uncertainty estimate.
    """
    if kind not in PREDICTORS:
        raise ValueError("HOLD_UNREGISTERED_GPS_CLIMATE_COVARIATE")
    if len(k)!=len(x) or len(x)!=len(y) or len(k)<MIN_PAIRS:
        return {"status":"INSUFFICIENT_CALENDAR_PAIRS","beta":None}
    if any(not math.isfinite(float(t)) for t in [*k,*x,*y]):
        raise ValueError("HOLD_NONFINITE_ERA5_OR_GPS_PHASE_DATA")
    if len(set(k))<MIN_DISTINCT_K or statistics.pstdev(k)<MIN_PHASE_SD:
        return {"status":"INSUFFICIENT_PHASE_VARIATION","beta":None}
    km=statistics.mean(k)
    xc=[v-statistics.mean(x) for v in x]
    yc=[v-statistics.mean(y) for v in y]
    kc=[v-km for v in k]
    den=sum(v*v for v in kc)
    bx=sum(a*b for a,b in zip(xc,kc))/den
    by=sum(a*b for a,b in zip(yc,kc))/den
    xr=[a-bx*b for a,b in zip(xc,kc)]
    yr=[a-by*b for a,b in zip(yc,kc)]
    residual_sd=statistics.pstdev(xr)
    if residual_sd<=MIN_RESID_X_SD[kind]:
        return {"status":"CLIMATE_RESIDUAL_NEAR_COLLINEAR_WITH_SOLAR_PHASE",
                "beta":None,"residual_x_sd":residual_sd}
    xx=sum(a*a for a in xr)
    beta=sum(a*b for a,b in zip(xr,yr))/xx
    before=sum(v*v for v in xc)
    phase_r2=1.0-xx/before if before else None
    return {"status":"ELIGIBLE_PHASE_CONTROL","beta":beta,
            "climate_phase_R2":max(0.,min(1.,phase_r2)) if phase_r2 is not None else None,
            "residual_x_sd":residual_sd,"phase_sd_days":statistics.pstdev(k),
            "original_pairs":len(k)}


def calendar_phase_year(year:list,weather:dict) -> dict:
    if len(year)<MIN_PAIRS:
        return {"status":"INSUFFICIENT_ORIGINAL_SOLAR_MATCHES"}
    rows=[]
    for rising,falling,relative,day,night in year:
        k=seasonal_distance_from_june_solstice(rising,falling)
        a=weather_rolling_30(weather,rising)
        b=weather_rolling_30(weather,falling)
        if a is None or b is None:
            return {"status":"HOLD_MISSING_ORIGINAL_CLIMATE_DAY"}
        dT=b[0]-a[0]
        dW=(b[1]-a[1])/100.0
        if any(not math.isfinite(float(v)) for v in (dT,dW,relative,day,night)):
            raise ValueError("HOLD_NONFINITE_CLIMATE_OR_ORIGINAL_GPS")
        if abs((night-day)-relative)>1e-12:
            raise ValueError("HOLD_ORIGINAL_NIGHT_MINUS_DAY_PAIR_IDENTITY")
        rows.append((k,dT,dW,relative,day,night))
    ks=[r[0] for r in rows]
    result={"status":"ORIGINAL_CALENDAR_PAIR_SUPPORT",
            "original_pair_count":len(rows)}
    for kind in PREDICTORS:
        index=1 if kind=="temp_C" else 2
        x=[r[index] for r in rows]
        adjusted={part:calendar_adjusted_ols(
            ks,x,[r[{"relative":3,"day":4,"night":5}[part]] for r in rows],kind
        ) for part in RESPONSES}
        statuses={v["status"] for v in adjusted.values()}
        if len(statuses)!=1:
            raise ValueError("HOLD_PHASE_ADJUSTMENT_RESPONSE_SUPPORT_NOT_IDENTICAL")
        raw=year_slopes(year,weather)[kind]
        prior_full=raw["relative"]
        new_full=adjusted["relative"]["beta"]
        if new_full is not None:
            if abs(new_full-(adjusted["night"]["beta"]-adjusted["day"]["beta"]))>1e-12:
                raise ValueError("HOLD_SOLAR_PHASE_ADJUSTED_COMPONENT_IDENTITY")
            if prior_full is None:
                raise ValueError("HOLD_PREVIOUS_UNADJUSTED_SLOPE_UNDEFINED")
        result[kind]={
            "status":adjusted["relative"]["status"],
            "beta_phase_adjusted":{p:adjusted[p]["beta"] for p in RESPONSES},
            "beta_same_dates_unadjusted":raw,
            "calendar_phase_explained_x_R2":
                adjusted["relative"].get("climate_phase_R2"),
            "x_residual_sd_after_k":adjusted["relative"].get("residual_x_sd"),
            "calendar_distance_sd_days":
                adjusted["relative"].get("phase_sd_days"),
        }
    return result


def nested_calendar_phase_effects(animal_years:list,weather:dict) -> dict:
    by_kind={
        kind:{section:{part:[] for part in RESPONSES}
              for section in ("phase","old_matched")}
        for kind in PREDICTORS
    }
    climate_explained={kind:[] for kind in PREDICTORS}
    calendar_sd={kind:[] for kind in PREDICTORS}
    status_counts={kind:Counter() for kind in PREDICTORS}
    year_counts={kind:0 for kind in PREDICTORS}
    for animal in animal_years:
        nested={
            kind:{section:defaultdict(list) for section in ("phase","old_matched")}
            for kind in PREDICTORS
        }
        nested_r2=defaultdict(list)
        nested_k=defaultdict(list)
        for year in animal:
            output=calendar_phase_year(year,weather)
            if output["status"]!="ORIGINAL_CALENDAR_PAIR_SUPPORT":
                for kind in PREDICTORS:
                    status_counts[kind][output["status"]]+=1
                continue
            for kind in PREDICTORS:
                vals=output[kind]
                status_counts[kind][vals["status"]]+=1
                if vals["status"]!="ELIGIBLE_PHASE_CONTROL":
                    continue
                year_counts[kind]+=1
                for part in RESPONSES:
                    nested[kind]["phase"][part].append(vals["beta_phase_adjusted"][part])
                    nested[kind]["old_matched"][part].append(vals["beta_same_dates_unadjusted"][part])
                nested_r2[kind].append(vals["calendar_phase_explained_x_R2"])
                nested_k[kind].append(vals["calendar_distance_sd_days"])
        for kind in PREDICTORS:
            for section in ("phase","old_matched"):
                for part in RESPONSES:
                    values=nested[kind][section][part]
                    by_kind[kind][section][part].append(
                        statistics.mean(values) if values else None
                    )
            climate_explained[kind].append(
                statistics.mean(nested_r2[kind]) if nested_r2[kind] else None
            )
            calendar_sd[kind].append(
                statistics.mean(nested_k[kind]) if nested_k[kind] else None
            )
    result={}
    for kind in PREDICTORS:
        blocks={}
        for section in ("phase","old_matched"):
            blocks[section]={
                part:summarize_original_animals(by_kind[kind][section][part])
                for part in RESPONSES
            }
            a=blocks[section]
            if any(a["relative"]["admitted_animal_slope"]!=a[p]["admitted_animal_slope"]
                   for p in ("day","night")):
                raise ValueError("HOLD_PHASE_ADJUSTED_NIGHT_DAY_ANIMAL_SUPPORT")
            if a["relative"]["mean"] is not None and abs(
                a["relative"]["mean"]-
                (a["night"]["mean"]-a["day"]["mean"]))>1e-11:
                raise ValueError("HOLD_PHASE_ADJUSTED_SOURCE_COMPONENT_IDENTITY")
        result[kind]={
            "status":"DESCRIPTIVE_CALENDAR_DISTANCE_CONTROL",
            "original_animal_count":len(animal_years),
            "calendar_qualified_animal_years":year_counts[kind],
            "calendar_qualification_reasons":dict(status_counts[kind]),
            "same_supported_original_unadjusted_slopes":blocks["old_matched"],
            "new_phase_adjusted_slopes":blocks["phase"],
            "calendar_R2_climate":summarize_original_animals(climate_explained[kind]),
            "solar_distance_sd_days":summarize_original_animals(calendar_sd[kind]),
        }
    return result


def run(archived_weather_file:Path,output_dir:Path)->dict:
    cfg=json.loads(CONTRACT.read_text(encoding="utf-8"))
    original=json.loads(ORIGINAL.read_text(encoding="utf-8"))
    if (cfg["id"]!="MOVEBANK_SIX_CALENDAR_PHASE_CONFOUND_GPS_ERA5_V0_20261023"
        or tuple(cfg["cohorts"])!=LABELS
        or tuple(original["cohorts"])!=LABELS
        or sum(original["original_group_n_animals"].values())!=197):
        raise ValueError("HOLD_ORIGINAL_SIX_COHORT_CONTRACT_CHANGED")
    raw=archived_weather_file.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=ORIGINAL_WEATHER_SHA:
        raise ValueError("HOLD_CANONICAL_ERA5_SOURCE_SNAPSHOT_SHA_CHANGED")
    original_weather=json.loads(raw)
    sources=original_cohort_source_configuration()
    if tuple(sources)!=LABELS:
        raise ValueError("HOLD_ORIGINAL_SOURCE_ORDER_CHANGED")
    output_dir.mkdir(parents=True,exist_ok=True)
    entries=[]
    for label in LABELS:
        source=sources[label]["source"]
        coarse_grid=sources[label]["grid"]
        n=original["original_group_n_animals"][label]
        effect=original["original_group_sampled_relative_movement"][label]
        item={"source":label,"taxon":source["taxon"],"source_DOI":source["doi"],
              "original_n_animals":n,"frozen_old_group_GPS_effect":effect,
              "status":"HOLD_SOURCE_OR_PHASE_CONTROL_NOT_ADMITTED"}
        source_path=output_dir/("original_"+label+".csv")
        try:
            original_files_matching=[
                f for f in original_files(source["package_uuid"])
                if f["bitstream_uuid"]==source["original_csv_bitstream_uuid"]
            ]
            if len(original_files_matching)!=1:
                raise ValueError("HOLD_ORIGINAL_NATIVE_SOURCE_NOT_UNIQUE")
            provider=original_files_matching[0]
            ck=provider.get("checksum") or {}
            if ck.get("checkSumAlgorithm","").upper()!="MD5" or (
                ck.get("value","").lower()!=source["original_csv_md5"].lower()):
                raise ValueError("HOLD_PROVIDER_DECLARED_ORIGINAL_MD5")
            item["original_MD5_file_integrity"]=checksum_and_download(provider,source_path)
            old_years,old_mean,old_counts=locked_pairs(source_path)
            original_effect_guard(old_mean,old_counts,effect,n)
            new_years,rows=paired_source_day_night(source_path)
            pair_replay(old_years,new_years)
            if rows!=old_counts["gps_rows"]:
                raise ValueError("HOLD_ORIGINAL_NATIVE_EVENT_ROW_COUNT_CHANGED")
            weather,receipts=archived_daily_weather(original_weather,label,coarse_grid)
            previous_regional_climate_guard(
                old_years,weather,original["original_group_regional_T_and_water_means"][label],n
            )
            prior_slope=individual_nested_component_summary(
                new_years,weather,{
                    "temp_C":original["original_group_relative_night_OLS_slope"][label],
                    "water_per_100mm":original["original_group_water_slope_per_100mm"][label],
                }
            )
            item["all_prior_original_GPS_calendar_source_dates_and_slopes_replayed"]=True
            item["original_source_calendar_pairs"]=old_counts["included_calendar_pairs"]
            item["original_source_individual_years"]=old_counts["included_individual_years"]
            item["original_canonical_daily_climate_source_receipts"]=receipts
            item["previous_original_unadjusted_associations"]={
                kind:{p:prior_slope[kind][{"relative":"β_relative_NIGHT_minus_DAY",
                                        "day":"β_day_absolute_observed_displacement",
                                        "night":"β_night_absolute_observed_displacement"}[p]]
                      for p in RESPONSES}
                for kind in PREDICTORS
            }
            item["calendar_distance_sensitivity"]=nested_calendar_phase_effects(
                new_years,weather
            )
            item["status"]="EXPLORATORY_POST_OUTCOME_PHASE_DISTANCE_ADJUSTED_GPS_ERA5"
        except Exception as exc:
            item.update(
                status="HOLD_SOURCE_OR_PHASE_CONTROL_NOT_ADMITTED",
                exception_type=type(exc).__name__,
                exception_detail=str(exc)[:200],
                no_new_phase_inference=True
            )
        finally:
            source_path.unlink(missing_ok=True)
        entries.append(item)
        print("MOVE_BANK_SOLAR_DISTANCE_CONTROL "+json.dumps({
            "source":label,"status":item["status"],
            "n_phase":item.get("calendar_distance_sensitivity",{}).get("temp_C",{}).
                get("new_phase_adjusted_slopes",{}).get("relative",{}).
                get("admitted_animal_slope"),
            "beta_phase":item.get("calendar_distance_sensitivity",{}).
                get("temp_C",{}).get("new_phase_adjusted_slopes",{}).
                get("relative",{}).get("mean"),
            "reason":item.get("exception_detail"),
        },sort_keys=True),flush=True)
    result={
        "status":"SIX_ORIGINAL_GPS_MAMMAL_SOLAR_PHASE_DISTANCE_CLIMATE_SENSITIVITY",
        "registered":"2026-10-23",
        "original_six_cohorts":list(LABELS),
        "original_197_animal_roster_unchanged":True,
        "canonical_ERA5_source_snapshot_sha256":digest,
        "cohorts":entries,
        "admitted_cohorts":sum(x["status"].startswith("EXPLORATORY_") for x in entries),
        "source_holds":sum(x["status"].startswith("HOLD_") for x in entries),
        "source_eras_and_climate_calendar_shared_between_tagged_animals":True,
        "causal_temperature_mediation_or_endogenous_hysteresis_proven":False,
        "source_animal_ID_GPS_coordinates_or_original_pair_dates_exported":False,
        "method":"FWL OLS adjusting distance from June solstice within original same-individual same-calendar-year source dates, one predetermined linear k trend; not prospective holdout or causal heat."
    }
    (output_dir/"movebank_six_phase_distance_era5_gps_v0.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archived-era5",required=True,type=Path)
    parser.add_argument("--output-dir",required=True,type=Path)
    a=parser.parse_args()
    result=run(a.archived_era5,a.output_dir)
    print("MOVE_BANK_PHASE_DISTANCE_SIX_SUMMARY "+json.dumps({
        "admitted":result["admitted_cohorts"],"holds":result["source_holds"],
        "cohorts":[{
            "source":item["source"],
            "status":item["status"],
            "n_original":item["original_n_animals"],
            "n_adjusted":item.get("calendar_distance_sensitivity",{}).
               get("temp_C",{}).get("new_phase_adjusted_slopes",{}).
               get("relative",{}).get("admitted_animal_slope"),
            "beta_old":item.get("previous_original_unadjusted_associations",{}).
               get("temp_C",{}).get("relative",{}).get("mean"),
            "beta_phase":item.get("calendar_distance_sensitivity",{}).
               get("temp_C",{}).get("new_phase_adjusted_slopes",{}).
               get("relative",{}).get("mean"),
            "error":item.get("exception_detail"),
        } for item in result["cohorts"]],
        "causal_temperature":False
    },sort_keys=True))
    if result["admitted_cohorts"]==0:
        raise SystemExit(2)


if __name__=="__main__":
    main()
