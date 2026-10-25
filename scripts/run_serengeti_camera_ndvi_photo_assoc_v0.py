#!/usr/bin/env python3
"""Exploratory local MODIS greenness vs same-camera photo reweighting.

One Serengeti ecology region only. QUALIFIED good NDVI satellite 16-day
source and MD5-pinned original photo data, both unmodified original first
receipts replayed. No exact source location, site ID, or photo timestamp in
outputs. NDVI does NOT measure forage or prove genuine animal movement.
"""
from __future__ import annotations
import argparse
from bisect import bisect_right
from collections import Counter,defaultdict
from datetime import date,timedelta
import hashlib
import json
import math
from pathlib import Path
import statistics

from scripts.probe_serengeti_mod13q1_ndvi_cog_v0 import good_ndvi_window
from scripts.run_serengeti_regional_modis_container_token_v1 import (
    official_anonymous_container_token,signed_public_asset
)
from scripts.run_serengeti_regional_ndvi_mirror_2010_2013_v0 import (
    fetch_all_stac_terra_scenes
)
from scripts.run_serengeti_source_recorded_solar_season_v0 import (
    load_effort,INDEPENDENCE_MINUTES,zone
)
from scripts.run_serengeti_photo_weather_cycle_alignment_v0 import (
    original_first_receipt_verified,raw_source_data
)
from scripts.run_serengeti_same_station_trophic_photo_time_v0 import (
    derive_calendar_eligibility
)

FIRST_SATELLITE_SHA="e0e3c57de8d6a3ab9996412886e9733ea572cf9989f88a68b5c3ac5fb5557f11"
FIRST_PHOTO_SHA="0b70f7425d8ade2489a989bebc7b22fda997d82b2190e5e7d3c5d6f83ee71ef3"
FOCAL=("zebra","wildebeest","buffalo","gazelleThomsons","hyenaSpotted")
YEARS=(2010,2011,2012)
COARSE_LAT,COARSE_LON=-2.5,34.75
REQUIRED_SATELLITES=83
REQUIRED_ORIGINAL_SITES=186
REQUIRED_ORIGINAL_DATE_PAIRS=24290
REQUIRED_ORIGINAL_PHOTOS=38792
MAX_SITE_PIXEL_WINDOW=2_000_000
MIN_GOOD_PIXELS=6
MIN_YEAR_VALID_NDVI_PAIR_DATES=10
MIN_YEAR_VALID_NDVI_PAIR_FRACTION=.60
MIN_PHOTO_EVENTS_PER_BRANCH_PER_SITE=5
MIN_SITES_PER_SPECIES_YEAR_FOR_CORRELATION=15
MIN_YEAR_PHOTO_COVERAGE=.50

def pinned_original_scene_receipt(path:Path)->dict:
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIRST_SATELLITE_SHA:
        raise ValueError("HOLD_83_SCENE_FROZEN_SOURCE_RECEIPT_SHA256_DRIFT")
    o=json.loads(raw)
    if o["terra_scene_count"]!=REQUIRED_SATELLITES or o["qualified_qa_good_scene_count"]!=75:
        raise ValueError("HOLD_FIRST_MODIS_SCIENCE_SOURCE_STATUS_DRIFT")
    return o

def source_scene_roster(pinned:dict):
    scenes,pages=fetch_all_stac_terra_scenes()
    old=pinned["all_83_source_scenes_observations"]
    if len(scenes)!=len(old):
        raise ValueError("HOLD_ORIGINAL_SATELLITE_SCENE_COUNT_CHANGED")
    for a,b in zip(scenes,old):
        if ((a["source_item"],a["start_date"],a["end_date"]) !=
            (b["source_item"],b["start_date"],b["end_date"])):
            raise ValueError("HOLD_ORIGINAL_MODIS_STAC_SCENE_IDENTITIES_CHANGED")
    return scenes,old

def _coord_pixel_windows(ds,geos):
    from rasterio.warp import transform
    sites=sorted(geos)
    lon=[geos[s][1] for s in sites]+[COARSE_LON]
    lat=[geos[s][0] for s in sites]+[COARSE_LAT]
    xs,ys=transform("EPSG:4326",ds.crs,lon,lat)
    pos={}
    for s,x,y in zip(sites+["__PUBLIC_REGION_PROBE__"],xs,ys):
        row,col=ds.index(x,y)
        if 1<=row<ds.height-2 and 1<=col<ds.width-2:
            pos[s]=(row,col)
    if len(pos)<.80*(len(geos)+1):
        raise ValueError("HOLD_ORIGINAL_SITES_NOT_IN_ONE_STAC_MODIS_TILE")
    if "__PUBLIC_REGION_PROBE__" not in pos:
        raise ValueError("HOLD_ORIGINAL_PUBLIC_PROBE_OUTSIDE_TILE")
    rowmin=min(r for r,c in pos.values())
    rowmax=max(r for r,c in pos.values())
    colmin=min(c for r,c in pos.values())
    colmax=max(c for r,c in pos.values())
    height=rowmax-rowmin+3;width=colmax-colmin+3
    if height*width>MAX_SITE_PIXEL_WINDOW:
        raise ValueError("HOLD_SITE_ROI_WINDOW_BOUNDS_TOO_LARGE")
    return pos,(rowmin,colmin,height,width)

def scene_pixels(s,token,geos,original_region_scene):
    import rasterio
    from rasterio.windows import Window
    option={
        "GDAL_DISABLE_READDIR_ON_OPEN":"EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS":".tif",
        "GDAL_HTTP_MAX_RETRY":"2",
        "GDAL_HTTP_RETRY_DELAY":"1"
    }
    ndvi_url=signed_public_asset(s["ndvi_asset"],token)
    qa_url=signed_public_asset(s["qa_asset"],token)
    with rasterio.Env(**option):
        with rasterio.open(ndvi_url) as nd:
            pos,(r0,c0,h,w)=_coord_pixel_windows(nd,geos)
            win=Window(c0-1,r0-1,w,h)
            raw_ndvi=nd.read(1,window=win)
            expected_shape=nd.shape
            expected_crs=nd.crs
            expected_transform=nd.transform
        with rasterio.open(qa_url) as q:
            if (q.shape!=expected_shape or q.crs!=expected_crs
                or q.transform!=expected_transform):
                raise ValueError("HOLD_NDVI_AND_QA_SOURCE_GRID_DIFFERENT")
            raw_qa=q.read(1,window=win)
    values={}
    for site,(row,col) in pos.items():
        # Full COG ROI origin is pixel colmin-1,rowmin-1.
        u=row-r0
        v=col-c0
        sub_ndvi=raw_ndvi[u:u+3,v:v+3]
        sub_qa=raw_qa[u:u+3,v:v+3]
        check=good_ndvi_window(sub_ndvi,sub_qa)
        values[site]=check["primary_good_only_median_NDVI"]
    source_pinned=original_region_scene["good_only_NDVI"]
    probe=values.pop("__PUBLIC_REGION_PROBE__")
    if ((source_pinned is None) != (probe is None)
         or source_pinned is not None and abs(probe-source_pinned)>1e-7):
        raise ValueError("HOLD_ORIGINAL_PUBLIC_MODIS_83_SCENE_QUALITY_DRIFT")
    return values,len(pos)-1

def last_completed_site_NDVI(ends,site_series,site:str,when:date):
    i=bisect_right(ends,when)-1
    if i<0 or (when-ends[i]).days>20:return None
    return site_series[i].get(site)

def mean(x):
    return statistics.mean(x) if x else None

def _rank(values):
    rows=sorted(enumerate(values),key=lambda pair:pair[1])
    rank=[0.0]*len(values)
    i=0
    while i<len(rows):
        j=i+1
        while j<len(rows) and rows[j][1]==rows[i][1]:
            j+=1
        center=(i+1+j)*.5
        for k in range(i,j):rank[rows[k][0]]=center
        i=j
    return rank

def spearman(x,y):
    n=len(x)
    if n<MIN_SITES_PER_SPECIES_YEAR_FOR_CORRELATION:return None
    u=_rank(x);v=_rank(y)
    au=mean(u);av=mean(v)
    xu=[a-au for a in u]; yv=[b-av for b in v]
    denom=(sum(a*a for a in xu)*sum(b*b for b in yv))**.5
    return sum(a*b for a,b in zip(xu,yv))/denom if denom>0 else None

def correlations_by_taxon_year(cells,ndvi_siteyear,photo_source_totals):
    results=[]
    for year in YEARS:
        for tax in FOCAL:
            rows=[]
            nup=nfall=0
            for (site,cy),delta in ndvi_siteyear.items():
                if cy!=year:continue
                b=cells.get((site,year,tax,"falling"),Counter())
                a=cells.get((site,year,tax,"rising"),Counter())
                nf=sum(b.values());nr=sum(a.values())
                nup+=nr;nfall+=nf
                if min(nf,nr)<MIN_PHOTO_EVENTS_PER_BRANCH_PER_SITE:continue
                frac=lambda z:z["night"]/sum(z.values())
                rows.append((site,delta,math.log(nf/nr),frac(b)-frac(a)))
            prev_up=photo_source_totals.get((tax,year,"rising"),0)
            prev_f=photo_source_totals.get((tax,year,"falling"),0)
            coverage=(min(nup/prev_up,nfall/prev_f) if min(prev_up,prev_f)>0 else None)
            n=len(rows)
            enough=(n>=MIN_SITES_PER_SPECIES_YEAR_FOR_CORRELATION
                    and coverage is not None and coverage>=MIN_YEAR_PHOTO_COVERAGE)
            def summary(i):
                if not enough:return {"spearman":None,"leave_one_site_min_max":None}
                vals=[z[1] for z in rows]; outcomes=[z[i] for z in rows]
                r=spearman(vals,outcomes)
                loos=[spearman(vals[:k]+vals[k+1:],outcomes[:k]+outcomes[k+1:])
                      for k in range(n)]
                loos=[a for a in loos if a is not None]
                return {
                    "spearman":r,
                    "leave_one_site_min_max":[min(loos),max(loos)] if loos else None
                }
            results.append({
                "source_taxon":tax,"solstice_cycle_year":year,
                "focal_photo_sites_both_branches_with_at_least_5_events":n,
                "original_photo_count_coverage_min_branch":coverage,
                "ndvi_siteyears_available":sum(y==year for (s,y) in ndvi_siteyear),
                "mean_site_NDVI_delta_among_photo_supported":
                    mean([v[1] for v in rows]),
                "supported_descriptive_association":enough,
                "ndvi_vs_camera_photo_count_log_falling_rising":summary(2),
                "ndvi_vs_night_photo_fraction_difference":summary(3),
            })
    return results

def run(consensus:Path,effort:Path,original_satellite:Path):
    frozen_photo=original_first_receipt_verified(consensus,effort)
    frozen_sat=pinned_original_scene_receipt(original_satellite)
    cycles,_=load_effort(effort)
    geos,events=raw_source_data(consensus,set(cycles))
    if len(geos)!=REQUIRED_ORIGINAL_SITES:
        raise ValueError("HOLD_ORIGINAL_PHYSICAL_CAMERA_SITES_NOT_REPLAYED")
    original_date_map,structural_sitecycles=derive_calendar_eligibility(cycles,geos)
    scenes,pinned_scenes=source_scene_roster(frozen_sat)
    token=official_anonymous_container_token()
    scene_value_maps=[]
    for scene,pinned in zip(scenes,pinned_scenes):
        # Network errors never imputed; if any source COG missing fail source lane,
        # preserve earlier regional QA result unchanged.
        values,nsites=scene_pixels(scene,token,geos,pinned)
        scene_value_maps.append(values)
    ends=[date.fromisoformat(s["end_date"]) for s in scenes]
    if ends!=sorted(ends):
        raise ValueError("HOLD_MODIS_SOURCE_END_DATE_UNSORTED")
    valid_ndvi_by_site={}
    original_eligible_pairs=0
    total_qa_matched_pairs=0
    admitted_photo_dates={}
    percycle=defaultdict(lambda:{"structural_pairs":0,"qa_pairs":0,"sitecycles":0,"supported_sitecycles":0,"deltas":[]})
    for site,yearpairs in cycles.items():
        if site not in geos:continue
        for year,pairs in yearpairs.items():
            good=[]
            denom=0
            for rising,falling in pairs:
                if (original_date_map.get((site,rising))!=(year,"rising")
                    or original_date_map.get((site,falling))!=(year,"falling")):
                    continue
                denom+=1
                first=last_completed_site_NDVI(ends,scene_value_maps,site,rising)
                second=last_completed_site_NDVI(ends,scene_value_maps,site,falling)
                if first is not None and second is not None:
                    good.append((rising,falling,second-first))
            original_eligible_pairs+=denom
            if year not in YEARS or denom<=0:continue
            percycle[year]["structural_pairs"]+=denom
            percycle[year]["qa_pairs"]+=len(good)
            percycle[year]["sitecycles"]+=1
            total_qa_matched_pairs+=len(good)
            qualifies=(len(good)>=MIN_YEAR_VALID_NDVI_PAIR_DATES
                       and len(good)/denom>=MIN_YEAR_VALID_NDVI_PAIR_FRACTION)
            if qualifies:
                percycle[year]["supported_sitecycles"]+=1
                avg=mean([x[2] for x in good])
                valid_ndvi_by_site[(site,year)]=avg
                percycle[year]["deltas"].append(avg)
                for rising,falling,_ in good:
                    admitted_photo_dates[(site,rising)]=(year,"rising")
                    admitted_photo_dates[(site,falling)]=(year,"falling")

    if original_eligible_pairs!=REQUIRED_ORIGINAL_DATE_PAIRS:
        raise ValueError("HOLD_MODIS_AND_ANIMAL_ORIGINAL_DATE_PAIR_JOIN_DRIFT")
    dedup_prev={}
    all_first_matched_photos=0
    source_totals=Counter()
    qualified_cells=defaultdict(Counter)
    for site,sp,time in events:
        key0=(site,sp)
        prev=dedup_prev.get(key0)
        if prev and time-prev<timedelta(minutes=INDEPENDENCE_MINUTES):continue
        dedup_prev[key0]=time
        origin=original_date_map.get((site,time.date()))
        if origin is None:continue
        all_first_matched_photos+=1
        year,branch=origin
        if sp in FOCAL:
            source_totals[(sp,year,branch)]+=1
        qualified=admitted_photo_dates.get((site,time.date()))
        if sp not in FOCAL or qualified is None:continue
        qyear,qbranch=qualified
        qualified_cells[(site,qyear,sp,qbranch)][zone(time,*geos[site])]+=1
    if all_first_matched_photos!=REQUIRED_ORIGINAL_PHOTOS:
        raise ValueError("HOLD_ORIGINAL_38792_PHOTO_SOURCE_REPLAY_FAILED")

    correlations=correlations_by_taxon_year(
        qualified_cells,valid_ndvi_by_site,source_totals
    )
    year_summary=[]
    for year in YEARS:
        p=percycle[year]
        year_summary.append({
            "year":year,
            "original_source_pair_dates":p["structural_pairs"],
            "satellite_QA_good_pair_dates":p["qa_pairs"],
            "satellite_QA_good_pair_fraction":(
                p["qa_pairs"]/p["structural_pairs"] if p["structural_pairs"] else None
            ),
            "source_camera_siteyears_with_datepairs":p["sitecycles"],
            "NDVI_qualified_source_camera_siteyears":p["supported_sitecycles"],
            "mean_local_site_NDVI_falling_minus_rising":mean(p["deltas"]),
            "site_NDVI_delta_median":statistics.median(p["deltas"]) if p["deltas"] else None,
            "site_NDVI_delta_positive_fraction":(
                sum(v>0 for v in p["deltas"])/len(p["deltas"])
                if p["deltas"] else None
            ),
        })
    return {
        "status":"EXPLORATORY_OBSERVED_CAMERA_PHOTO_NDVI_PIXEL_ASSOCIATION_ONLY",
        "source_original_photo_first_receipt_sha256":FIRST_PHOTO_SHA,
        "original_regional_NDVI_83_scene_receipt_sha256":FIRST_SATELLITE_SHA,
        "original_43_taxon_photo_source_replayed":True,
        "all_original_match_photo_records":all_first_matched_photos,
        "original_24_290_photoperiod_site_date_pairs":original_eligible_pairs,
        "full_MODIS_Terra_83_item_source_replayed":True,
        "source_site_coordinate_count_not_exported":len(geos),
        "source_NDVI_all_stations_internal_only":True,
        "site_years_environmental_coverage":year_summary,
        "all_five_prelisted_taxa_and_three_years_descriptive_correlations":correlations,
        "strong_ceiling":"PHOTO RECORD correlations only; 250m MODIS vegetation is not forage biomass; original hourly ON hours and q not independently verified; co-photo-selected camera samples and one Serengeti landscape.",
        "causal_NDVI_migration_behavior_or_out_of_region_inference":False,
        "site_ids_coordinates_event_times_ndvi_pixels_exported":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--consensus",required=True,type=Path)
    p.add_argument("--effort",required=True,type=Path)
    p.add_argument("--original-satellite-receipt",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    try:
        o=run(a.consensus,a.effort,a.original_satellite_receipt)
    except (OSError,ValueError,KeyError,TypeError,IndexError) as e:
        o={
            "status":"HOLD_CAMERA_NDVI_SOURCE_OR_REPLAY_NOT_QUALIFIED",
            "error_type":type(e).__name__,
            "no_ecological_association_claimed":True
        }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(o,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "status":o["status"],
        "original_photo_replay":o.get("all_original_match_photo_records"),
        "year_summary":o.get("site_years_environmental_coverage"),
        "taxon_cycles":o.get("all_five_prelisted_taxa_and_three_years_descriptive_correlations"),
        "causal_animal_inference":False
    },sort_keys=True))
    if o["status"].startswith("HOLD"):raise SystemExit(2)

if __name__=="__main__":main()
