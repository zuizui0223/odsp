"""Exploratory ERA5 hydrothermal correlates of co-observed Utah ungulate diel speed.

Reproduce all SIX source-original paired cell/month q contrasts before weather
requests. Never export original animal identifiers, GPS fixes, 1°-cell keys, or
weather query coordinates. This is NOT a causal thermal/water/vegetation test.
"""
import argparse, calendar, hashlib, json, math, random, time
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean,pstdev
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,urlopen

from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_utah_four_taxa_solar_20261019 import (
    extract_time_only_original_source,CONTRACT as UTAH_SOURCE
)
from scripts.movebank_utah_shared_spatial_20261019 import (
    source_cell_month,cluster_interval
)
from scripts.movebank_utah_diel_photoperiod_20261019 import compare_sites

CONTRACT=HERE/"research/MOVEBANK_UTAH_SHARED_CELL_ERA5_V0_20261019.json"
ORIGINAL=HERE/"research/MOVEBANK_UTAH_SHARED_SPATIAL_BLOCK_V0_20261019.json"
API="https://archive-api.open-meteo.com/v1/archive"
FIELDS=("temperature_2m_mean","temperature_2m_max","precipitation_sum","et0_fao_evapotranspiration")

def first_of_month(y,m):
    return date(y,m,1)

def last_of_month(y,m):
    return date(y,m,calendar.monthrange(y,m)[1])

def month_index(date_value):
    return (date_value.year,date_value.month)

def timezone_name(longitude):
    hour=math.floor(longitude/15+.5)
    return "Etc/GMT"+(f"{-hour:+d}" if hour else "")

def get_bytes(url):
    for retry in range(4):
        try:
            with urlopen(Request(url,headers={"User-Agent":"ODSP-source-registered-public-ecology/1.0","Accept":"application/json"}),timeout=110) as f:
                content=f.read(12000000)
            if len(content)>=12000000:raise ValueError("ERA5 source exceeded bounded response limit")
            return content
        except (HTTPError,URLError,TimeoutError) as e:
            if retry==3 or (isinstance(e,HTTPError) and e.code in (400,401,403,404)):
                raise
            time.sleep(2**retry)

def get_monthly_era5(block,months):
    lat,lon=block
    lo=min(months);hi=max(months)
    start=first_of_month(*lo);end=last_of_month(*hi)
    params={"latitude":lat+.5,"longitude":lon+.5,
        "start_date":start.isoformat(),"end_date":end.isoformat(),
        "daily":",".join(FIELDS),"models":"era5",
        "timezone":timezone_name(lon+.5),"elevation":"nan","cell_selection":"nearest"}
    raw=get_bytes(API+"?"+urlencode(params))
    s=json.loads(raw)
    daily=s.get("daily") or {};unit=s.get("daily_units") or {}
    for name,expected in [("temperature_2m_mean","°C"),("temperature_2m_max","°C"),
                          ("precipitation_sum","mm"),("et0_fao_evapotranspiration","mm")]:
        if unit.get(name)!=expected:
            raise ValueError("Unrecognized source ERA5 unit for "+name)
    days=daily.get("time") or []
    if not days or any(len(daily.get(f,[]))!=len(days) for f in FIELDS):
        raise ValueError("Incomplete source daily ERA5 output")
    groups=defaultdict(list)
    for i,d in enumerate(days):
        day=date.fromisoformat(d)
        values=[daily[f][i] for f in FIELDS]
        if any(x is None or not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):
            continue
        tmean,tmax,rain,et0=values
        if rain<0 or et0<0 or tmax<tmean:
            continue
        groups[month_index(day)].append((tmean,tmax,rain,et0))
    output={}
    for y,m in sorted(months):
        entries=groups.get((y,m),[])
        numdays=calendar.monthrange(y,m)[1]
        if len(entries)<15 or len(entries)/numdays<.8:
            continue
        output[(y,m)]={
            "temperature_mean":mean(x[0] for x in entries),
            "temperature_max":mean(x[1] for x in entries),
            "precip_minus_et0":sum(x[2]-x[3] for x in entries),
            "support_days":len(entries)
        }
    receipt={"sha256":hashlib.sha256(raw).hexdigest(),"daily_rows":len(days),
        "requested_months":len(months),"admitted_months":len(output)}
    return output,receipt

def centered_slope(xy,min_span_sd):
    if len(xy)<4:return None
    x=[row[0] for row in xy];y=[row[1] for row in xy]
    if pstdev(x)<min_span_sd:return None
    xb=mean(x);yb=mean(y)
    denominator=sum((z-xb)**2 for z in x)
    if denominator<=1e-12:return None
    return sum((a-xb)*(b-yb) for a,b in xy)/denominator

def paired_environment(speciesa,speciesb,cell_sources,weather):
    both=sorted(set(cell_sources[speciesa])&set(cell_sources[speciesb]))
    support=defaultdict(list);qualified=0;missing=0
    all_values=[]
    for lat,lon,y,m in both:
        climate=weather.get((lat,lon,y,m))
        if climate is None:
            missing+=1;continue
        qdiff=cell_sources[speciesa][(lat,lon,y,m)][0]-cell_sources[speciesb][(lat,lon,y,m)][0]
        qualified+=1
        item=(climate["temperature_mean"],climate["precip_minus_et0"],qdiff,climate["temperature_max"])
        support[(lat,lon)].append(item)
        all_values.append(item)
    temp=[];water=[]
    for cell,rows in support.items():
        sx=centered_slope([(z[0],z[2]) for z in rows],.25)
        sy=centered_slope([(z[1],z[2]) for z in rows],5.)
        if sx is not None:temp.append(sx)
        if sy is not None:water.append(sy*100)
    return {
        "taxa":[speciesa,speciesb],
        "source_original_shared_cell_months":len(both),
        "weather_supported_common_cell_months":qualified,
        "source_months_missing_climate":missing,
        "shared_geographic_blocks_with_weather":len(support),
        "mean_ERA5_daily_temperature_of_supported_months_C":mean(z[0] for z in all_values) if all_values else None,
        "mean_ERA5_daily_maximum_temperature_of_supported_months_C":mean(z[3] for z in all_values) if all_values else None,
        "mean_monthly_precip_minus_reference_ET0_mm":mean(z[1] for z in all_values) if all_values else None,
        "mean_q_difference_on_weather_qualified_source_months":mean(z[2] for z in all_values) if all_values else None,
        "within_geogrid_temp_slope_blocks":len(temp),
        "within_geogrid_mean_slope_q_per_C":mean(temp) if temp else None,
        "within_geogrid_temp_slope_95_block_bootstrap":cluster_interval(temp) if temp else None,
        "within_geogrid_P_minus_ET0_slope_blocks":len(water),
        "within_geogrid_mean_slope_q_per_100mm":mean(water) if water else None,
        "within_geogrid_P_minus_ET0_slope_95_block_bootstrap":cluster_interval(water) if water else None,
        "measurement_limits":"Same coarse ERA5 climatic month for two taxon source observations; location/month/year and taxon recruitment do not establish direct animal microclimate, forage or causality."
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    f=json.loads(CONTRACT.read_text())
    prev=json.loads(ORIGINAL.read_text())
    if f["version"]!="utah-original-source-shared-cellmonth-era5-ecology-v0":
        raise ValueError("Unfrozen temperature/water ecological route")
    if prev["version"]!="utah-shared-gridmonth-spatial-block-ecology-v0":
        raise ValueError("Original accepted source paired taxon result unavailable")
    src=json.loads(UTAH_SOURCE.read_text())["source"]
    path=args.out/"provider_original_utah.zip"
    report={"source":"Original Movebank Utah 4 ungulates, independent ERA5 monthly regional climate",
        "source_doi":src["doi"],"stage":"post-GPS exploratory, not a causal environmental intervention",
        "previous_original_pair_results_reproduced":False,"pairs":[]}
    try:
        entries=[x for x in original_files(src["package_uuid"]) if x["bitstream_uuid"]==src["original_bitstream_uuid"]]
        if len(entries)!=1 or entries[0]["checksum"]["value"].lower()!=src["original_md5"].lower():
            raise ValueError("Provider original Movebank ZIP MD5 changed")
        report["source_original_md5"]=checksum_and_download(entries[0],path)
        animals,counts,other=extract_time_only_original_source(path,src["catalog_taxa"])
        per={}
        for taxon in src["catalog_taxa"]:
            per[taxon]=source_cell_month(animals[taxon])
            animals[taxon].clear()
        previous=compare_sites({k:{key:q[0] for key,q in v.items()} for k,v in per.items()})
        if len(previous)!=6:
            raise ValueError("Previously frozen source had exactly 6 supported species comparisons")
        for r in previous:
            key="|".join(r["taxa"])
            if r["shared_1degree_calendar_month_cells"]!=prev["source_overlap_count_replay"][key]:
                raise ValueError("Previous source location-month support count changed")
            if abs(r["diel_contrast_a_minus_b_on_common_cells"]-prev["source_effect_replay"][key])>1e-11:
                raise ValueError("Previous source location-month effect changed")
        report["previous_original_pair_results_reproduced"]=True
        counts=defaultdict(set)
        for i,a in enumerate(src["catalog_taxa"]):
            for b in src["catalog_taxa"][i+1:]:
                for (lat,lon,y,m) in set(per[a])&set(per[b]):
                    counts[(lat,lon)].add((y,m))
        report["original_geographic_ERA5_grids"]=len(counts)
        env={};receipts=[];error_count=0
        for cell,months in sorted(counts.items()):
            try:
                climates,receipt=get_monthly_era5(cell,months)
                for (y,m),value in climates.items():
                    env[(*cell,y,m)]=value
                receipts.append(receipt)
            except Exception as e:
                error_count+=1
                # Do NOT substitute another grid or modify source sample.
                receipts.append({"status":"source_weather_hold","error_type":type(e).__name__})
        report["era5_original_source_response_receipts"]=receipts
        report["era5_grids_with_weather_source_hold"]=error_count
        for i,a in enumerate(src["catalog_taxa"]):
            for b in src["catalog_taxa"][i+1:]:
                result=paired_environment(a,b,per,env)
                report["pairs"].append(result)
                print("UTAH_SAME_CELL_HYDROTHERMAL_ASSOCIATION "+json.dumps(result,sort_keys=True),flush=True)
        report["status"]="first_source_ERA5_pairs_preserved_exploratory_environment_completed"
    except Exception as e:
        report.update(status="source_hold",error=f"{type(e).__name__}: {e}")
    finally:
        path.unlink(missing_ok=True)
    (args.out/"utah_same_cell_climate_ecology.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("UTAH_ORIGINAL_ERA5_SOURCE_SUMMARY "+json.dumps({
        "status":report["status"],"previous_six_reproduced":report["previous_original_pair_results_reproduced"],
        "source_pairs":len(report["pairs"]),"source_ERA5_grid_count":report.get("original_geographic_ERA5_grids"),
        "weather_hold_grid_count":report.get("era5_grids_with_weather_source_hold")
    },sort_keys=True))
if __name__=="__main__":main()
