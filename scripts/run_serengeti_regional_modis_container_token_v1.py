#!/usr/bin/env python3
"""MOD13Q1 Terra 2010–13 real 16-day satellite NDVI public container SAS read.

v1 changes SOURCE ACCESS mechanism ONLY after documented first v0 source-access
HOLD; preserve previous v0 receipts, original 83 source scenes, 522 solar
mirror dates and all quality rules. The first verified NDVI=0.5484 scene
must replay BEFORE other sources are read. No animal/camera data opened.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import urllib.error
from scripts.probe_serengeti_mod13q1_ndvi_cog_v0 import (
    api_json, raster3x3, verified_item, STAC_ITEM_URL
)
from scripts.run_serengeti_regional_ndvi_mirror_2010_2013_v0 import (
    fetch_all_stac_terra_scenes, apply_frozen_522_mirror_pairs, 
    MAX_TERRA_SCENES, COLLECTION, ENDPOINT, DATE_QUERY_START, DATE_QUERY_END,
    PUBLIC_BBOX, STAC_LIMIT
)
from urllib.parse import urlencode

PUBLIC_TOKEN_ENDPOINT=(
    "https://planetarycomputer.microsoft.com/api/sas/v1/token/"
    "modiseuwest/modis-061-cogs"
)
PREVIOUS_PROBE_GOOD_NDVI=.5484
PREVIOUS_PROBE_QUALITY_PIXELS=9
PREVIOUS_SOURCE_TERRA_SCENES=83

def official_anonymous_container_token():
    data=api_json(PUBLIC_TOKEN_ENDPOINT)
    token=data.get("token","").lstrip("?")
    if not all(k+"=" in token for k in ("sig","se","sp","sv")):
        raise ValueError("HOLD_PUBLIC_CONTAINER_SAS_TOKEN_FORMAT")
    # Return ephemeral credential ONLY IN PROCESS; never log/serialize.
    return token

def signed_public_asset(href:str, token:str)->str:
    if not href.startswith("https://modiseuwest.blob.core.windows.net/modis-061-cogs/MOD13Q1/"):
        raise ValueError("HOLD_ASSET_OUTSIDE_PUBLIC_NASA_TERRA_CONTAINER")
    return href+"?"+token

def known_item_required(token:str)->dict:
    raw=api_json(STAC_ITEM_URL)
    ndvi,qa=verified_item(raw)
    img=raster3x3(signed_public_asset(ndvi,token),
                  signed_public_asset(qa,token))
    x=img.get("primary_good_only_median_NDVI")
    if (x is None or abs(x-PREVIOUS_PROBE_GOOD_NDVI)>1e-7 or
        img["qa_good_reliability0_raw_valid_pixels"]!=PREVIOUS_PROBE_QUALITY_PIXELS):
        raise ValueError("HOLD_ORIGINAL_PROBE_RESULT_CANNOT_BE_REPLAYED_USING_CONTAINER_TOKEN")
    return {"item":raw["id"],"ndvi":x,"qa_good":9,"original_first_probe_replayed":True}

def scene_with_public_container_token(source_scene:dict,token:str)->dict:
    scene=source_scene
    try:
        ndvi=signed_public_asset(scene["ndvi_asset"],token)
        qa=signed_public_asset(scene["qa_asset"],token)
        image=raster3x3(ndvi,qa)
        return {
            "source_item":scene["source_item"],
            "start_date":scene["start_date"],
            "end_date":scene["end_date"],
            "status":image["status"],
            "good_pixels":image["qa_good_reliability0_raw_valid_pixels"],
            "marginal_pixels_not_used":image["qa_marginal_reliability1_pixel_count"],
            "cloud_pixels":image["qa_cloudy3_pixel_count"],
            "good_only_NDVI":image["primary_good_only_median_NDVI"],
        }
    except (OSError,ValueError,KeyError,TypeError,IndexError,urllib.error.URLError) as exc:
        return {
            "source_item":scene["source_item"],
            "start_date":scene["start_date"],
            "end_date":scene["end_date"],
            "status":"HOLD_PUBLIC_SOURCE_SCENE_READ_OR_QA_ERROR",
            "exception_type":type(exc).__name__,
            "http_status_if_reported":getattr(exc,"code",None),
            "good_only_NDVI":None,
        }

def run():
    token=official_anonymous_container_token()
    known=known_item_required(token)
    scenes,pages=fetch_all_stac_terra_scenes()
    if len(scenes)!=PREVIOUS_SOURCE_TERRA_SCENES:
        raise ValueError("HOLD_PREVIOUS_TERRA_STAC_SOURCE_COUNT_83_NOT_REPLAYED")
    data=[scene_with_public_container_token(s,token) for s in scenes]
    obs=sorted(data,key=lambda r:r["end_date"])
    exact_2012=[x for x in obs if x["source_item"]==known["item"]]
    if not exact_2012 or abs(exact_2012[0]["good_only_NDVI"]-.5484)>1e-7:
        raise ValueError("HOLD_SOURCE_2012_REPEATED_FIRST_ITEM_DRIFT")
    environment=apply_frozen_522_mirror_pairs(obs)
    qa_scene_count=sum(x["good_only_NDVI"] is not None for x in obs)
    ready=environment["three_years_coverage_qualified"]
    return {
        "status":("REGIONAL_TERRA_MOD13_2010_2013_NDVI_QUALITY_SUPPORTED"
                  if ready else
                  "REGIONAL_SOURCE_RETRIEVED_BUT_ANNUAL_QA_COVERAGE_HOLD"),
        "schema":"serengeti_public_modis_terra_token_source_v1",
        "source_endpoint":"https://planetarycomputer.microsoft.com/api/stac/v1",
        "source_collection":COLLECTION,
        "source_product_DOI":"10.5067/MODIS/MOD13Q1.061",
        "source_access":"one official anonymous public container SAS token, token neither serialized nor logged",
        "source_STAC_pages":pages,
        "terra_scene_count":len(obs),
        "qualified_qa_good_scene_count":qa_scene_count,
        "unqualified_or_failed_scene_count":len(obs)-qa_scene_count,
        "known_original_2012_item_replayed":known,
        "all_83_source_scenes_observations":obs,
        "unchanged_522_pair_climate_NDVI_result":environment,
        "pre_v1_first_source_outcome_frozen":True,
        "no_camera_GPS_or_wildlife_source_data_read":True,
        "NDVI_not_genuine_forage_biomass":True,
        "no_species_correlation_or_causation_estimated":True,
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--output",required=True,type=Path)
    args=a.parse_args()
    try:
        out=run()
    except (OSError,ValueError,KeyError,TypeError,IndexError,urllib.error.URLError) as exc:
        out={
            "status":"HOLD_PUBLIC_MODIS_CONTAINER_TOKEN_OR_SOURCE_NOT_VALID",
            "error_type":type(exc).__name__,
            "http_status_if_available":getattr(exc,"code",None),
            "no_NDVI_or_animal_biological_result_fabricated":True
        }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "source_scenes":out.get("terra_scene_count"),
        "good_source_scenes":out.get("qualified_qa_good_scene_count"),
        "known_2012_probe_replayed":out.get("known_original_2012_item_replayed"),
        "yearwise":out.get("unchanged_522_pair_climate_NDVI_result",{}).get("yearwise"),
        "no_animal_causation":True
    },sort_keys=True))

if __name__=="__main__": main()
