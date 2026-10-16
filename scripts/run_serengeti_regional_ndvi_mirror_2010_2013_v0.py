#!/usr/bin/env python3
"""First public-area MOD13Q1 Terra 2010–13 QUALITY-SCREENED NDVI season mirror.

Independent NASA satellite outcome only. Photo animal records NOT read. One
regional coarse site fixed before greenness results, never source cameras.
Each satellite scene uses 3x3 raw raster NDVI and pixel QA==0 ONLY. No cloud
gap filling, future-dated composite exposure or outcome-driven pair selection.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from datetime import date, timedelta
import hashlib
import json
import math
from pathlib import Path
import statistics
from urllib.parse import urlencode
import urllib.error

from scripts.probe_serengeti_mod13q1_ndvi_cog_v0 import (
    api_json, NDVI_ASSET, QA_ASSET, NDVI_SCALE,
    sign_public_blob, raster3x3
)
from scripts.run_serengeti_era5_environment_v0 import calendar_pairs

COLLECTION="modis-13Q1-061"
ENDPOINT="https://planetarycomputer.microsoft.com/api/stac/v1/search"
DATE_QUERY_START="2010-01-01T00:00:00Z"
DATE_QUERY_END="2013-07-16T23:59:59Z"
PUBLIC_BBOX="34.73,-2.52,34.77,-2.48"
DATE_PAIRS_COUNT=522
PAIR_COVERAGE_MIN=.60
MAX_SCENE_AGE=20
MAX_TERRA_SCENES=150
MAX_STAC_PAGES=6
STAC_LIMIT=50
PRIMARY_MODIS_PLATFORM="terra"

def source_scene_from_stac(raw):
    p=raw.get("properties",{})
    if p.get("platform")!=PRIMARY_MODIS_PLATFORM: return None
    itemid=raw.get("id","")
    if not itemid.startswith("MOD13Q1.") or raw.get("collection")!=COLLECTION:
        raise ValueError("HOLD_MODIS_TERRA_SOURCE_ID_OR_COLLECTION")
    start=p.get("start_datetime","")[:10]
    end=p.get("end_datetime","")[:10]
    try: start_date=date.fromisoformat(start);end_date=date.fromisoformat(end)
    except ValueError: raise ValueError("HOLD_MODIS_COMPOSITE_DATE_PARSE")
    if end_date<start_date or (end_date-start_date).days>17:
        raise ValueError("HOLD_MODIS_UNEXPECTED_COMPOSITE_DURATION")
    assets=raw.get("assets",{})
    if NDVI_ASSET not in assets or QA_ASSET not in assets:
        raise ValueError("HOLD_NDVI_QA_ASSETS_ABSENT")
    ndvi=assets[NDVI_ASSET]
    b=ndvi.get("raster:bands",[{}])[0]
    if float(b.get("scale",-1))!=NDVI_SCALE:
        raise ValueError("HOLD_NDVI_STAC_SCALE_MISMATCH")
    for name in (NDVI_ASSET,QA_ASSET):
        if not assets[name]["href"].startswith(
            "https://modiseuwest.blob.core.windows.net/modis-061-cogs/MOD13Q1/"
        ):
            raise ValueError("HOLD_WRONG_COG_SOURCE")
    return {
        "source_item":itemid,"start_date":start,"end_date":end,
        "ndvi_asset":ndvi["href"],"qa_asset":assets[QA_ASSET]["href"]
    }

def fetch_all_stac_terra_scenes():
    first=ENDPOINT+"?"+urlencode({
        "bbox":PUBLIC_BBOX,
        "collections":COLLECTION,
        "datetime":DATE_QUERY_START+"/"+DATE_QUERY_END,
        "limit":STAC_LIMIT
    })
    current=first
    pages=0
    scenes={}
    while current:
        pages+=1
        if pages>MAX_STAC_PAGES:
            raise ValueError("HOLD_MODIS_STAC_PAGINATION_OVER_LIMIT")
        data=api_json(current)
        if data.get("type")!="FeatureCollection":
            raise ValueError("HOLD_MODIS_STAC_NOT_FEATURE_COLLECTION")
        for raw in data.get("features",[]):
            scene=source_scene_from_stac(raw)
            if scene is None:continue
            if scene["start_date"] in scenes and scene["source_item"]!=scenes[scene["start_date"]]["source_item"]:
                raise ValueError("HOLD_DUPLICATE_TERRA_COMPOSITE_START_DATE")
            scenes[scene["start_date"]]=scene
        nexts=[x.get("href") for x in data.get("links",[]) if x.get("rel")=="next"]
        current=nexts[0] if nexts else None
        if current and not current.startswith("https://planetarycomputer.microsoft.com/api/stac/v1/"):
            raise ValueError("HOLD_MODIS_STAC_UNTRUSTED_NEXT_LINK")
    values=sorted(scenes.values(),key=lambda d:d["end_date"])
    if not 55<=len(values)<=MAX_TERRA_SCENES:
        raise ValueError("HOLD_MODIS_TERRA_SCENE_COUNT_UNEXPECTED")
    dates=[date.fromisoformat(x["start_date"]) for x in values]
    if any((b-a).days>20 for a,b in zip(dates,dates[1:])):
        raise ValueError("HOLD_MISSING_TERRA_COMPOSITES_OVER_TWENTY_DAYS")
    return values,pages

def read_scene(scene):
    try:
        ndvi=sign_public_blob(scene["ndvi_asset"])
        qa=sign_public_blob(scene["qa_asset"])
        result=raster3x3(ndvi,qa)
        return {
            "source_item":scene["source_item"],
            "start_date":scene["start_date"],
            "end_date":scene["end_date"],
            "status":result["status"],
            "good_pixels":result["qa_good_reliability0_raw_valid_pixels"],
            "marginal_pixels_not_used":result["qa_marginal_reliability1_pixel_count"],
            "cloud_pixels":result["qa_cloudy3_pixel_count"],
            "snow_pixels":result["qa_snow2_pixel_count"],
            "good_only_NDVI":result["primary_good_only_median_NDVI"],
        }
    except (OSError,ValueError,TypeError,KeyError,IndexError,urllib.error.URLError) as exc:
        return {
            "source_item":scene["source_item"],
            "start_date":scene["start_date"],
            "end_date":scene["end_date"],
            "status":"HOLD_SCENE_COG_OR_QA_SOURCE_UNAVAILABLE",
            "error_type":type(exc).__name__,
            "good_only_NDVI":None,
        }

def past_completed_qualified_ndvi(composites:list, date_target:date):
    ends=[date.fromisoformat(scene["end_date"]) for scene in composites]
    idx=bisect_right(ends,date_target)-1
    if idx<0:return None
    scene=composites[idx]
    if (date_target-ends[idx]).days>MAX_SCENE_AGE:return None
    # CRITICAL: Do not use older 'good' scene if the most recent source scene is cloudy.
    return scene.get("good_only_NDVI",None)

def quantile(xs,q):
    vs=sorted(xs)
    i=(len(vs)-1)*q
    n=int(i)
    return vs[n]+(vs[min(n+1,len(vs)-1)]-vs[n])*(i-n)

def summary_of_deltas(d):
    if not d:return None
    return {
        "n":len(d),
        "mean":statistics.mean(d),
        "median":statistics.median(d),
        "p10":quantile(d,.1),
        "p90":quantile(d,.9),
        "fraction_positive":sum(x>0 for x in d)/len(d),
        "fraction_negative":sum(x<0 for x in d)/len(d)
    }

def apply_frozen_522_mirror_pairs(composites:list):
    all_pairs=calendar_pairs()
    if len(all_pairs)!=DATE_PAIRS_COUNT:
        raise ValueError("FROZEN_SOLSTICE_MIRROR_COUNT_MISMATCH")
    peryear={y:[] for y in (2010,2011,2012)}
    for year,up,down in all_pairs:
        x=past_completed_qualified_ndvi(composites,date.fromisoformat(up))
        y=past_completed_qualified_ndvi(composites,date.fromisoformat(down))
        if x is not None and y is not None:
            peryear[year].append(y-x)
    rows=[]
    every=[]
    for year in (2010,2011,2012):
        d=peryear[year]
        every.extend(d)
        sufficient=len(d)>=PAIR_COVERAGE_MIN*174
        rows.append({
            "year":year,
            "total_original_fixed_photoperiod_mirrors":174,
            "paired_ndvi_good_observations":len(d),
            "paired_observation_fraction":len(d)/174,
            "qualifies_for_regional_descriptive_mean":sufficient,
            "delta_falling_minus_rising_good_NDVI":
                summary_of_deltas(d) if sufficient else None,
            "insufficient_qa_year_raw_deltas_not_inferred":not sufficient
        })
    eligible_years=[y for y in rows if y["qualifies_for_regional_descriptive_mean"]]
    return {
        "yearwise":rows,
        "full_522_calendar_pair_qualified_good_observation_count":len(every),
        "per_pair_ndvi_coverage_frac":len(every)/DATE_PAIRS_COUNT,
        "descriptive_all_years_available_pair_summary":
            summary_of_deltas(every) if len(eligible_years)==3 else None,
        "three_years_coverage_qualified":len(eligible_years)==3
    }

def run():
    scenes,pages=fetch_all_stac_terra_scenes()
    received=[read_scene(s) for s in scenes]
    composites=sorted(received,key=lambda x:x["end_date"])
    context=apply_frozen_522_mirror_pairs(composites)
    qa_pass=sum(scene.get("good_only_NDVI") is not None for scene in composites)
    status=("REGIONAL_QUALITY_FILTERED_NDVI_ALL_THREE_YEARS"
            if context["three_years_coverage_qualified"]
            else "REGIONAL_NDVI_AVAILABLE_BUT_INSUFFICIENT_ANNUAL_QA_COVERAGE")
    return {
        "status":status,
        "satellite_source":"NASA MOD13Q1 v061 Terra 16day NDVI COGs",
        "satellite_product_doi":"10.5067/MODIS/MOD13Q1.061",
        "source_STAC_collection":COLLECTION,
        "source_STAC_query":ENDPOINT+"?"+urlencode({
           "bbox":PUBLIC_BBOX,"collections":COLLECTION,
           "datetime":DATE_QUERY_START+"/"+DATE_QUERY_END,
           "limit":STAC_LIMIT
        }),
        "source_STAC_pages":pages,
        "original_source_Terra_composite_scenes":len(composites),
        "source_scenes_with_at_least_6_good_250m_pixels":qa_pass,
        "source_scenes_without_primary_qualified_NDVI":len(composites)-qa_pass,
        "original_source_scene_status_and_good_only_median":composites,
        "season_mirror":context,
        "public_regional_point":[-2.5,34.75],
        "camera_GPS_or_animal_events_read":False,
        "NDVI_forage_amount_or_animal_behavior_estimated":False,
        "daily_greenness_interpolation_performed":False,
        "seasonal_datepair_selection_redefined":False,
        "no_statistical_independent_climate_p":True
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    try:
        result=run()
    except (OSError,ValueError,TypeError,KeyError,IndexError) as e:
        result={
            "status":"HOLD_REGIONAL_NDVI_SCENE_SOURCE_OR_CALENDAR_FAILURE",
            "exception_type":type(e).__name__,
            "NDVI_or_animal_conclusion_fabricated":False
        }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "status":result["status"],
        "terra_composites":result.get("original_source_Terra_composite_scenes"),
        "good_composites":result.get("source_scenes_with_at_least_6_good_250m_pixels"),
        "years":result.get("season_mirror",{}).get("yearwise"),
        "three_years_qa":result.get("season_mirror",{}).get("three_years_coverage_qualified"),
        "no_animal_activity_estimated":True
    },sort_keys=True))
    if result["status"].startswith("HOLD"):raise SystemExit(2)

if __name__=="__main__":main()
