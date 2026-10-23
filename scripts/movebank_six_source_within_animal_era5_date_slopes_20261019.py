#!/usr/bin/env python3
"""Post-outcome EXPLORATORY matched-day ERA5 climate/movement associations.

Reproduce all six original source-MD5-authenticated GPS cohort effects
BEFORE requesting any new regional ERA5 data. Analyze climate difference
and original night-minus-day minimum GPS displacement change only within
the SAME original individual × matched-solstice-year date roster.
Pairwise weather repeats and solar seasons are NOT independent climate draws;
slopes are observational co-trends, NOT causal or individual microclimate.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import statistics

from scripts.movebank_native_ecology_20261019 import (
    HERE, original_files, checksum_and_download
)
from scripts.movebank_regional_climate_link_20261019 import (
    locked_pairs, read_weather, weather_rolling_30
)

CFG=HERE/"research/MOVEBANK_SIX_COHORT_WITHIN_ANIMAL_ERA5_SLOPES_V0_20261019.json"
PILOT=HERE/"research/MOVEBANK_NATIVE_OBSERVATION_PILOT_20261019.json"
EXTENSION=HERE/"research/MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_20261019.json"
PILOT_ENV=HERE/"research/MOVEBANK_REGIONAL_ERA5_MOVEMENT_LINK_V0_20261019.json"
EXT_ENV=HERE/"research/MOVEBANK_EXTENSION_THREE_ERA5_DATE_CONTEXT_V0_20261019.json"

LABELS=("elk_canada","wild_pig_florida","black_bear_connecticut",
        "mule_deer_wyoming","white_tail_virginia","wolves_alberta")
MIN_ORIGINAL_PAIRS_PER_YEAR=10
MIN_WEATHER_COMPLETE_PAIRS=10
MIN_TEMP_SD_C=0.5
MIN_WATER_SD_MM=10.

def strictly_valid_source(s,expected_mean,expected_n,meta):
    files=[f for f in original_files(s["package_uuid"])
           if f["bitstream_uuid"]==s["original_csv_bitstream_uuid"]]
    if len(files)!=1:
        raise ValueError("HOLD_ORIGINAL_NATIVE_BITSTREAM_NOT_UNIQUE")
    ck=files[0].get("checksum") or {}
    if (ck.get("checkSumAlgorithm","").upper()!="MD5"
        or ck.get("value","").lower()!=s["original_csv_md5"].lower()):
        raise ValueError("HOLD_ORIGINAL_MOVE_BANK_MD5_CHANGED")
    if (s["label"]!=meta["label"]
        or not isinstance(expected_mean,(int,float))
        or expected_n<5):
        raise ValueError("HOLD_PRIOR_SOURCE_COHORT_REGISTRY_CHANGED")
    return files[0]

def original_effect_guard(value,counts,old_mean,expected_n):
    if value is None or abs(value-old_mean)>1e-10:
        raise ValueError("HOLD_PREVIOUS_MAMMAL_GPS_EFFECT_CHANGED")
    if counts["source_individuals"]!=expected_n or counts["included_calendar_pairs"]<10:
        raise ValueError("HOLD_PREVIOUS_ANIMAL_COUNT_OR_MATCHED_DATE_DRIFT")
    return True

def centered_slope(data,which):
    """Return x/y centered least-squares slope of y on a single paired-date climate x.

    data pairs (temperatureDeltaC, waterDeltaMm, sourceOriginalGPSNightDayDelta)
    are already admitted original same-animal one-to-one photoperiod pairs.
    SD floors prevent dividing by a constant/narrow climate covariate.
    """
    if len(data)<MIN_WEATHER_COMPLETE_PAIRS:
        return None
    idx=0 if which=="temp_C" else 1
    if which not in ("temp_C","water_per_100mm"):
        raise ValueError("HOLD_UNREGISTERED_ENVIRONMENT_PREDICTOR")
    x=[float(p[idx])/(100. if idx==1 else 1.) for p in data]
    y=[float(p[2]) for p in data]
    if not all(math.isfinite(v) for v in x+y):
        raise ValueError("HOLD_NONFINITE_ORIGINAL_CLIMATE_GPS_COVARIATE")
    sd=statistics.pstdev(x)
    if sd <= (MIN_TEMP_SD_C if idx==0 else MIN_WATER_SD_MM/100.):
        return None
    xb=statistics.mean(x);yb=statistics.mean(y)
    den=sum((v-xb)**2 for v in x)
    if den<=0:return None
    return sum((v-xb)*(w-yb) for v,w in zip(x,y))/den

def matched_year_climate_original(pairs,weather):
    valid=[];missing=0
    for rising,falling,movement in pairs:
        early=weather_rolling_30(weather,rising)
        late=weather_rolling_30(weather,falling)
        if early is None or late is None:
            missing+=1
            continue
        dt=late[0]-early[0]
        dw=late[1]-early[1]
        if not (math.isfinite(dt) and math.isfinite(dw) and math.isfinite(movement)):
            raise ValueError("HOLD_NONFINITE_ORIGINAL_ANIMAL_WEATHER_DATE_PAIR")
        valid.append((dt,dw,movement))
    return valid,missing

def describe_animal_slopes(group):
    """One value per distinct marked individual. No pseudo-independent GPS fixes."""
    s=[v for v in group if v is not None]
    n=len(s)
    if n<1:
        return {"n_original_animals":len(group),"n_slope_admitted_animals":0,
                "n_undefined_animals":len(group),"mean":None,"median":None,
                "positive":0,"negative":0,"zero":0,
                "leave_one_individual_out_mean_range_NOT_CI":None}
    loo=[statistics.mean(s[:i]+s[i+1:]) for i in range(n)] if n>1 else []
    return {
        "n_original_animals":len(group),
        "n_slope_admitted_animals":n,
        "n_undefined_animals":len(group)-n,
        "mean":statistics.mean(s),
        "median":statistics.median(s),
        "positive":sum(x>0 for x in s),
        "negative":sum(x<0 for x in s),
        "zero":sum(x==0 for x in s),
        "leave_one_individual_out_mean_range_NOT_CI":[min(loo),max(loo)] if loo else None
    }

def original_cohort_source_configuration():
    p=json.loads(PILOT.read_text(encoding="utf-8"))
    e=json.loads(EXTENSION.read_text(encoding="utf-8"))
    if len(p["sources"])!=3 or len(e["sources"])!=8:
        raise ValueError("HOLD_ORIGINAL_PUBLIC_SOURCE_INVENTORY_DRIFT")
    pindex={s["label"]:s for s in p["sources"]}
    eindex={s["label"]:s for s in e["sources"]}
    if len(pindex)!=3 or len(eindex)!=8:
        raise ValueError("HOLD_ORIGINAL_SOURCE_DUPLICATE_IDS")
    env1=json.loads(PILOT_ENV.read_text(encoding="utf-8"))
    env2=json.loads(EXT_ENV.read_text(encoding="utf-8"))
    sources={}
    for label in LABELS:
        if label in pindex:
            s=pindex[label]
            grid=env1["coarse_weather_reference_sites"][label]
        else:
            s=eindex[label]
            grid=env2["geographic_exposure"][label]
        sources[label]={"source":s,"grid":grid}
    return sources

def run(out_dir:Path):
    cfg=json.loads(CFG.read_text(encoding="utf-8"))
    registered=cfg["source_cohorts"]
    if cfg.get("id")!="MOVEBANK_SIX_COHORT_WITHIN_ANIMAL_MATCHED_ERA5_ASSOC_V0" or tuple(registered["labels_fixed"])!=LABELS:
        raise ValueError("HOLD_SIX_SOURCE_AFTER_OUTCOME_CONTRACT_CHANGED")
    origins=original_cohort_source_configuration()
    expected_means=registered["original_source_effects_exact"]
    expected_ns=registered["original_individual_counts_exact"]
    if len(expected_means)!=6 or len(expected_ns)!=6:
        raise ValueError("HOLD_SIX_ORIGINAL_RESULTS_NOT_REGISTERED")
    out_dir.mkdir(parents=True,exist_ok=True)
    source_reports=[]
    for label in LABELS:
        r=origins[label];s=r["source"];grid=r["grid"]
        report={"source":label,"doi":s["doi"],"taxon":s["taxon"],
                "original_expected_effect":expected_means[label],
                "original_expected_eligible_animals":expected_ns[label],
                "status":"HOLD_NATIVE_GPS_OR_CLIMATE_SOURCE",
                "within_animal_temperature_or_water_Causality":False}
        p=out_dir/("temporary_original_"+label+".csv")
        try:
            native=strictly_valid_source(s,expected_means[label],expected_ns[label],s)
            report["original_source_integrity"]=checksum_and_download(native,p)
            years,old_mean,counts=locked_pairs(p)
            original_effect_guard(old_mean,counts,expected_means[label],expected_ns[label])
            report["original_previous_movement_effect_reproduced"]=True
            report.update(counts)
            d=[dt for animal in years for year in animal for rise,fall,_ in year for dt in (rise,fall)]
            if not d:raise ValueError("HOLD_ORIGINAL_ANIMAL_DATEPAIRS_MISSING")
            # Critically the original outcome is frozen/reproduced BEFORE
            # environmental source acquisition in this new exploratory route.
            weather,receipts=read_weather(grid,min(d),max(d))
            report["coarse_public_reference_grid"]={
                "latitude":grid["latitude"],"longitude":grid["longitude"],
                "source_date_reference_only_not_animal_temperature":True}
            report["weather_original_source_receipts"]=receipts
            person_slopes={"temp_C":[],"water_per_100mm":[]}
            total_weather_matched_pairs=total_weather_missing_pairs=0
            original_years=0;admissible_years={"temp_C":0,"water_per_100mm":0}
            for animal in years:
                by_person={"temp_C":[],"water_per_100mm":[]}
                for yr in animal:
                    original_years+=1
                    valid,missing=matched_year_climate_original(yr,weather)
                    total_weather_matched_pairs+=len(valid)
                    total_weather_missing_pairs+=missing
                    for x in ("temp_C","water_per_100mm"):
                        slope=centered_slope(valid,x)
                        if slope is not None:
                            admissible_years[x]+=1
                            by_person[x].append(slope)
                for x in ("temp_C","water_per_100mm"):
                    person_slopes[x].append(statistics.mean(by_person[x]) if by_person[x] else None)
            report.update(status="EXPLORATORY_WITHIN_ORIGINAL_ANIMAL_ERA5_DATE_ASSOCIATION",
                          original_matched_animal_years=original_years,
                          source_pairs_with_ERA5_and_movement=total_weather_matched_pairs,
                          source_pairs_missing_ERA5=total_weather_missing_pairs,
                          year_slopes_admitted=admissible_years,
                          beta_temperature_log1p_GPS_per_C=describe_animal_slopes(person_slopes["temp_C"]),
                          beta_water_balance_log1p_GPS_per_100mm=describe_animal_slopes(person_slopes["water_per_100mm"]),
                          observational_association_only=True,
                          source_region_date_confounded=True)
        except Exception as exc:
            report.update(status="HOLD_NATIVE_GPS_OR_CLIMATE_SOURCE",
                          error_type=type(exc).__name__,
                          error_detail=str(exc)[:220],
                          no_environment_GPS_slope_inferred=True)
        finally:
            p.unlink(missing_ok=True)
        source_reports.append(report)
        print("ORIGINAL_ERA5_WITHIN_INDIVIDUAL_CLIMATE_PAIR_ASSOC "+json.dumps({
            "source":label,"status":report["status"],
            "n":report.get("source_individuals"),
            "temp":report.get("beta_temperature_log1p_GPS_per_C"),
            "water":report.get("beta_water_balance_log1p_GPS_per_100mm"),
        },sort_keys=True),flush=True)
    result={
        "status":"EXPLORATORY_SIX_SOURCE_WITHIN_INDIVIDUAL_PAIRED_DATE_ERA5",
        "source_cohorts":source_reports,
        "original_six_sources_and_effects_unchanged":True,
        "expected_animals":sum(expected_ns.values()),
        "completed_source_count":sum(r["status"]=="EXPLORATORY_WITHIN_ORIGINAL_ANIMAL_ERA5_DATE_ASSOCIATION" for r in source_reports),
        "source_holds":sum(r["status"].startswith("HOLD_") for r in source_reports),
        "observational_response":"within-individual original solar-daylength-matched relative NIGHT−DAY GPS MINIMUM straight-line speed change, not time-active",
        "environment":"coarse original source-region ERA5 daily 2m air temp and antecedent 30d P−ET0 modeled proxy; not direct animal microclimate",
        "seasonal_calendar_and_source_GPS_dependence_unresolved":True,
        "inference":"Descriptive one-covariate within-individual solar-date association only; no p-values, causal model, or global animal behavior law",
        "individual_animal_ids_or_raw_GPS_coordinates_timestamps_exported":False,
    }
    (out_dir/"six_source_individual_year_climate_movements.json").write_text(
        json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    data=run(args.out)
    print("SIX_SOURCE_CLIMATE_PAIRED_ANIMAL_SUMMARY "+json.dumps({
        "completed":data["completed_source_count"],"holds":data["source_holds"],
        "by_source":[{"source":r["source"],"status":r["status"],
                      "T_mean_slope":r.get("beta_temperature_log1p_GPS_per_C",{}).get("mean"),
                      "W_mean_slope":r.get("beta_water_balance_log1p_GPS_per_100mm",{}).get("mean")}
                     for r in data["source_cohorts"]]},sort_keys=True),flush=True)
    if data["completed_source_count"]==0:raise SystemExit(2)

if __name__=="__main__":main()
