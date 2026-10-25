#!/usr/bin/env python3
"""Exploratory original-pinned Serengeti PHOTO RECORD x coarse regional ERA5 date alignment.

This is a separately declared AFTER-pool-outcome, AFTER-weather-outcome source
reanalysis. All taxa, dates, signs, zeros and source caveats retained. No source
station ids, coordinates or animal/photo timestamps exported. Three solstice
cycles are NOT climate iid replicates. See research/...ALIGNMENT_V0_CONTRACT.json.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

from pyproj import Transformer
from scripts.run_serengeti_source_recorded_solar_season_v0 import (
    CONSENSUS_MD5, CERTAINTY_MIN, EXCLUDED, INDEPENDENCE_MINUTES,
    DAYLENGTH_MISMATCH_MAX_MINUTES, _mh, colmap, key,
    load_effort, md5_file, parse_timestamp, run as original_run,
    solar_boundaries, tax_norm, zone
)
from scripts.run_serengeti_era5_environment_v0 import (
    fetch as fetch_era5, verify_source, run as weather_only,
    SOURCE_URL as ERA5_API
)

EXPECTED_ORIGINAL_JSON_SHA256 = "0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3"
EXPECTED_ERA5_DAILY_SERIES_SHA256 = "aaa93eec1ac0fab3315bfc712020970746d47cd1d407b8a7778243b2f627bee7"
PREDECLARED_CYCLES = (2010, 2011, 2012)
PREDECLARED_FOCAL = ("hyenaSpotted", "lionFemale", "zebra", "buffalo", "gazelleThomsons")

def original_first_receipt_verified(consensus:Path,effort:Path)->dict:
    o=original_run(consensus,effort)
    content=(json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()
    digest=hashlib.sha256(content).hexdigest()
    if digest != EXPECTED_ORIGINAL_JSON_SHA256:
        raise ValueError("HOLD_ORIGINAL_FROZEN_V0_POOLED_RECEIPT_NOT_REPRODUCED")
    if (o["source"]["retained_events_on_solar_matched_source_date_pairs"] != 38792
        or o["source_site_support"]["accepted_solar_matched_site_day_pairs"] != 24290
        or len(o["taxa"]) != 43):
        raise ValueError("HOLD_ORIGINAL_POOLED_SOURCE_COUNT_DRIFT")
    return o

def environmental_source_verified(payload:dict,digest:str)->dict[str,dict[str,float]]:
    result=weather_only(payload,digest)
    if result["source_daily_arrays_sha256"] != EXPECTED_ERA5_DAILY_SERIES_SHA256:
        raise ValueError("HOLD_ERA5_SOURCE_DAILY_ARRAYS_NOT_FROZEN")
    return verify_source(payload)

def tmax_precip30_change(grid,rising:dt.date,falling:dt.date)->tuple[float,float]:
    def rain30(day:dt.date)->float:
        return sum(grid[(day-dt.timedelta(days=k)).isoformat()]["precipitation_sum"] for k in range(30))
    a=grid[rising.isoformat()]
    b=grid[falling.isoformat()]
    return (b["temperature_2m_max"] - a["temperature_2m_max"],
            rain30(falling)-rain30(rising))

def raw_source_data(consensus:Path, eligible_sites:set[str]):
    coords={}
    conflicts=set()
    obs=[]
    with consensus.open(newline="",encoding="utf-8-sig") as h:
        reader=csv.DictReader(h)
        cols=colmap(reader.fieldnames)
        for required in ("SiteID","Species","DateTime","NumVotes","NumClassifications","LocationX","LocationY"):
            key(cols,required)
        for row in reader:
            site=row[key(cols,"SiteID")].strip()
            if site not in eligible_sites: continue
            try:
                east=float(row[key(cols,"LocationX")])
                north=float(row[key(cols,"LocationY")])
                if not (math.isfinite(east) and math.isfinite(north)): raise ValueError()
                prev=coords.get(site)
                if prev and math.hypot(east-prev[0],north-prev[1])>500:
                    conflicts.add(site)
                elif prev is None:
                    coords[site]=(east,north)
            except (ValueError,TypeError): pass
            try:
                instant=parse_timestamp(row[key(cols,"DateTime")])
                species=row[key(cols,"Species")].strip()
                votes=float(row[key(cols,"NumVotes")])
                nclass=float(row[key(cols,"NumClassifications")])
            except (ValueError,TypeError,KeyError):
                continue
            if not species or nclass<=0 or votes/nclass<CERTAINTY_MIN or tax_norm(species) in EXCLUDED:
                continue
            obs.append((site,species,instant))
    converter=Transformer.from_crs("EPSG:21036","EPSG:4326",always_xy=True)
    geos={}
    for site,(east,north) in coords.items():
        if site in conflicts: continue
        lon,lat=converter.transform(east,north)
        if (-6<=lat<=3 and 31<=lon<=38 and math.isfinite(lat) and math.isfinite(lon)):
            geos[site]=(lat,lon)
    if len(geos)!=186:
        raise ValueError("HOLD_V0_PHYSICAL_SITE_GEOMETRY_NOT_REPRODUCED")
    return geos, sorted(obs,key=lambda x:(x[0],x[1],x[2]))

def source_eligible_site_date_map(cycles,geos,weather_grid):
    eligible={}
    env_by_year=defaultdict(lambda: {"temperature":[],"rain30":[],"sites":set()})
    for site,by_year in cycles.items():
        if site not in geos: continue
        lat,lon=geos[site]
        for year,pairs in by_year.items():
            for rising,falling in pairs:
                _,_,u=solar_boundaries(rising,lat,lon)
                _,_,v=solar_boundaries(falling,lat,lon)
                if abs(u-v)>DAYLENGTH_MISMATCH_MAX_MINUTES:
                    continue
                eligible[(site,rising)]=(year,"rising")
                eligible[(site,falling)]=(year,"falling")
                if year in PREDECLARED_CYCLES:
                    if rising.isoformat() not in weather_grid or falling.isoformat() not in weather_grid:
                        raise ValueError("HOLD_ERA5_MISSING_ORIGINAL_SITE_PAIR_DAY")
                    tm,rain=tmax_precip30_change(weather_grid,rising,falling)
                    env_by_year[year]["temperature"].append(tm)
                    env_by_year[year]["rain30"].append(rain)
                    env_by_year[year]["sites"].add(site)
    if len(env_by_year) != len(PREDECLARED_CYCLES):
        raise ValueError("HOLD_SOURCE_YEAR_CYCLE_NOT_SUPPORTED")
    return eligible,env_by_year

def mh_by_year(site_counts:dict,year:int):
    taxa_counts=defaultdict(Counter)
    strat_edge=[]
    strat_night=[]
    both=0
    sites=set()
    for site,yr in sorted({(site,yr) for site,yr,b in site_counts if yr==year}):
        rising=site_counts.get((site,yr,"rising"),Counter())
        falling=site_counts.get((site,yr,"falling"),Counter())
        taxa_counts["rising"].update(rising)
        taxa_counts["falling"].update(falling)
        sites.add(site)
        if sum(rising.values())>0 and sum(falling.values())>0:
            both+=1
        strat_edge.append((site,falling["edge"],falling["core"],rising["edge"],rising["core"]))
        strat_night.append((site,falling["night"],falling["core"]+falling["edge"],
                           rising["night"],rising["core"]+rising["edge"]))
    rise=taxa_counts["rising"];fall=taxa_counts["falling"]
    return {
        "events_rising":int(sum(rise.values())),"events_falling":int(sum(fall.values())),
        "source_site_codes_with_any_species_records":len(sites),
        "sites_with_species_detections_on_both_branches":both,
        "photographed_time_zone_counts_rising":{k:int(rise[k]) for k in ("core","edge","night")},
        "photographed_time_zone_counts_falling":{k:int(fall[k]) for k in ("core","edge","night")},
        "site_stratified_recorded_edge_core_OR":_mh(strat_edge),
        "site_stratified_recorded_night_day_OR":_mh(strat_night),
    }

def analyze(consensus:Path,effort:Path,weather:dict,weather_digest:str="NO_TRANSPORT_SHA")->dict:
    if md5_file(consensus)!=CONSENSUS_MD5:
        raise ValueError("HOLD_ORIGINAL_CAMERA_SOURCE_DIGEST")
    first=original_first_receipt_verified(consensus,effort)
    grid=environmental_source_verified(weather,weather_digest)
    cycles,_=load_effort(effort)
    geos,events=raw_source_data(consensus,set(cycles))
    elig,climate=source_eligible_site_date_map(cycles,geos,grid)
    if len(elig)<20000: raise ValueError("HOLD_SOURCE_DATE_MAP_TOO_SMALL")
    counts=defaultdict(lambda:defaultdict(Counter))
    last={}
    count_events=0
    for site,species,instant in events:
        key0=(site,species)
        if key0 in last and instant-last[key0]<dt.timedelta(minutes=INDEPENDENCE_MINUTES):
            continue
        last[key0]=instant
        p=elig.get((site,instant.date()))
        if p is None:continue
        year,branch=p
        count_events+=1
        if year not in PREDECLARED_CYCLES:continue
        counts[species][(site,year,branch)][zone(instant,*geos[site])]+=1

    if count_events != first["source"]["retained_events_on_solar_matched_source_date_pairs"]:
        raise ValueError("HOLD_FIRST_SOURCE_REPLAY_DEDUP_EVENT_DRIFT")
    all_taxa=[x["species"] for x in first["taxa"]]
    new_taxa=[{
        "source_taxon":name,
        "cycles":{
            str(y):mh_by_year(counts.get(name,{}),y) for y in PREDECLARED_CYCLES
        },
    } for name in all_taxa]
    year_context=[]
    for year in PREDECLARED_CYCLES:
        obs=climate[year]
        if not obs["temperature"] or len(obs["temperature"])!=len(obs["rain30"]):
            raise ValueError("HOLD_SOURCE_PAIR_EXPOSURE_MISSING")
        year_context.append({
            "solstice_cycle_year":year,
            "eligible_site_daylength_matched_date_pairs":len(obs["temperature"]),
            "independent_source_camera_station_ID_count":len(obs["sites"]),
            "temperature_max_falling_minus_rising_C_mean":sum(obs["temperature"])/len(obs["temperature"]),
            "precipitation_30day_falling_minus_rising_mm_mean":sum(obs["rain30"])/len(obs["rain30"]),
            "regional_climate_cell_count":1,
            "date_pairs_are_not_independent_climate_samples":True
        })
    return {
        "status":"EXPLORATORY_PHOTO_TIME_BY_CYCLE_LINKED_TO_COARSE_REGIONAL_ERA5_CONTEXT",
        "animal_source_first_result_sha256":EXPECTED_ORIGINAL_JSON_SHA256,
        "weather_source_daily_sha256":EXPECTED_ERA5_DAILY_SERIES_SHA256,
        "matched_original_animals_replayed_count":count_events,
        "photo_time_matched_source_sites":len(geos),
        "year_context":year_context,
        "all_43_original_taxon_labels":new_taxa,
        "five_preselected_after_old_pool_result_taxa":list(PREDECLARED_FOCAL),
        "no_camera_site_ids_exact_GPS_or_event_dates_exported":True,
        "same_site_year_photos_are_not_animal_independence_evidence":True,
        "hourly_camera_power_OR_detector_q_qualified":False,
        "independent_ecosystem_generalization_or_causal_thermal_effect_qualified":False,
        "climate_year_count":len(PREDECLARED_CYCLES),
        "climate_years_not_independent_regions":True,
        "claim":"Descriptive joint observation only, no yearwise model slope, p-value, or biological thermal causation."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--consensus",required=True,type=Path)
    p.add_argument("--effort",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    try:
        climate,digest=fetch_era5()
        result=analyze(args.consensus,args.effort,climate,digest)
    except (OSError,KeyError,ValueError,TypeError,IndexError) as exc:
        result={
            "status":"HOLD_SOURCE_REPLAY_CLIMATE_ALIGNMENT_FAILED",
            "exception_type":type(exc).__name__,
            "ecological_conclusion":None
        }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    show={
        "status":result["status"],
        "original_camera_event_count":result.get("matched_original_animals_replayed_count"),
        "year_weather_context":result.get("year_context"),
        "taxa":[
            row for row in result.get("all_43_original_taxon_labels",[])
            if row["source_taxon"] in PREDECLARED_FOCAL
        ],
        "latent_behavior":False
    }
    print(json.dumps(show,sort_keys=True))
    if result["status"].startswith("HOLD"):raise SystemExit(2)

if __name__=="__main__":
    main()
