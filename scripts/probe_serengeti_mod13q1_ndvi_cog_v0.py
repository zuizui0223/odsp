#!/usr/bin/env python3
"""Real NASA MOD13Q1 Terra NDVI COG access and quality-pixel audit.

Fetch via openly searchable Planetary Computer STAC + anonymous public SAS sign.
Only one previously fixed public coarse regional point and one predeclared
2012 scene; do NOT read source camera GPS or any animal event. No interpolation.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import statistics
import urllib.parse
import urllib.request

import numpy as np

STAC_COLLECTION = "modis-13Q1-061"
ITEM_ID = "MOD13Q1.A2012017.h21v09.061.2021203222829"
STAC_ITEM_URL = (
    "https://planetarycomputer.microsoft.com/api/stac/v1/collections/"
    + STAC_COLLECTION + "/items/" + ITEM_ID
)
SIGN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
LAT, LON = -2.5, 34.75
NDVI_ASSET = "250m_16_days_NDVI"
QA_ASSET = "250m_16_days_pixel_reliability"
NDVI_SCALE = .0001
NDVI_RAW_BOUNDS = (-2000, 10000)
VALID_QA = 0
REQUIRED_GOOD_PIXELS = 6

def api_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": "ODSP-Public-NDVI-QA-science/0.1",
                      "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("HOLD_API_RESPONSE_TOO_LARGE")
    return json.loads(raw)

def verified_item(source: dict) -> tuple[str, str]:
    if source.get("id") != ITEM_ID or source.get("collection") != STAC_COLLECTION:
        raise ValueError("HOLD_WRONG_MOD13Q1_TERRA_ITEM")
    if source.get("properties", {}).get("platform") != "terra":
        raise ValueError("HOLD_NOT_TERRA_COMPOSITE")
    p = source["properties"]
    if (p.get("start_datetime") != "2012-01-17T00:00:00Z"
        or p.get("end_datetime") != "2012-02-01T23:59:59Z"):
        raise ValueError("HOLD_MODIS_COMPOSITE_DATE_CHANGED")
    assets = source["assets"]
    if NDVI_ASSET not in assets or QA_ASSET not in assets:
        raise ValueError("HOLD_REQUIRED_NDVI_AND_PIXEL_RELIABILITY_MISSING")
    b = assets[NDVI_ASSET].get("raster:bands", [{}])[0]
    if float(b.get("scale", -1)) != NDVI_SCALE:
        raise ValueError("HOLD_STAC_NDVI_RASTER_SCALE_CHANGED")
    hrefs = []
    for name in (NDVI_ASSET, QA_ASSET):
        href = assets[name]["href"]
        if not href.startswith("https://modiseuwest.blob.core.windows.net/modis-061-cogs/MOD13Q1/"):
            raise ValueError("HOLD_UNRECOGNIZED_NASA_MOD13_TERRA_ASSET")
        hrefs.append(href)
    return tuple(hrefs)

def sign_public_blob(url: str) -> str:
    payload = api_json(SIGN_URL + "?" + urllib.parse.urlencode({"href": url}))
    signed = payload.get("href", "")
    if not signed.startswith(url+"?"):
        raise ValueError("HOLD_UNEXPECTED_PUBLIC_SAS_SIGNER")
    # Never log the short-lived SAS credential in source receipts.
    return signed

def good_ndvi_window(raw_ndvi, raw_qa) -> dict:
    ndvi=np.asarray(raw_ndvi)
    qa=np.asarray(raw_qa)
    if ndvi.shape != (3,3) or qa.shape != (3,3):
        raise ValueError("HOLD_SATELLITE_WINDOW_NOT_THREE_BY_THREE")
    mask = ((qa == VALID_QA) &
            (ndvi >= NDVI_RAW_BOUNDS[0]) &
            (ndvi <= NDVI_RAW_BOUNDS[1]))
    values = ndvi[mask].astype(float) * NDVI_SCALE
    n = int(values.size)
    median = float(np.median(values)) if n >= REQUIRED_GOOD_PIXELS else None
    return {
        "pixel_count_3x3":9,
        "qa_good_reliability0_raw_valid_pixels":n,
        "qa_marginal_reliability1_pixel_count":int((qa == 1).sum()),
        "qa_snow2_pixel_count":int((qa == 2).sum()),
        "qa_cloudy3_pixel_count":int((qa == 3).sum()),
        "primary_good_only_median_NDVI":median,
        "status":("QUALIFIED_FIRST_REAL_MOD13Q1_QA_GOOD_MEDIAN"
                  if median is not None else
                  "QA_HOLD_NEED_AT_LEAST_6_GOOD_PIXELS"),
        "ndvi_scale_verified":NDVI_SCALE,
        "interpolation_or_marginal_qa_used":False,
    }

def raster3x3(signed_ndvi: str, signed_qa: str) -> dict:
    import rasterio
    from rasterio.windows import Window
    from rasterio.warp import transform as transform_coords
    options={
        "GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS":".tif",
        "GDAL_HTTP_MAX_RETRY":"2",
        "GDAL_HTTP_RETRY_DELAY":"1",
    }
    with rasterio.Env(**options):
        with rasterio.open(signed_ndvi) as ndvi_ds:
            x,y=transform_coords("EPSG:4326",ndvi_ds.crs,[LON],[LAT])
            row,col = ndvi_ds.index(x[0],y[0])
            if not (1 <= row < ndvi_ds.height-1 and
                    1 <= col < ndvi_ds.width-1):
                raise ValueError("HOLD_PUBLIC_COARSE_POINT_OUTSIDE_MODIS_TILE")
            win=Window(col-1,row-1,3,3)
            ndvi = ndvi_ds.read(1,window=win)
            raster_meta={
                "shape":list(ndvi_ds.shape),
                "raw_data_type":str(ndvi_ds.dtypes[0]),
                "crs_kind":"MODIS sinusoidal",
                "scale":NDVI_SCALE,
            }
        with rasterio.open(signed_qa) as qa_ds:
            if qa_ds.crs != ndvi_ds.crs or qa_ds.transform != ndvi_ds.transform or qa_ds.shape != ndvi_ds.shape:
                raise ValueError("HOLD_QA_RASTER_GRID_MISMATCH")
            qa=qa_ds.read(1,window=win)
    return {"raster":raster_meta, **good_ndvi_window(ndvi,qa)}

def run():
    item=api_json(STAC_ITEM_URL)
    ndvi,qa=verified_item(item)
    signed_ndvi=sign_public_blob(ndvi)
    signed_qa=sign_public_blob(qa)
    raster=raster3x3(signed_ndvi,signed_qa)
    return {
        "study":"MOD13Q1_061_2012017_QUALITY_SOURCE_PROBE_V0",
        "status":raster["status"],
        "product":"MOD13Q1 V061 Terra",
        "source_DOI":"10.5067/MODIS/MOD13Q1.061",
        "original_STAC_item_id":ITEM_ID,
        "source_STAC_item_url":STAC_ITEM_URL,
        "source_composite_start":"2012-01-17",
        "source_composite_end":"2012-02-01",
        "public_regional_probe_lat_lon":[LAT,LON],
        "source_camera_locations_read":False,
        "animal_event_data_read":False,
        "raster_quality_receipt":raster,
        "source_site_ndvi_or_animal_behavior_identified":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    try:
        out=run()
    except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        out={
            "study":"MOD13Q1_061_2012017_QUALITY_SOURCE_PROBE_V0",
            "status":"HOLD_OPEN_ASSET_DOWNLOAD_OR_QA_NOT_VERIFIED",
            "error_type":type(exc).__name__,
            "animal_or_ndvi_source_value_fabricated":False,
        }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "item":out.get("original_STAC_item_id"),
        "good_pixels":out.get("raster_quality_receipt",{}).get("qa_good_reliability0_raw_valid_pixels"),
        "ndvi":out.get("raster_quality_receipt",{}).get("primary_good_only_median_NDVI"),
        "error_type":out.get("error_type"),
        "animal_inference":False,
    },sort_keys=True))

if __name__=="__main__":main()
