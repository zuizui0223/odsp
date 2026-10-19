#!/usr/bin/env python3
"""Post-original-outcome, within-INDIVIDUAL-YEAR paired GPS/ERA5 associations.

Do not treat pair dates/animals as independent climate replicates. Source ORIGINAL
MD5, original cohort mean GPS e, original source ERA5 response SHA256 and prior
published source means MUST replay before new rho calculation. Retain source holds.
Outputs only per-cohort aggregate results, never animal IDs, exact times or GPS.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from datetime import date, timedelta
from urllib.parse import urlencode
import hashlib
import statistics

from scripts.movebank_native_ecology_20261019 import (
    HERE, PILOT, original_files, checksum_and_download
)
from scripts.movebank_regional_climate_link_20261019 import (
    locked_pairs, link_weather, weather_rolling_30, API, FIELDS, fixed_timezone, source_read
)

BASE = HERE / "research"
CONTRACT = BASE / "MOVEBANK_WITHIN_ANIMAL_ERA5_ASSOCIATION_V0_20261019.json"
EXTENSION = BASE / "MOVEBANK_SOLAR_MOVEMENT_EXTENSION_V0_20261019.json"
LABELS = (
    "elk_canada", "wild_pig_florida", "black_bear_connecticut",
    "mule_deer_wyoming", "white_tail_virginia", "wolves_alberta"
)
MIN_PAIRS = 10
MIN_WEATHER_COVERAGE = .80
MIN_FINITE = 8
MIN_UNIQUE = 4
MIN_INDIVIDUALS_HEADLINE = 5


def midranks(values):
    if not values:
        return []
    order = sorted(range(len(values)), key=lambda i: values[i])
    rank = [0.0] * len(values)
    j = 0
    while j < len(order):
        k = j + 1
        while k < len(order) and values[order[k]] == values[order[j]]:
            k += 1
        # one-based average rank for every tied set
        center = ((j+1) + k) / 2
        for idx in order[j:k]:
            rank[idx] = center
        j = k
    return rank


def spearman_paired(x, y):
    """Tie-aware descriptive Spearman; no hypothesis test or p-value."""
    if len(x) != len(y) or len(x) < MIN_FINITE:
        return None
    if (any(not math.isfinite(float(v)) for v in [*x, *y])
        or len(set(x)) < MIN_UNIQUE or len(set(y)) < MIN_UNIQUE):
        return None
    rx = midranks(x)
    ry = midranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    dx = [v-mx for v in rx]
    dy = [v-my for v in ry]
    den = math.sqrt(sum(v*v for v in dx)*sum(v*v for v in dy))
    return sum(a*b for a,b in zip(dx,dy))/den if den else None


def summarize_animals(values, candidate):
    x = [v for v in values if v is not None]
    loo = [statistics.mean(x[:i]+x[i+1:]) for i in range(len(x))] if len(x)>1 else []
    return {
        "original_individuals_in_source":candidate,
        "individuals_with_finite_within_year_rho":len(x),
        "individuals_undefined_or_insufficient":candidate-len(x),
        "rho_mean_over_individuals":statistics.mean(x) if x else None,
        "rho_median_over_individuals":statistics.median(x) if x else None,
        "individual_rho_positive":sum(v>0 for v in x),
        "individual_rho_negative":sum(v<0 for v in x),
        "individual_rho_exactly_zero":sum(v==0 for v in x),
        "leave_one_individual_out_rho_mean_range_NOT_CI":[min(loo),max(loo)] if loo else None,
        "minimum_five_individuals_for_descriptive_source_mean":len(x)>=MIN_INDIVIDUALS_HEADLINE,
    }


def year_pairwise_spearman(pairs, weather):
    """Same fixed source pair list, never substitute/choose date on e or Δweather."""
    n = len(pairs)
    t, water, effect = [], [], []
    missing = 0
    for rising, falling, e in pairs:
        a = weather_rolling_30(weather, rising)
        b = weather_rolling_30(weather, falling)
        if a is None or b is None:
            missing += 1
            continue
        dt = b[0]-a[0]
        dw = b[1]-a[1]
        if any(not math.isfinite(v) for v in (dt,dw,e)):
            missing += 1
            continue
        t.append(dt)
        water.append(dw)
        effect.append(e)
    coverage = (len(effect)/n if n else 0.0)
    admitted = n>=MIN_PAIRS and coverage>=MIN_WEATHER_COVERAGE and len(effect)>=MIN_FINITE
    result = {
        "original_matched_source_datepairs":n,
        "qualified_weather_datepairs":len(effect),
        "weather_missing_datepairs":missing,
        "weather_pair_coverage":coverage,
        "year_pair_source_support":admitted,
        "mean_relative_night_minus_day_source_effect":statistics.mean(effect) if admitted else None,
        "mean_falling_minus_rising_regional_T":statistics.mean(t) if admitted else None,
        "mean_falling_minus_rising_regional_PminusET0":statistics.mean(water) if admitted else None,
        "spearman_source_temperature_vs_relative_night_displacement":
            spearman_paired(t,effect) if admitted else None,
        "spearman_source_water_vs_relative_night_displacement":
            spearman_paired(water,effect) if admitted else None,
    }
    return result


def mean_or_none(values):
    finite=[x for x in values if x is not None]
    return statistics.mean(finite) if finite else None


def individual_nested_summary(original_animal_years, weather):
    """One animal contributes one statistic per predictor after equally weighting years."""
    animals = []
    year_support = Counter()
    for years in original_animal_years:
        yr = [year_pairwise_spearman(pairs,weather) for pairs in years]
        year_support["original_individual_years"] += len(yr)
        year_support["original_matched_source_pairs"] += sum(x["original_matched_source_datepairs"] for x in yr)
        year_support["weather_valid_datepairs"] += sum(x["qualified_weather_datepairs"] for x in yr)
        year_support["weather_missing_datepairs"] += sum(x["weather_missing_datepairs"] for x in yr)
        year_support["years_with_80pct_weather_coverage"] += sum(x["year_pair_source_support"] for x in yr)
        temp = mean_or_none([x["spearman_source_temperature_vs_relative_night_displacement"] for x in yr])
        water = mean_or_none([x["spearman_source_water_vs_relative_night_displacement"] for x in yr])
        animals.append({"temperature_rho":temp,"water_rho":water})
    return {
        "admissibility":dict(year_support),
        "temperature_within_animal_year":summarize_animals(
            [x["temperature_rho"] for x in animals],len(animals)
        ),
        "water_within_animal_year":summarize_animals(
            [x["water_rho"] for x in animals],len(animals)
        )
    }


def verify_unchanged_first_effects(pairs, actual, counts, frozen):
    if len(pairs)!=frozen["n"] or counts["source_individuals"]!=frozen["n"]:
        raise ValueError("HOLD_PRIOR_ANIMAL_COUNTS_DRIFT")
    if actual is None or abs(actual-frozen["e"])>1e-10:
        raise ValueError("HOLD_FIRST_GPS_GROUP_EFFECT_DRIFT")
    if counts["included_calendar_pairs"]<=0:
        raise ValueError("HOLD_NO_ORIGINAL_SOURCE_DATEPAIRS")
    return True


def canonical_climate_payload(source:dict)->dict:
    """ONLY original scientific daily data, not volatile API generationtime_ms."""
    daily=source.get("daily") or {}
    units=source.get("daily_units") or {}
    required=("temperature_2m_mean","precipitation_sum","et0_fao_evapotranspiration")
    for key,unit in zip(required,("°C","mm","mm")):
        if units.get(key)!=unit or not isinstance(daily.get(key),list):
            raise ValueError("HOLD_ERA5_ORIGINAL_DAILY_SOURCE_UNITS_OR_COLUMNS")
    if not isinstance(daily.get("time"),list):
        raise ValueError("HOLD_ERA5_ORIGINAL_CALENDAR_MISSING")
    return {
        "latitude":float(source["latitude"]),
        "longitude":float(source["longitude"]),
        "elevation_m":float(source["elevation"]),
        "timezone":source["timezone"],
        "utc_offset_seconds":source["utc_offset_seconds"],
        "daily_units":{k:units[k] for k in required},
        "daily":{"time":daily["time"],**{k:daily[k] for k in required}},
    }


def canonical_bytes(snapshot:dict)->bytes:
    return json.dumps(snapshot,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")


def read_weather_canonical_v1(ref,first_day,last_day):
    """Reissues identical previously registered ERA5 URLs.

    Produces a separately versioned original daily science snapshot; v0
    raw-response SHA256s are retained as provenance, never falsely asserted to
    match because Open-Meteo's generationtime_ms varies across requests.
    """
    start=first_day-timedelta(days=29)
    end=last_day
    weather={}
    receipts=[]
    daily_snapshots=[]
    for yr in range(start.year,end.year+1,4):
        lo=max(start,date(yr,1,1))
        hi=min(end,date(yr+3,12,31))
        if lo>hi:
            continue
        params={"latitude":ref["latitude"],"longitude":ref["longitude"],
                "start_date":lo.isoformat(),"end_date":hi.isoformat(),
                "daily":",".join(FIELDS),"models":"era5",
                "timezone":fixed_timezone(ref["longitude"]),
                "elevation":"nan","cell_selection":"nearest"}
        url=API+"?"+urlencode(params)
        raw=source_read(url)
        source=json.loads(raw)
        stable=canonical_climate_payload(source)
        if (stable["timezone"] != fixed_timezone(ref["longitude"])
            or abs(stable["latitude"]-ref["latitude"])>.5
            or abs(stable["longitude"]-ref["longitude"])>.5):
            raise ValueError("HOLD_ERA5_SOURCE_GRID_OR_TIMEZONE_DRIFT")
        d=stable["daily"]
        days=d["time"]
        expected_n=(hi-lo).days+1
        if (len(days)!=expected_n or days!=[
            (lo+timedelta(days=i)).isoformat() for i in range(expected_n)]):
            raise ValueError("HOLD_ERA5_SOURCE_MISSING_OR_NONCONSECUTIVE_DAYS")
        if any(len(d[k])!=expected_n for k in FIELDS):
            raise ValueError("HOLD_ERA5_SOURCE_VARIABLE_LENGTH")
        for i,day in enumerate(days):
            parsed=date.fromisoformat(day)
            if parsed in weather:
                raise ValueError("HOLD_ERA5_SOURCE_DUPLICATE_CALENDAR")
            vals=tuple(d[k][i] for k in FIELDS)
            if (any(v is None or isinstance(v,bool) or
                not isinstance(v,(int,float)) or not math.isfinite(v) for v in vals)
                or vals[1]<0 or vals[2]<0):
                weather[parsed]=None
            else:
                weather[parsed]=vals
        digest=hashlib.sha256(canonical_bytes(stable)).hexdigest()
        receipts.append({
            "source_url":url,
            "source_returned_days":expected_n,
            "source_provider_grid":[stable["latitude"],stable["longitude"]],
            "new_v1_canonical_daily_content_sha256":digest,
            "raw_response_sha256_diagnostic_only":hashlib.sha256(raw).hexdigest(),
            "raw_response_generationtime_ms_present":"generationtime_ms" in source,
            "volatile_generationtime_ms_EXCLUDED_from_canonical":True,
        })
        daily_snapshots.append({"source_url":url,**stable,
            "canonical_scientific_source_sha256":digest})
    return weather,receipts,daily_snapshots


def validate_first_regional_ERA5(actual_summary, receipts, frozen):
    # The first raw-response SHA cannot be replayed because generationtime_ms
    # changes. Source scientific fields and six previously published
    # aggregate GPS and climate quantities must otherwise reproduce exactly.
    if actual_summary["status"]!="descriptive_coarse_region_weather_link":
        raise ValueError("HOLD_FIRST_ERA5_DATE_JOIN_NOT_COMPLETE")
    if (actual_summary["individuals_with_complete_weather_and_displacement"]!=frozen["n"]
        or abs(actual_summary["mean_falling_minus_rising_regional_temperature_c"]-frozen["t"])>1e-10
        or abs(actual_summary["mean_falling_minus_rising_regional_p_minus_et0_30d_mm"]-frozen["w"])>1e-10
        or abs(actual_summary["mean_observed_falling_minus_rising_relative_log1p_night_day_speed"]-frozen["e"])>1e-10
        or actual_summary["missing_weather_date_pairs"]!=0):
        raise ValueError("HOLD_FIRST_ORIGINAL_ERA5_GROUP_SCIENTIFIC_VALUES_DRIFT")
    if len(receipts)!=len(frozen["sha"]):
        raise ValueError("HOLD_FIRST_ERA5_CHUNK_ROSTER_CHANGED")
    if any(not x["new_v1_canonical_daily_content_sha256"] for x in receipts):
        raise ValueError("HOLD_V1_CANONICAL_WEATHER_SOURCE_MISSING")
    return True


def source_roster():
    originals=json.loads(PILOT.read_text())["sources"]
    additions=json.loads(EXTENSION.read_text())["sources"]
    by_label={o["label"]:o for o in [*originals,*additions]}
    if len(by_label)!=11 or any(x not in by_label for x in LABELS):
        raise ValueError("HOLD_SOURCE_REGISTRY_UNEXPECTED")
    return by_label


def run(out_dir):
    cfg=json.loads(CONTRACT.read_text())
    if cfg["id"]!="MOVEBANK_WITHIN_INDIVIDUAL_YEAR_HYDROTHERMAL_ASSOCIATION_V0_20261019":
        raise ValueError("HOLD_PRE_FROZEN_STUDY_CONTRACT_CHANGED")
    by_label=source_roster()
    refs0=json.loads((BASE/"MOVEBANK_REGIONAL_ERA5_MOVEMENT_LINK_V0_20261019.json").read_text())["coarse_weather_reference_sites"]
    refs1=json.loads((BASE/"MOVEBANK_EXTENSION_THREE_ERA5_DATE_CONTEXT_V0_20261019.json").read_text())["geographic_exposure"]
    out_dir.mkdir(parents=True,exist_ok=True)
    cohort=[]
    weather_snapshots=[]
    for label in LABELS:
        source=by_label[label]
        freeze=cfg["previous_source_results_and_response_raw_SHA"][label]
        pub = refs0.get(label) or refs1.get(label)
        if pub is None:raise ValueError("HOLD_MISSING_PRE_FROZEN_WEATHER_EXPOSURE")
        row={
            "source_label":label,
            "source_taxon":source["taxon"],
            "source_DOI":source["doi"],
            "original_gps_source_effect_prior":freeze["e"],
            "original_gps_individual_count_prior":freeze["n"],
            "status":"HOLD_ORIGINAL_SOURCE_OR_CLIMATE",
            "original_animal_outcomes_reclassified":False,
            "independent_biological_causation_identified":False,
        }
        raw=out_dir/(label+"_private_original_source.csv")
        try:
            if source["original_csv_md5"]!=(
                json.loads((BASE/"MOVEBANK_NATIVE_OBSERVATION_PILOT_20261019.json").read_text())
                ["sources"][[s["label"] for s in json.loads((BASE/"MOVEBANK_NATIVE_OBSERVATION_PILOT_20261019.json").read_text())["sources"]].index(label)]["original_csv_md5"]
                if label in refs0 else
                json.loads(EXTENSION.read_text())["sources"][
                   [s["label"] for s in json.loads(EXTENSION.read_text())["sources"]].index(label)
                ]["original_csv_md5"]
            ):
                raise ValueError("HOLD_ORIGINAL_MD5_SOURCE_MANIFEST_CHANGED")
            native=[x for x in original_files(source["package_uuid"])
                    if x["bitstream_uuid"]==source["original_csv_bitstream_uuid"]]
            if len(native)!=1:
                raise ValueError("HOLD_AMBIGUOUS_ORIGINAL_NATIVE_FILE")
            checksum=native[0].get("checksum") or {}
            if (checksum.get("checkSumAlgorithm","").upper()!="MD5"
                or checksum.get("value","").lower()!=source["original_csv_md5"].lower()):
                raise ValueError("HOLD_PROVIDER_NATIVE_MD5_MISMATCH")
            integrity=checksum_and_download(native[0],raw)
            pairs, actual, counts=locked_pairs(raw)
            verify_unchanged_first_effects(pairs,actual,counts,freeze)
            original_dates=[d for animal in pairs for year in animal
                            for rising,falling,_ in year for d in (rising,falling)]
            weather,receipts,source_snapshots=read_weather_canonical_v1(pub,min(original_dates),max(original_dates))
            validate_first_regional_ERA5(link_weather(pairs,weather),receipts,freeze)
            new_stats=individual_nested_summary(pairs,weather)
            weather_snapshots.append({"cohort_source_label":label,"original_published_raw_envelope_SHA256":freeze["sha"],"new_stable_scientific_daily_snapshots":source_snapshots})
            row.update({
                "status":"EXPLORATORY_WITHIN_ANIMAL_YEAR_SOURCE_DATE_ERA5_ASSOCIATION",
                "source_original_md5_verified":True,
                "source_original_gps_source_rows":counts["gps_rows"],
                "previous_gps_and_weather_source_results_byte_replayed":True,
                "original_GPS_individuals":counts["source_individuals"],
                "original_matched_source_datepairs":counts["included_calendar_pairs"],
                "original_individual_years":counts["included_individual_years"],
                "prior_ERA5_raw_response_envelope_SHA256_NOT_DIRECTLY_REPLAYABLE":freeze["sha"],
                "environment_source_v1_canonical_daily_sha256":[z["new_v1_canonical_daily_content_sha256"] for z in receipts],
                "generationtime_ms_volatile_excluded_from_v1_sha":True,
                "original_30d_climate_context": {
                    "delta_ERA5_daily_T_C":freeze["t"],
                    "delta_ERA5_previous_30d_PminusET0_mm":freeze["w"]
                },
                "within_individual_year_correlations":new_stats,
                "no_animal_ID_positions_raw_timestamps_or_pair_effects_exported":True,
                "description":"Source individual-year Spearman rank correlations from original matched GPS dates and coarse regional ERA5; NOT independently assigned climate exposure or causal behavior."
            })
        except Exception as exc:
            row.update({
                "status":"HOLD_ORIGINAL_SOURCE_OR_CLIMATE",
                "error_type":type(exc).__name__,
                "error_reason_without_individual_identifiers":str(exc)[:200],
                "new_annual_animal_climate_correlation_computed":False
            })
        finally:
            raw.unlink(missing_ok=True)
        cohort.append(row)
        print("MAMMAL_WITHIN_ANIMAL_YEAR_GPS_CLIMATE "+
              json.dumps({"label":label,"status":row["status"],
                "original_individuals":row.get("original_GPS_individuals"),
                "temperature":row.get("within_individual_year_correlations",{}).get("temperature_within_animal_year"),
                "water":row.get("within_individual_year_correlations",{}).get("water_within_animal_year"),
                "error_type":row.get("error_type"),
                "error_reason":row.get("error_reason_without_individual_identifiers")
              },sort_keys=True),flush=True)
    report={
        "status":"SOURCE_VERSIONED_SIX_MAMMAL_COHORT_WITHIN_ANIMAL_YEAR_ERA5_EXPLORATORY_V1",
        "original_failed_v0_source_response_SHA_HOLD_preserved":True,
        "climate_daily_payload_v1_archived_separately":True,
        "previous_GPS_and_ERA5_cohort_result_unmodified":True,
        "source_canonical_v1_semantics":"Raw Open-Meteo API envelope fluctuates generationtime_ms; new source snapshot science payload SHA excludes only transport metadata. Previous daily science arrays were not originally archived, so full original-data equivalence cannot be asserted, while all old group climate and animal means must match.",
        "source_labels_order":list(LABELS),
        "six_cohorts_source_admitted":sum(x["status"].startswith("EXPLORATORY") for x in cohort),
        "six_cohorts_source_hold":sum(x["status"].startswith("HOLD") for x in cohort),
        "within_source_pair_correlation_not_causal_or_global_law":True,
        "results":cohort,
        "no_source_individual_ids_dates_or_locations_exported":True,
        "interpretation":"Within source and individual-year date pairs, directional rank associations only. Coarse ERA5 regional climate, temporally dependent date observations, and original source selection; no p-values."
    }
    (out_dir/"six_source_within_animal_year_ERA5_correlations_v1.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    (out_dir/"six_original_regional_era5_scientific_daily_snapshot_v1.json").write_text(
        json.dumps({"status":"PUBLIC_COARSE_ERA5_ORIGINAL_SCIENTIFIC_DAILY_FIELDS_V1",
                    "original_v0_raw_envelope_not_byte_equivalent":True,
                    "source_weather_not_animal_tracking_or_individual_exposure":True,
                    "source_groups":weather_snapshots},
                   ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    r=run(args.output_dir)
    print("GPS_ENVIRONMENT_WITHIN_COHORTS_SUMMARY "+json.dumps({
        "admitted":r["six_cohorts_source_admitted"],
        "source_hold":r["six_cohorts_source_hold"],
        "results":[{
            "label":x["source_label"],"status":x["status"],
            "n":x.get("original_GPS_individuals"),
            "rho_T":x.get("within_individual_year_correlations",{}).get("temperature_within_animal_year",{}).get("rho_mean_over_individuals"),
            "rho_water":x.get("within_individual_year_correlations",{}).get("water_within_animal_year",{}).get("rho_mean_over_individuals"),
            "eligible_T":x.get("within_individual_year_correlations",{}).get("temperature_within_animal_year",{}).get("individuals_with_finite_within_year_rho"),
            "eligible_water":x.get("within_individual_year_correlations",{}).get("water_within_animal_year",{}).get("individuals_with_finite_within_year_rho"),
        } for x in r["results"]]
    },sort_keys=True))
    if r["six_cohorts_source_admitted"]==0:
        raise SystemExit(2)


if __name__=="__main__":
    main()
