"""Exact-source solar altitude/fine-solar-clock partial irradiance sensitivity.

Reuses ORIGINAL provider MD5 GPS data and full-year archived ERA5 model.
Prior first 24+24 source radiation coefficients MUST replay numerically from
newly fetched ERA5 before this separate post-result geometry sensitivity is
ever reported. 28 original source studies without prior radiation support
stay explicitly UNIDENTIFIABLE in 48-source report, not source replacement.

No raw GPS coordinates, animal IDs, exact timestamp or weather query source
grid coordinates are released in CI logs or derived outputs.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime
import json
import math
from pathlib import Path
from statistics import mean

from scripts.movebank_native_ecology_20261019 import HERE, original_files, checksum_and_download
from scripts.global_solar_azimuth_12_new_original_events_v1 import load_source_taxa
from scripts.solar_azimuth_macro_v0 import analyze_taxon, directional_step, _bootstrap
from scripts.solar_azimuth_era5_wind_v0 import (
    year_request_parameters,get_original_hourly_response,validate_and_parse_weather
)
from scripts.run_solar_azimuth_24_source_population_weather_v0 import (
    original_directional_grid_years,source_siteyear_environment_response,latitude_band,
    _original_source_replay
)
from scripts.solar_radiation_sun_geometry_fwl_v0 import (
    conditional_shortwave_slope_one_animal
)

CONTRACT=HERE/"research/SOLAR_RADIATION_SOLAR_ALTITUDE_CONDITIONAL_48_SOURCE_V0_CONTRACT.json"
MANIFEST_FIRST=HERE/"research/GLOBAL_SOLAR_AZIMUTH_NEW24_PROVIDER_FROZEN_SOURCE_FILE_MANIFEST_20261025.json"
MANIFEST_SECOND=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_PROVIDER_FROZEN_SOURCE_MANIFEST_20261025.json"
RESULT_FIRST=HERE/"research/SOLAR_AZIMUTH_24_SOURCE_MULTI_POPULATION_ERA5_V0_FIRST_ALL_RESULTS_20261025.json"
RESULT_SECOND=HERE/"research/SOLAR_RADIATION_EXTERNAL_24_SOURCE_FIRST_ALL_RESULTS_20261025.json"

def fixed_original_study_roster():
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["version"]!="original-GPS-irradiance-conditioned-on-solar-altitude-v0":
        raise ValueError("New physical sunlight sensitivity contract changed")
    old_manifest=json.loads(MANIFEST_FIRST.read_text(encoding="utf-8"))
    new_manifest=json.loads(MANIFEST_SECOND.read_text(encoding="utf-8"))
    old_result=json.loads(RESULT_FIRST.read_text(encoding="utf-8"))
    new_result=json.loads(RESULT_SECOND.read_text(encoding="utf-8"))
    man_old={x["package_uuid"]:x for x in old_manifest["source_file_entries"]}
    man_new={x["original_source_package_uuid"]:x for x in new_manifest["all_selected_original_source_entries"]}
    result_old={x["source_package_uuid"]:x for x in old_result["source_groups"]}
    result_new={x["source_package_uuid"]:x for x in new_result["all_external_first_source_results"]}
    selected=contract["selected_existing_study_originals_for_sensitivity"]
    held=contract["existing_nonestimable_study_originals_retained"]
    if len(selected)!=20 or len(held)!=28 or len({x["source_uuid"] for x in selected+held})!=48:
        raise ValueError("Original 48-study radiation support frame incomplete")
    ret=[]
    for row in selected:
        cohort,uuid=row["cohort"],row["source_uuid"]
        src=man_old.get(uuid) if cohort=="earlier" else man_new.get(uuid)
        result=result_old.get(uuid) if cohort=="earlier" else result_new.get(uuid)
        if src is None or result is None:
            raise ValueError("Previously fixed source original file/result missing")
        native=(src["original_species_labels"] if cohort=="earlier" else [src["original_taxon"]])
        if not set(row["native_eligible_taxa"])<=set(native):
            raise ValueError("Original source taxon sensitivity support roster modified")
        ret.append((row,src,result))
    return ret,held


def original_sun_geometry_for_siteyear(source_taxon, selected_keys, baseline):
    """Match astronomical step altitude to same original source event tuple.

    Original source GPS steps in the previous registered source selection
    contain 6 values, without solar elevation. We reproduce each exact step
    without altering the older estimator; append its real sun elevation.
    """
    eligible=set(selected_keys)
    out=defaultdict(list)
    for animal,fixes in source_taxon.items():
        original=sorted(fixes.values())
        for a,b in zip(original,original[1:]):
            step=directional_step(a,b)
            if step is None:
                continue
            middle=a[0]+(b[0]-a[0])/2
            if not 1940<=middle.year<=2025:
                continue
            lat=(a[1]+b[1])/2
            lon=((a[2]+((b[2]-a[2]+180)%360-180)/2+180)%360)-180
            key=(math.floor(lat),math.floor(lon),middle.year)
            if key not in eligible:
                continue
            original_six=(
                animal,middle.replace(minute=0,second=0,microsecond=0),
                step.solar_date,step.solar_hour,step.bearing,step.sun_azimuth
            )
            out[key].append((*original_six,step.sun_elevation))
    for key in eligible:
        a=out.get(key,[])
        b=baseline[key]["steps"]
        if len(a)!=len(b) or any(x[:6]!=y for x,y in zip(a,b)):
            raise ValueError("Original sun elevation cannot attach to previous identical GPS step roster")
    return out


def replay_original_full_source_GPS(cohort,source,previous,tracks,coverage):
    if cohort=="earlier":
        original=_original_source_replay(tracks,coverage,previous)
        return original
    native=source["original_taxon"]
    recorded=previous["source_original_GPS_first_directional_result"]
    if recorded is None:
        raise ValueError("New source original GPS reference unexpectedly absent")
    now=analyze_taxon({a:list(v.values()) for a,v in tracks[native].items()})
    if now["status"]!=recorded["status"]:
        raise ValueError("Unseen source GPS behavioral status did not replay")
    if now["supported_individuals"]!=recorded["supported_individuals"]:
        raise ValueError("Original source qualified tagged animal N changed")
    if now["daylight_directional_qualified_steps"]!=recorded["daylight_directional_qualified_steps"]:
        raise ValueError("Original source qualified daytime step count changed")
    if now["status"]=="descriptive_source_estimated":
        for k in ("raw_toward_sun_mean_cos","clock_adjusted_excess_cos","compass_independence_excess_cos"):
            a=now["results"][k]["mean"]
            b=recorded["results"][k]["mean"]
            if (a is None)!=(b is None) or (a is not None and abs(a-b)>1e-12):
                raise ValueError("Original new source GPS solar angle mean did not replay")
    return {"original_GPS_taxa_replayed":1,
            "original_effect_full_replay_verified":True}


def weather_source_one_gridyear(key):
    params=year_request_parameters(*key)
    raw=get_original_hourly_response(params)
    return validate_and_parse_weather(raw,key[2])


def evaluate_selected_source(item,src,reference,out):
    cohort,uuid=item["cohort"],item["source_uuid"]
    native=(src["original_species_labels"] if cohort=="earlier" else [src["original_taxon"]])
    original=src["original_file"]
    if cohort=="earlier":
        digest=original["checksum"]
        filename=original["filename"]
    else:
        digest=original["provider_checksum"]
        filename=original["original_file_name"]
    result={
        "source_package_uuid":uuid,
        "cohort":cohort,
        "original_study_ids":item["study_id"],
        "original_native_taxa":native,
        "original_taxa_with_prior_identifiable_irradiance":item["native_eligible_taxa"],
        "source_status":"SOURCE_HOLD",
        "original_provider_MD5_verified":False,
        "all_native_original_GPS_effects_replayed_before_ERA5":False,
        "siteyear_contexts":[],
        "original_ERA5_source_query_count":0,
        "source_weather_body_digest_receipts_without_coordinates":[],
        "animal_track_positions_exported":False
    }
    private=out/("private_GPS_original_"+uuid+".csv")
    try:
        f=[x for x in original_files(uuid) if x["bitstream_uuid"]==original["bitstream_uuid"]]
        if len(f)!=1 or f[0]["checksum"]!=digest or f[0]["bytes"]!=original["bytes"]:
            raise ValueError("Original Movebank provider file bitstream checksum/size changed")
        receipt=checksum_and_download(f[0],private)
        result["original_provider_MD5_verified"]=bool(receipt.get("provider_checksum_verified"))
        if not result["original_provider_MD5_verified"]:
            raise ValueError("Provider original file checksum not verified")
        tracks,coverage,rawmeta=load_source_taxa(private,filename,native)
        result["original_native_source_rows"]=rawmeta["original_total_rows"]
        replay_original_full_source_GPS(cohort,src,reference,tracks,coverage)
        result["all_native_original_GPS_effects_replayed_before_ERA5"]=True

        old_by_taxon={t["taxon"]:t for t in reference["source_taxa"]}
        planned=[]
        for taxon in native:
            if taxon not in item["native_eligible_taxa"]:
                continue
            fixed_taxon=old_by_taxon[taxon]
            selected,selection=original_directional_grid_years(tracks[taxon])
            original_context=fixed_taxon["source_gridyear_weather_contexts"]
            if len(selected)!=len(original_context):
                raise ValueError("Original source siteyear selection changed")
            lookup={key:body for key,body in selected}
            targets={}
            for index,((key,rec),prior) in enumerate(zip(selected,original_context),1):
                if prior["source_taxon_modal_original_gridyear_rank"]!=index:
                    raise ValueError("Original GPS grid-year order changed")
                if (prior["original_gridyear_source_n_tagged_animals"]!=len(rec["animal_ids"]) or
                    prior["original_gridyear_source_n_steps"]!=len(rec["steps"]) or
                    prior["original_gridyear_source_n_solar_dates"]!=len(rec["dates"]) or
                    prior["original_UTC_observation_year"]!=key[2]):
                    raise ValueError("Original selected GPS grid-year support changed")
                if (prior.get("within_animal_clock_month_weather_associations") is None or
                    prior["within_animal_clock_month_weather_associations"]["shortwave_Wm2"]["mean"] is None):
                    continue
                targets[key]=prior
            geometry=original_sun_geometry_for_siteyear(tracks[taxon],targets,lookup)
            for key,old in targets.items():
                planned.append((taxon,key,lookup[key],old,geometry[key]))
        weatherkeys=sorted({key for _,key,_,_,_ in planned})
        if not weatherkeys or len(weatherkeys)>8:
            raise ValueError("Original supported environmental site-years invalid/cap exceeded")
        weather={}
        for key in weatherkeys:
            try:
                parsed,receipt=weather_source_one_gridyear(key)
                weather[key]=parsed
                result["source_weather_body_digest_receipts_without_coordinates"].append(
                    {"request_sequence_number":
                     len(result["source_weather_body_digest_receipts_without_coordinates"])+1,
                     **receipt})
            except Exception as exc:
                weather[key]=None
                result["source_weather_body_digest_receipts_without_coordinates"].append(
                    {"request_sequence_number":
                     len(result["source_weather_body_digest_receipts_without_coordinates"])+1,
                     "source_status":"SOURCE_WEATHER_HOLD",
                     "error_type":type(exc).__name__})
        result["original_ERA5_source_query_count"]=len(weatherkeys)
        for taxon,key,original,old,extended in planned:
            context={
                "taxon":taxon,
                "original_source_taxon_siteyear_rank":old["source_taxon_modal_original_gridyear_rank"],
                "original_source_year":old["original_UTC_observation_year"],
                "source_coarse_latitude_band":latitude_band(key[0]),
                "source_previous_irradiance_slope_per_100Wm2":
                    old["within_animal_clock_month_weather_associations"]["shortwave_Wm2"]["mean"],
                "source_status":"SOURCE_WEATHER_HOLD",
                "geometric_solar_adjustment_effect":None,
                "source_tagged_animal_IDs_exported":False
            }
            w=weather.get(key)
            if w is None:
                context["reason"]="Provider ERA5 previous source year unavailable"
                result["siteyear_contexts"].append(context)
                continue
            try:
                ref=source_siteyear_environment_response(key,original["steps"],w)
                old_association=old["within_animal_clock_month_weather_associations"]["shortwave_Wm2"]
                new_assoc=(ref.get("within_animal_clock_month_weather_associations") or {}).get("shortwave_Wm2") or {}
                if ref["weather_environmental_effect_status"]!="SOURCE_GROUP_OBSERVED_ENVIRONMENT_DESCRIPTION":
                    raise ValueError("Prior weather-qualified original group now unavailable")
                if (new_assoc.get("mean") is None or
                        abs(new_assoc["mean"]-old_association["mean"])>1e-10 or
                        new_assoc["original_tagged_animals"]!=old_association["original_tagged_animals"] or
                        ref["weather_matched_same_original_GPS_steps"]!=old["weather_matched_same_original_GPS_steps"]):
                    raise ValueError("Prior source hourly ERA5 response did not reproduce")
                # Reproduce original within-individual month×4h radiation
                # marginal on the exact original GPS-weather subpopulation.
                animal_obs=defaultdict(list)
                for animal,utc,solar_day,hour,bearing,az,elevation in extended:
                    meteo=w.get(utc)
                    if meteo is None:
                        continue
                    animal_obs[animal].append((
                        utc,solar_day,hour,bearing,az,elevation,meteo[2]
                    ))
                individual=[conditional_shortwave_slope_one_animal(obs)
                            for obs in animal_obs.values()]
                originals=[x["unadjusted_same_step_slope"] for x in individual
                           if x["unadjusted_same_step_slope"] is not None]
                if (len(originals)!=old_association["original_tagged_animals"] or
                        abs(mean(originals)-old_association["mean"])>1e-10):
                    raise ValueError("Original shortwave pre-solar-altitude same-step slope did not replay")
                adjusted=[x for x in individual if
                          x["status"]=="GEOMETRY_ADJUSTED_SOURCE_ANIMAL_ESTIMABLE"]
                valid=[x["solar_geometry_conditional_slope"] for x in adjusted]
                context.update({
                    "source_status":("GEOMETRY_ADJUSTED_GROUP_OBSERVED"
                                     if len(valid)>=5 else
                                     "SUN_GEOMETRY_SOURCE_ANIMAL_SUPPORT_HOLD"),
                    "original_animal_shortwave_slope_replayed":True,
                    "source_radiation_animal_n_before_geometry":
                        len(originals),
                    "source_animal_n_after_geometry":len(valid),
                    "original_GPS_daylight_moving_steps_weather_qualified":len(extended),
                    "geometry_residual_shortwave_mean_sd_Wm2":
                        mean(x["residual_shortwave_SD_Wm2"] for x in adjusted) if adjusted else None,
                    "geometry_residual_shortwave_fraction_variation":
                        mean(x["fraction_shortwave_variance_after_solar_geometry"] for x in adjusted) if adjusted else None,
                    "source_animal_geometry_HOLD_reason_counts":
                        {status:sum(x["status"]==status for x in individual)
                         for status in sorted({x["status"] for x in individual})
                         if status!="GEOMETRY_ADJUSTED_SOURCE_ANIMAL_ESTIMABLE"},
                    "geometric_solar_adjustment_effect":{
                        "mean_slope_per100_Wm2":mean(valid) if len(valid)>=5 else None,
                        "source_original_tagged_animal_bootstrap95":_bootstrap(valid) if len(valid)>=5 else None,
                        "source_animal_n":len(valid),
                        "description":"Original GPS movement relative to source solar azimuth, residualized on sin(actual solar elevation) and within 4h apparent solar-clock before source shortwave; exploratory."
                    }
                })
            except Exception as exc:
                context.update(
                    source_status="SOURCE_WEATHER_REPLAY_HOLD",
                    weather_original_replay_failure_type=type(exc).__name__,
                    geometric_solar_adjustment_effect=None)
            result["siteyear_contexts"].append(context)
        result["source_status"]="GPS_REPLAYED_ALL_SELECTED_ORIGINAL_WEATHER_CONTEXTS_SCREENED"
    except Exception as exc:
        result["source_status"]="SOURCE_HOLD"
        result["failure_type"]=type(exc).__name__
        result["failure_stage"]="original_GPS_provider_or_prior_solar_effect_replay_or_source_context_selection"
        result["siteyear_contexts"]=[]
    finally:
        private.unlink(missing_ok=True)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--shard",type=int,choices=range(5),required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    selected,held=fixed_original_study_roster()
    records=[]
    for i,(item,src,reference) in enumerate(selected):
        if i%5!=args.shard:
            continue
        result=evaluate_selected_source(item,src,reference,args.out)
        records.append(result)
        print("SOLAR_ALTITUDE_IRRADIANCE_FIRST_SOURCE "+
              json.dumps(result,ensure_ascii=False,sort_keys=True),flush=True)
    if len(records)!=4:
        raise ValueError("Every original GPS source shard must contain four identified studies")
    siteyears=[c for r in records for c in r["siteyear_contexts"]]
    report={
        "version":"original-GPS-irradiance-conditioned-on-solar-altitude-v0",
        "source_shard":args.shard,
        "frozen_total_original_source_study_denominator":48,
        "prior_identifiable_original_source_studies_to_attempt":20,
        "prior_unidentifiable_original_source_studies_retained":28,
        "assigned_original_studies":4,
        "source_provider_MD5_verified":sum(r["original_provider_MD5_verified"] for r in records),
        "all_original_GPS_source_effects_replayed_before_new_weather":sum(
            r["all_native_original_GPS_effects_replayed_before_ERA5"] for r in records),
        "attempted_source_taxon_siteyears":len(siteyears),
        "prior_radiation_shortwave_slope_replayed_source_siteyears":sum(
            c.get("original_animal_shortwave_slope_replayed",False) for c in siteyears),
        "geometry_adjusted_siteyear_groups":sum(
            c["source_status"]=="GEOMETRY_ADJUSTED_GROUP_OBSERVED" for c in siteyears),
        "source_weather_replay_HOLD_siteyear_groups":sum(
            c["source_status"]=="SOURCE_WEATHER_REPLAY_HOLD" for c in siteyears),
        "all_source_results":records,
        "interpretation_ceiling":"Post-result original-source astronomical solar elevation and residual clock sensitivity. Does not establish sun/heat/wind causality; no GPS individual traces or original source site coordinates emitted."
    }
    (args.out/("sun_altitude_original_source_shard_"+str(args.shard)+".json")).write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("SOLAR_ALTITUDE_IRRADIANCE_SHARD_SUMMARY "+
          json.dumps({k:v for k,v in report.items() if k!="all_source_results"},
                     ensure_ascii=False,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
