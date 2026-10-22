#!/usr/bin/env python3
"""Six original Movebank GPS cohorts: thermal DAY vs NIGHT displacement slopes.

Post-outcome ecological description, frozen by
research/MOVEBANK_SIX_THERMAL_DAY_NIGHT_COMPONENT_V0_20261022.json.
Reconstruct original SAME GPS source date pairs and source mean BEFORE
joining separately archived source-verified ERA5 day arrays. No animal
identifier, track, precise location, individual timestamp or slope exported.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import statistics

from scripts.movebank_native_ecology_20261019 import (
    HERE, original_files, checksum_and_download, daylength
)
from scripts.movebank_solar_movement_20261019 import load_events, valid_interval
from scripts.movebank_regional_climate_link_20261019 import (
    locked_pairs, link_weather, weather_rolling_30, fixed_timezone
)
from scripts.movebank_six_source_within_animal_era5_date_slopes_20261019 import (
    centered_slope, original_cohort_source_configuration, original_effect_guard,
)
from scripts.movebank_six_source_within_animal_era5_canonical_v1 import canonical_bytes

CONTRACT=HERE/"research/MOVEBANK_SIX_THERMAL_DAY_NIGHT_COMPONENT_V0_20261022.json"
LABELS=("elk_canada","wild_pig_florida","black_bear_connecticut",
        "mule_deer_wyoming","white_tail_virginia","wolves_alberta")
FIELDS=("temperature_2m_mean","precipitation_sum","et0_fao_evapotranspiration")
PREDICTORS=("temp_C","water_per_100mm")
PARTS=("relative","day","night")
REL_TOL=1e-10
CLIMATE_TOL=1e-9
SLOPE_TOL=1e-9


def paired_source_day_night(path:Path):
    """Replay all exact first locked_pairs sources and retain its two components.

    Date matching, solar period, samples, lat rules and steps are copied
    literally from unmodified original helper; original samples compared
    against it date-by-date before returning any new component.
    """
    tracked,n_rows,bad=load_events(path)
    daily=defaultdict(lambda:{"day":[],"night":[],"lat":[]})
    for ind,obs in tracked.items():
        obs.sort(key=lambda x:x[0])
        for a,b in zip(obs,obs[1:]):
            step=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if step is None:
                continue
            d,part,speed,hours,lat=step
            daily[(ind,d)][part].append(speed)
            daily[(ind,d)]["lat"].append(lat)
    tracked.clear()
    good=defaultdict(dict)
    for (individual,d),vals in daily.items():
        if len(vals["day"])<3 or len(vals["night"])<3:
            continue
        good[(individual,d.year)][d]={
            "day":statistics.median(vals["day"]),
            "night":statistics.median(vals["night"]),
            "n_day":len(vals["day"]),"n_night":len(vals["night"]),
            "lat":statistics.mean(vals["lat"]),
        }
    del daily
    by_animal=defaultdict(list)
    for (animal,year),obs in good.items():
        if not obs or statistics.mean(x["lat"] for x in obs.values())<=0:
            continue
        pivot=date(year,6,21)
        up=[d for d in obs if d<pivot]
        down=[d for d in obs if d>pivot]
        edges=[]
        for da in up:
            a=obs[da]
            for db in down:
                b=obs[db]
                if (db-da).days<30:
                    continue
                gap=abs(daylength(a["lat"],da)-daylength(b["lat"],db))*60
                if gap>5:
                    continue
                if any(not .5<=a["n_"+part]/b["n_"+part]<=2
                       for part in ("day","night")):
                    continue
                edges.append((gap,da,db))
        used_a=set(); used_b=set(); pairs=[]
        for gap,da,db in sorted(edges):
            if da in used_a or db in used_b:
                continue
            a,b=obs[da],obs[db]
            delta_day=math.log1p(b["day"])-math.log1p(a["day"])
            delta_night=math.log1p(b["night"])-math.log1p(a["night"])
            pairs.append((da,db,delta_night-delta_day,delta_day,delta_night))
            used_a.add(da);used_b.add(db)
        if len(pairs)>=10:
            by_animal[animal].append(pairs)
    return list(by_animal.values()),n_rows


def pair_replay(original_years,new_years):
    if len(original_years)!=len(new_years):
        raise ValueError("HOLD_OLD_GPS_ANIMAL_ROSTER_CHANGED")
    for orig_animal,new_animal in zip(original_years,new_years):
        if len(orig_animal)!=len(new_animal):
            raise ValueError("HOLD_OLD_GPS_INDIVIDUAL_YEAR_COUNT_DRIFT")
        for old_year,new_year in zip(orig_animal,new_animal):
            if len(old_year)!=len(new_year):
                raise ValueError("HOLD_OLD_SOLAR_DATE_PAIR_COUNT_DRIFT")
            for old,new in zip(old_year,new_year):
                if old[:2]!=new[:2] or abs(old[2]-new[2])>REL_TOL:
                    raise ValueError("HOLD_OLD_GPS_DATE_PAIR_OR_RELATIVE_OUTCOME_DRIFT")
                if abs((new[4]-new[3])-new[2])>1e-12:
                    raise ValueError("HOLD_NIGHT_MINUS_DAY_COMPONENT_IDENTITY")
    return True


def archived_daily_weather(snapshot:dict,label:str,grid:dict):
    if snapshot.get("status")!="PUBLIC_COARSE_ERA5_ORIGINAL_SCIENTIFIC_DAILY_FIELDS_V1":
        raise ValueError("HOLD_ARCHIVED_ERA5_SOURCE_STATUS_DRIFT")
    entries=snapshot.get("source_groups",[])
    by_label={x["cohort_source_label"]:x for x in entries}
    if len(by_label)!=6 or label not in by_label:
        raise ValueError("HOLD_CANONICAL_SOURCE_SIX_COHORT_ROSTER_DRIFT")
    weather={}
    receipts=[]
    for src in by_label[label]["new_stable_scientific_daily_snapshots"]:
        scientific={k:v for k,v in src.items() if k not in
                    ("canonical_scientific_source_sha256","source_url")}
        digest=hashlib.sha256(canonical_bytes(scientific)).hexdigest()
        if digest!=src["canonical_scientific_source_sha256"]:
            raise ValueError("HOLD_ORIGINAL_DAILY_CLIMATE_SCIENTIFIC_SHA_CHANGED")
        if (scientific["timezone"]!=fixed_timezone(grid["longitude"])
            or abs(scientific["latitude"]-grid["latitude"])>.5
            or abs(scientific["longitude"]-grid["longitude"])>.5):
            raise ValueError("HOLD_ORIGINAL_COHORT_CLIMATE_GRID_OR_TZ_CHANGED")
        units=scientific["daily_units"]
        if any(units.get(k)!=u for k,u in zip(FIELDS,("°C","mm","mm"))):
            raise ValueError("HOLD_ORIGINAL_DAILY_SOURCE_UNITS")
        d=scientific["daily"]
        dates=d["time"]
        if not dates or any(len(d[k])!=len(dates) for k in FIELDS):
            raise ValueError("HOLD_ORIGINAL_DAILY_WEATHER_VECTOR_LENGTH")
        start=date.fromisoformat(dates[0])
        if dates!=[(start+timedelta(days=i)).isoformat() for i in range(len(dates))]:
            raise ValueError("HOLD_ORIGINAL_DAILY_SOURCE_NONCONSECUTIVE")
        for i,raw_day in enumerate(dates):
            day=date.fromisoformat(raw_day)
            if day in weather:
                raise ValueError("HOLD_CLIMATE_DAILY_SOURCE_OVERLAP")
            vals=[d[k][i] for k in FIELDS]
            if any(v is None or isinstance(v,bool) or
                   not isinstance(v,(int,float)) or not math.isfinite(v) for v in vals):
                weather[day]=None
            elif vals[1]<0 or vals[2]<0:
                weather[day]=None
            else:
                weather[day]=tuple(vals)
        receipts.append({
            "v1_source_scientific_SHA256":digest,
            "date_count":len(dates),
            "original_fixed_public_ERA5_reference":[grid["latitude"],grid["longitude"]],
            "contains_gps_locations_or_animals":False,
        })
    return weather,receipts


def previous_regional_climate_guard(original_years,weather,old,expected_n):
    link=link_weather(original_years,weather)
    if link["status"]!="descriptive_coarse_region_weather_link":
        raise ValueError("HOLD_ORIGINAL_SIX_SOURCE_CLIMATE_JOIN")
    if (link["individuals_with_complete_weather_and_displacement"]!=expected_n
        or link["missing_weather_date_pairs"]!=0
        or abs(link["mean_falling_minus_rising_regional_temperature_c"]-old[0])>CLIMATE_TOL
        or abs(link["mean_falling_minus_rising_regional_p_minus_et0_30d_mm"]-old[1])>CLIMATE_TOL):
        raise ValueError("HOLD_OLD_SIX_SOURCE_CLIMATE_MEAN_NOT_REPLAYED")
    return link


def year_slopes(detailed_pairs,weather):
    points=[]
    for rising,falling,relative,day,night in detailed_pairs:
        a=weather_rolling_30(weather,rising)
        b=weather_rolling_30(weather,falling)
        if a is None or b is None:
            continue
        points.append((b[0]-a[0],b[1]-a[1],relative,day,night))
    result={}
    for kind in PREDICTORS:
        indexes={"relative":2,"day":3,"night":4}
        values={p:centered_slope([(row[0],row[1],row[index]) for row in points],kind)
                for p,index in indexes.items()}
        if (values["relative"] is None)!=(values["day"] is None) or (
            values["relative"] is None)!=(values["night"] is None):
            raise ValueError("HOLD_COMPONENT_SD_OR_PAIR_SET_DRIFT")
        if values["relative"] is not None and abs(values["relative"]-
                       (values["night"]-values["day"]))>1e-12:
            raise ValueError("HOLD_RELATIVE_BETA_NOT_NIGHT_MINUS_DAY")
        result[kind]=values
    return result


def summarize_original_animals(values):
    usable=[v for v in values if v is not None]
    loo=[statistics.mean(usable[:i]+usable[i+1:])
         for i in range(len(usable))] if len(usable)>1 else []
    return {
        "original_animals":len(values),
        "admitted_animal_slope":len(usable),
        "undefined_animal_slope":len(values)-len(usable),
        "mean":statistics.mean(usable) if usable else None,
        "median":statistics.median(usable) if usable else None,
        "positive":sum(v>0 for v in usable),
        "negative":sum(v<0 for v in usable),
        "zero":sum(v==0 for v in usable),
        "leave_one_animal_out_mean_min_max_NOT_CI":
            [min(loo),max(loo)] if loo else None,
    }


def individual_nested_component_summary(detailed,weather,expected_relative_means):
    # Complete original date list; equally weight years within a marked individual.
    by_kind={kind:{part:[] for part in PARTS} for kind in PREDICTORS}
    valid_years=Counter()
    for individual in detailed:
        nested=defaultdict(lambda:defaultdict(list))
        for year in individual:
            slopes=year_slopes(year,weather)
            for kind in PREDICTORS:
                vals=slopes[kind]
                if vals["relative"] is not None:
                    valid_years[kind]+=1
                for part in PARTS:
                    if vals[part] is not None:
                        nested[kind][part].append(vals[part])
        for kind in PREDICTORS:
            for part in PARTS:
                xs=nested[kind][part]
                by_kind[kind][part].append(statistics.mean(xs) if xs else None)
    result={}
    for kind in PREDICTORS:
        counts={p:summarize_original_animals(by_kind[kind][p]) for p in PARTS}
        relmean=counts["relative"]["mean"]
        if relmean is None or abs(relmean-expected_relative_means[kind])>SLOPE_TOL:
            raise ValueError("HOLD_ORIGINAL_RELATIVE_CLIMATE_SLOPE_NOT_REPLAYED")
        for part in ("day","night"):
            if counts[part]["admitted_animal_slope"]!=counts["relative"]["admitted_animal_slope"]:
                raise ValueError("HOLD_COMPONENT_SLOPE_SUPPORT_NOT_IDENTICAL")
        if abs(counts["night"]["mean"]-counts["day"]["mean"]-relmean)>1e-12:
            raise ValueError("HOLD_SOURCE_ANIMAL_MEAN_COMPONENT_IDENTITY")
        result[kind]={
            "source_individual_years_with_admitted_slope":valid_years[kind],
            "β_relative_NIGHT_minus_DAY":counts["relative"],
            "β_day_absolute_observed_displacement":counts["day"],
            "β_night_absolute_observed_displacement":counts["night"],
            "source_level_β_identity_residual":
                counts["night"]["mean"]-counts["day"]["mean"]-relmean,
            "previous_frozen_relative_slope_replayed":True,
        }
    return result


def run(archived_weather_file:Path,out_dir:Path):
    cfg=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if cfg["id"]!="MOVEBANK_SIX_COHORT_THERMAL_DAY_NIGHT_COMPONENT_V0_20261022":
        raise ValueError("HOLD_REGISTERED_SCIENCE_CONTRACT_CHANGED")
    raw=archived_weather_file.read_bytes()
    snapshot=json.loads(raw)
    sources=original_cohort_source_configuration()
    if len(sources)!=6 or list(sources)!=list(LABELS):
        # Source dict in previous helper matches LABELS exact fixed order.
        raise ValueError("HOLD_ORIGINAL_SIX_COHORT_ORDER")
    out_dir.mkdir(parents=True,exist_ok=True)
    results=[]
    for label in LABELS:
        source=sources[label]["source"]
        grid=sources[label]["grid"]
        prevmean=cfg["original_group_sampled_relative_movement"][label]
        prevn=cfg["original_group_n_animals"][label]
        item={
            "source_label":label,
            "taxon":source["taxon"],
            "source_DOI":source["doi"],
            "old_sampled_relative_GPS_effect":prevmean,
            "original_source_n_individuals":prevn,
            "status":"HOLD_ORIGINAL_SOURCE_OR_COMPONENT_NOT_ADMITTED",
        }
        path=out_dir/("temp_original_"+label+".csv")
        try:
            files=[f for f in original_files(source["package_uuid"])
                   if f["bitstream_uuid"]==source["original_csv_bitstream_uuid"]]
            if len(files)!=1:
                raise ValueError("HOLD_ORIGINAL_MOVE_BANK_BITSTREAM_NOT_UNIQUE")
            ck=files[0]["checksum"]
            if (ck["checkSumAlgorithm"].upper()!="MD5"
                or ck["value"].lower()!=source["original_csv_md5"].lower()):
                raise ValueError("HOLD_ORIGINAL_MOVE_BANK_MD5_CHANGED")
            item["source_original_integrity"]=checksum_and_download(files[0],path)
            old_years,old_mean,counts=locked_pairs(path)
            original_effect_guard(old_mean,counts,prevmean,prevn)
            item["first_original_group_GPS_effect_and_cohort_exactly_replayed"]=True
            new_years,new_rows=paired_source_day_night(path)
            pair_replay(old_years,new_years)
            if new_rows!=counts["gps_rows"]:
                raise ValueError("HOLD_ORIGINAL_GPS_RAW_ROW_COUNT_DIFFERENT")
            item["original_matched_date_pair_roster_and_relative_outcomes_replayed"]=True
            weather,receipts=archived_daily_weather(snapshot,label,grid)
            oldweather=previous_regional_climate_guard(
                old_years,weather,cfg["original_group_regional_T_and_water_means"][label],prevn
            )
            item["previous_regional_ERA5_cohort_thermal_water_means_replayed"]=True
            item["source_original_canonical_ERA5_daily_snapshot"]=receipts
            item["original_source_individual_years"]=counts["included_individual_years"]
            item["original_source_individual_matched_pairs"]=counts["included_calendar_pairs"]
            item["climate_missed_original_matched_pairs"]=oldweather["missing_weather_date_pairs"]
            rel={
                "temp_C":cfg["original_group_relative_night_OLS_slope"][label],
                "water_per_100mm":cfg["original_group_water_slope_per_100mm"][label],
            }
            item["associations"]=individual_nested_component_summary(new_years,weather,rel)
            item["status"]="EXPLORATORY_ORIGINAL_GPS_COMPONENT_TEMPERATURE_WATER_SLOPES"
        except Exception as exc:
            item.update(status="HOLD_ORIGINAL_SOURCE_OR_COMPONENT_NOT_ADMITTED",
                        error_type=type(exc).__name__,error_detail=str(exc)[:200],
                        no_new_component_ecology_conclusion=True)
        finally:
            path.unlink(missing_ok=True)
        results.append(item)
        print("DAY_NIGHT_ORIGINAL_GPS_CLIMATE_COMPONENT "+json.dumps({
            "source":label, "status":item["status"],
            "temp":item.get("associations",{}).get("temp_C"),
            "water":item.get("associations",{}).get("water_per_100mm"),
        },sort_keys=True),flush=True)
    result={
        "status":"SIX_SOURCE_GPS_ABSOLUTE_DAY_NIGHT_ERA5_COMPONENT_EXPLORATION",
        "original_animal_total":cfg["original_total_individual_animals"],
        "original_scientific_daily_ERA5_archived_sha256":
            hashlib.sha256(raw).hexdigest(),
        "source_results":results,
        "source_admitted_count":sum(r["status"].startswith("EXPLORATORY_ORIGINAL_GPS") for r in results),
        "source_holds":sum(r["status"].startswith("HOLD_") for r in results),
        "source_per_animal_dates_ID_or_original_GPS_coordinates_exported":False,
        "true_animal_behavior_or_energy_expenditure_identified":False,
        "causal_effect_of_heat_or_hydrology_identified":False,
        "source_level_habitat_and_taxon_confounded":True,
        "interpretation":"Fixed same individual/solar dates. β(relative NIGHT−DAY) = β(NIGHT)−β(DAY) observational slope identity; cannot interpret as a causal decomposition of thermoregulation."
    }
    (out_dir/"movebank_six_source_thermal_day_night_component_v0.json").write_text(
        json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-era5-snapshot",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    r=run(args.original_era5_snapshot,args.output_dir)
    print("SIX_GPS_ABSOLUTE_DAY_NIGHT_ERA5_SUMMARY "+json.dumps({
        "admitted":r["source_admitted_count"],"holds":r["source_holds"],
        "cohorts":[{
            "label":z["source_label"],"status":z["status"],
            "temp_components":{
                k:v["mean"] for k,v in
                z.get("associations",{}).get("temp_C",{}).items()
                if isinstance(v,dict) and "mean" in v
            },
            "error":z.get("error_detail")
        } for z in r["source_results"]]
    },sort_keys=True))
    if r["source_admitted_count"]==0:
        raise SystemExit(2)


if __name__=="__main__":
    main()
