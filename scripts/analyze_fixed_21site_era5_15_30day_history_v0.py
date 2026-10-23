#!/usr/bin/env python3
"""Source-replayed 15/30-day ERA5 histories on the SAME 21×3 fixed solar dates.

Exploratory post-first-one-day-outcome time-scale check. Preserve original
source bytes, local timezone, 63 sites×year pairs, exact endpoint values and
all bad physical observations. Never replace, zero-fill or clip source data.
No animal response, field soil sensor, area-weighted global prevalence or p.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

from scripts.analyze_fixed_21site_global_equinoctial_era5_20261019 import (
    BASE, DATES, compute as replay_original_one_day, desc,
)

FIELDS = ("temperature_2m_mean", "temperature_2m_max",
          "soil_moisture_0_to_7cm_mean", "precipitation_sum")
WINDOWS = (15, 30)
ORIGINAL_1DAY_VALID_PAIRS = 62
ORIGINAL_1DAY_OPPOSITE = 29


def load_sites():
    with (BASE / "original_21_land_grid_sites.csv").open(newline="", encoding="utf-8") as h:
        sites = list(csv.DictReader(h))
    if len(sites) != 21 or len({r["cell_id"] for r in sites}) != 21:
        raise ValueError("HOLD_ORIGINAL_LAND_GRID_ROSTER")
    for row in sites:
        row["latitude"] = float(row["latitude"])
        row["longitude"] = float(row["longitude"])
    return sites


def require_source_structure(new, old, sites, hemisphere):
    if (new.get("id") != "GLOBAL_GRID_EQUINOX_15_30_DAY_ERA5_SEASON_HISTORY_V0"
        or new.get("hemisphere") != hemisphere
        or len(new.get("batches", [])) != 6
        or old.get("hemisphere") != hemisphere
        or len(old.get("batches", [])) != 6
        or new.get("original_site_order") !=
            [[site["latitude"],site["longitude"]] for site in sites]
        or old.get("original_site_order") != new.get("original_site_order")):
        raise ValueError("HOLD_SOURCE_SITE_HEMISPHERE_OR_DATE_ROSTER_CHANGED")
    for i, (source_batch, baseline) in enumerate(zip(new["batches"], old["batches"])):
        if (source_batch["id"] != baseline["id"]
            or source_batch["date"] != baseline["date"]
            or len(source_batch["original_response"]) != len(sites)
            or len(baseline["original_response"]) != len(sites)):
            raise ValueError("HOLD_ORIGINAL_SIX_BATCH_ORDER_OR_DATE_CHANGED")
        end = date.fromisoformat(source_batch["date"])
        begin = end - timedelta(days=29)
        if source_batch["start_date"] != begin.isoformat():
            raise ValueError("HOLD_30DAY_TRAILING_START_CHANGED")
        for j, site in enumerate(sites):
            src = source_batch["original_response"][j]
            oldsite = baseline["original_response"][j]
            for one in (src,oldsite):
                if (abs(one["latitude"]-site["latitude"]) > .4
                    or abs(one["longitude"]-site["longitude"]) > .4
                    or not one.get("timezone")):
                    raise ValueError("HOLD_ORIGINAL_ERA5_SELECTED_GRID_OR_TIMEZONE")
            if (abs(src["latitude"]-oldsite["latitude"]) > 1e-9
                or abs(src["longitude"]-oldsite["longitude"]) > 1e-9
                or src["timezone"] != oldsite["timezone"]):
                raise ValueError("HOLD_SOURCE_ORIGINAL_GRID_TIMEZONE_DRIFT")
            ds = src.get("daily",{})
            if len(ds.get("time",[])) != 30:
                raise ValueError("HOLD_SOURCE_NOT_EXACT_30DAY_CALENDAR")
            if ds["time"] != [(begin+timedelta(days=k)).isoformat() for k in range(30)]:
                raise ValueError("HOLD_SOURCE_NONCONSECUTIVE_OR_DUPLICATE_DATE")
            units = src.get("daily_units",{})
            expected_units = ("°C","°C","m³/m³","mm")
            for field, unit in zip(FIELDS, expected_units):
                if units.get(field) != unit or len(ds.get(field, [])) != 30:
                    raise ValueError("HOLD_SOURCE_FIELD_OR_UNIT_DRIFT_"+field)
            baseline_daily=oldsite["daily"]
            if baseline_daily.get("time") != [source_batch["date"]]:
                raise ValueError("HOLD_ONE_DAY_ENDPOINT_DATE_DRIFT")
            for field in FIELDS[:3]:
                x=ds[field][-1]
                y=baseline_daily[field][0]
                # A future ERA5 revision is a NEW source, not a silent refit.
                if (not isinstance(x,(int,float)) or not isinstance(y,(int,float))
                    or not math.isfinite(x) or not math.isfinite(y)
                    or abs(x-y) > 1e-9):
                    raise ValueError("HOLD_ORIGINAL_ONE_DAY_ERA5_NUMERIC_DRIFT")
    return True


def validated_window(packet, window):
    """One 15/30d source span; null/physically bad means full branch HOLD."""
    if window not in WINDOWS:
        raise ValueError("HOLD_UNREGISTERED_TIME_WINDOW")
    start=30-window
    values={field:packet["daily"][field][start:] for field in FIELDS}
    for index in range(window):
        day=packet["daily"]["time"][start+index]
        v=[values[field][index] for field in FIELDS]
        if any(isinstance(x,bool) or not isinstance(x,(int,float))
               or not math.isfinite(x) for x in v):
            raise ValueError("HOLD_NONFINITE_DAILY_SOURCE_"+day)
        if v[1]<v[0]:
            raise ValueError("HOLD_TMAX_BELOW_TMEAN_"+day)
        if not 0<=v[2]<=1:
            raise ValueError("HOLD_PHYSICALLY_INVALID_SOIL_"+day)
        if v[3]<0:
            raise ValueError("HOLD_NEGATIVE_DAILY_PRECIP_"+day)
    return {
        "mean_t2m_C":mean(values["temperature_2m_mean"]),
        "mean_tmax_C":mean(values["temperature_2m_max"]),
        "mean_soil_m3m3":mean(values["soil_moisture_0_to_7cm_mean"]),
        "total_precip_mm":sum(values["precipitation_sum"]),
    }


def make_row(site, cycle, hemisphere, window, rising, falling, old):
    row={
        "cell_id":site["cell_id"],"latitude":site["latitude"],
        "longitude":site["longitude"],"map_label":site["map_label"],
        "continent":site["continent"],"hemisphere":hemisphere,
        "cycle":cycle,"trailing_window_days":window,
        "rising_endpoint":rising["daily"]["time"][-1],
        "falling_endpoint":falling["daily"]["time"][-1],
        "old_one_day_source_status":old["status"],
        "old_one_day_delta_tmean_C":old["delta_tmean_C"],
        "old_one_day_delta_soil_m3m3":old["delta_soil_m3m3"],
        "old_one_day_opposite":old["opposite_tmean_soil_sign"],
        "status":"HOLD_NOT_CALCULATED",
        "delta_tmean_C":None,
        "delta_tmax_C":None,
        "delta_soil_m3m3":None,
        "delta_precip_window_mm":None,
        "temperature_and_soil_opposite":None,
        "temperature_and_soil_category":None,
        "precipitation_soil_opposite":None,
    }
    try:
        u=validated_window(rising,window)
        f=validated_window(falling,window)
        t=f["mean_t2m_C"]-u["mean_t2m_C"]
        moisture=f["mean_soil_m3m3"]-u["mean_soil_m3m3"]
        rain=f["total_precip_mm"]-u["total_precip_mm"]
        if t>0 and moisture<0:category="warmer_drier"
        elif t<0 and moisture>0:category="cooler_wetter"
        elif t>0 and moisture>0:category="warmer_wetter"
        elif t<0 and moisture<0:category="cooler_drier"
        else:category="zero_or_unpaired_direction"
        row.update(
            status="VERIFIED_ERA5_HISTORICAL_WINDOW",
            delta_tmean_C=t,
            delta_tmax_C=f["mean_tmax_C"]-u["mean_tmax_C"],
            delta_soil_m3m3=moisture,
            delta_precip_window_mm=rain,
            temperature_and_soil_opposite=(t*moisture<0),
            temperature_and_soil_category=category,
            precipitation_soil_opposite=(rain*moisture<0),
        )
    except ValueError as exc:
        row["status"]=str(exc) if str(exc).startswith("HOLD_") else "HOLD_SOURCE_VALIDATION_ERROR"
    return row


def report(rows, original):
    result={
        "science":"Fixed 21-site ERA5 equal-photoperiod-ENDPOINT trailing climate-history pilot",
        "status":"EXPLORATORY_EXTERNAL_REANALYSIS_CLIMATE_HISTORY_NOT_ANIMAL",
        "n_original_sites":21,"original_site_cycles":63,
        "original_one_day_admitted":62,
        "original_one_day_temperature_soil_opposite":29,
        "windows":{},
        "historical_comparison":{},
        "limits":{
            "center_date_photoperiod_only":True,
            "not_equal_daily_photoperiod_throughout_trailing_windows":True,
            "not_global_land_area_weighted":True,
            "not_animal_behavior_or_foraging_causality":True,
            "source_water_and_weather_both_ERA5_not_independent_field_measurement":True,
            "no_source_outlier_clipping_or_imputation":True,
        }
    }
    old_map={(a["cell_id"],a["cycle"]):a for a in original}
    new_maps={}
    for width in WINDOWS:
        data=[r for r in rows if r["trailing_window_days"]==width]
        valid=[r for r in data if r["status"]=="VERIFIED_ERA5_HISTORICAL_WINDOW"]
        site=defaultdict(list)
        for r in valid:site[r["cell_id"]].append(r)
        complete=[v for v in site.values() if len(v)==3]
        cat=defaultdict(int)
        for r in valid:cat[r["temperature_and_soil_category"]]+=1
        # Same site-year original day-1 and multiweek compared ONLY when both qualified.
        matched=[r for r in valid if old_map[(r["cell_id"],r["cycle"])]["status"]=="VERIFIED_REANALYSIS_PAIR"]
        oldyes=sum(old_map[(r["cell_id"],r["cycle"])]["opposite_tmean_soil_sign"] for r in matched)
        keep=sum(old_map[(r["cell_id"],r["cycle"])]["opposite_tmean_soil_sign"] and r["temperature_and_soil_opposite"] for r in matched)
        gain=sum(not old_map[(r["cell_id"],r["cycle"])]["opposite_tmean_soil_sign"] and r["temperature_and_soil_opposite"] for r in matched)
        flipT=sum((old_map[(r["cell_id"],r["cycle"])]["delta_tmean_C"] * r["delta_tmean_C"])<0 for r in matched)
        flipS=sum((old_map[(r["cell_id"],r["cycle"])]["delta_soil_m3m3"] * r["delta_soil_m3m3"])<0 for r in matched)
        result["windows"][str(width)]={
            "original_site_cycles":len(data),
            "source_admitted_site_cycles":len(valid),
            "unavailable_pairs":[{"cell_id":r["cell_id"],"cycle":r["cycle"],"reason":r["status"]} for r in data if r["status"]!="VERIFIED_ERA5_HISTORICAL_WINDOW"],
            "hydrothermal_direction_categories":dict(cat),
            "opposite_temp_soil_sign_count":sum(r["temperature_and_soil_opposite"] for r in valid),
            "precipitation_and_surface_soil_water_opposite_sign_count":sum(r["precipitation_soil_opposite"] for r in valid),
            "temp_C":desc([r["delta_tmean_C"] for r in valid]),
            "moisture_m3m3":desc([r["delta_soil_m3m3"] for r in valid]),
            "precipitation_mm":desc([r["delta_precip_window_mm"] for r in valid]),
            "sites_with_complete_three_years":len(complete),
            "site_complete_three_years_all_opposed":sum(all(r["temperature_and_soil_opposite"] for r in v) for v in complete),
            "site_complete_three_years_mean_opposed":sum(mean(x["delta_tmean_C"] for x in v)*mean(x["delta_soil_m3m3"] for x in v)<0 for v in complete),
            "sites_with_any_admitted_years":len(site),
            "matched_to_original_valid_one_day":len(matched),
            "old_one_day_opposed_on_common_support":oldyes,
            "opposite_retained_from_original_one_day":keep,
            "opposite_newly_present_in_window":gain,
            "one_day_temperature_sign_changed":flipT,
            "one_day_soil_water_sign_changed":flipS,
        }
        new_maps[width]={(r["cell_id"],r["cycle"]):r for r in valid}
    common=set(new_maps[15]) & set(new_maps[30])
    result["historical_comparison"]={
        "both_15_and_30_good":len(common),
        "both_opposite":sum(new_maps[15][k]["temperature_and_soil_opposite"] and new_maps[30][k]["temperature_and_soil_opposite"] for k in common),
        "opposite_15_not_30":sum(new_maps[15][k]["temperature_and_soil_opposite"] and not new_maps[30][k]["temperature_and_soil_opposite"] for k in common),
        "opposite_30_not_15":sum(not new_maps[15][k]["temperature_and_soil_opposite"] and new_maps[30][k]["temperature_and_soil_opposite"] for k in common),
    }
    return result


def compute():
    one_day, orig= replay_original_one_day()
    if (len(one_day)!=63 or orig["verified_pairs"]!=ORIGINAL_1DAY_VALID_PAIRS
        or orig["opposite_temperature_soil_sign_pairs"]!=ORIGINAL_1DAY_OPPOSITE):
        raise ValueError("HOLD_FIRST_ORIGINAL_ERA5_RESULT_NOT_REPLAYED")
    oldmap={(r["cell_id"],r["cycle"]):r for r in one_day}
    site_list=load_sites()
    new_rows=[]
    source_shas={}
    for hemisphere in ("south","north"):
        name="southern" if hemisphere=="south" else "northern"
        group=[s for s in site_list if (s["latitude"]<0)==(hemisphere=="south")]
        new_path=BASE/f"era5_{name}_30day_six_original_batches_v0.json"
        old_path=BASE/f"era5_{name}_6batches_original_source.json"
        raw=new_path.read_bytes()
        source_shas[hemisphere]=hashlib.sha256(raw).hexdigest()
        new=json.loads(raw)
        old=json.loads(old_path.read_text(encoding="utf-8"))
        require_source_structure(new,old,group,hemisphere)
        for cycle,(date_u,date_f) in enumerate(DATES[hemisphere],start=2018):
            for i,site in enumerate(group):
                u=new["batches"][(cycle-2018)*2]["original_response"][i]
                f=new["batches"][(cycle-2018)*2+1]["original_response"][i]
                if (u["daily"]["time"][-1],f["daily"]["time"][-1])!=(date_u,date_f):
                    raise ValueError("HOLD_ORIGINAL_SOLAR_END_DATE")
                oldrow=oldmap[(site["cell_id"],cycle)]
                for width in WINDOWS:
                    new_rows.append(make_row(site,cycle,hemisphere,width,u,f,oldrow))
    if len(new_rows)!=126 or len({(r["cell_id"],r["cycle"],r["trailing_window_days"]) for r in new_rows})!=126:
        raise ValueError("HOLD_ORIGINAL_63_PAIRS_TWO_WINDOWS")
    summary=report(new_rows,one_day)
    summary["original_30day_source_sha256"]=source_shas
    summary["original_one_day_workflow"]="https://github.com/zuizui0223/odsp/actions/runs/39201993065"
    return new_rows,summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,default=Path(__file__).resolve().parents[1]/"results")
    args=p.parse_args()
    data,s=compute()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    with (args.output_dir/"global_grid_ERA5_15_30day_history_126sitecycles.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(data[0]))
        writer.writeheader();writer.writerows(data)
    (args.output_dir/"global_grid_ERA5_15_30day_source_history_summary.json").write_text(
        json.dumps(s,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":s["status"],
        "W15":{k:s["windows"]["15"][k] for k in ("source_admitted_site_cycles","opposite_temp_soil_sign_count","sites_with_complete_three_years","site_complete_three_years_all_opposed","opposite_retained_from_original_one_day")},
        "W30":{k:s["windows"]["30"][k] for k in ("source_admitted_site_cycles","opposite_temp_soil_sign_count","sites_with_complete_three_years","site_complete_three_years_all_opposed","opposite_retained_from_original_one_day")},
        "comparison":s["historical_comparison"]},sort_keys=True))
if __name__=="__main__":
    main()
