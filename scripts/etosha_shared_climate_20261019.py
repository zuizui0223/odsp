"""Post-outcome, source-locked Etosha hydrothermal context on matched solar dates.

Both mammal sources use same time-only 1 fix/UTC hour, southern December
solstice, and 30–120 minute observed GPS step criteria. Publish only
source-level regional climate summaries and years, never GPS coordinates.
"""
import argparse,json
from pathlib import Path
from collections import defaultdict
from statistics import mean
from scripts.movebank_native_ecology_20261019 import HERE,original_files,checksum_and_download
from scripts.movebank_elephant_hourly_20261019 import thinned_loader
from scripts.movebank_southern_solar_mammal_20261019 import southern_solar_cycle,matched_pairs,safe_unzip_data_csv
from scripts.movebank_solar_movement_20261019 import valid_interval
from scripts.movebank_regional_climate_link_20261019 import read_weather,weather_rolling_30

CONTRACT=HERE/"research/ETOSHA_SHARED_CLIMATE_V0_20261019.json"
SOUTH=HERE/"research/MOVEBANK_SOUTHERN_SOLAR_MOVEMENT_V0_20261019.json"

def pairs_from_source(path):
    animals,source_rows,invalid=thinned_loader(path)
    support=defaultdict(lambda:{"day":0,"night":0,"lat_sum":0.0,"n":0})
    for animal,track in animals.items():
        track.sort(key=lambda v:v[0])
        for a,b in zip(track,track[1:]):
            v=valid_interval(a[0],a[1],a[2],b[0],b[1],b[2])
            if v is None:continue
            d,part,speed,h,lat=v
            if lat>=0:continue
            s=support[(animal,d)];s[part]+=1;s["lat_sum"]+=lat;s["n"]+=1
    animals.clear()
    by_year=defaultdict(dict)
    for (animal,d),s in support.items():
        if s["day"]<3 or s["night"]<3:continue
        year,branch=southern_solar_cycle(d)
        if year is None:continue
        by_year[(animal,year)][d]={"branch":branch,"lat":s["lat_sum"]/s["n"],"n_day":s["day"],"n_night":s["night"]}
    out=defaultdict(list);yrs=[]
    for (individual,year),dates in by_year.items():
        if {v["branch"] for v in dates.values()}!={"rising","falling"}:continue
        matched=matched_pairs(dates)
        if len(matched)<10:continue
        out[individual].append(matched);yrs.append(year)
    return out,{"source_rows":source_rows,"invalid_gps_rows":invalid,
        "qualified_individuals":len(out),"qualified_individual_solar_cycles":len(yrs),
        "qualified_solar_years":sorted(set(yrs)),"qualified_matched_date_pairs":sum(len(z) for y in out.values() for z in y),
        "observed_hourly_selection":thinned_loader.counts}

def join_region_climate(roster,weather):
    result=[];missing=complete=0
    for yearly in roster.values():
        yr_means=[]
        for pairs in yearly:
            vals=[]
            for rise,fall in pairs:
                a=weather_rolling_30(weather,rise);b=weather_rolling_30(weather,fall)
                if a is None or b is None:missing+=1;continue
                complete+=1;vals.append((b[0]-a[0],b[1]-a[1]))
            if vals:yr_means.append((mean(v[0] for v in vals),mean(v[1] for v in vals)))
        if yr_means:result.append((mean(v[0] for v in yr_means),mean(v[1] for v in yr_means)))
    if not result:return {"status":"source_weather_hold","complete_weather_pairs":complete,"missing_weather_pairs":missing}
    return {"status":"matched_date_coarse_era5_descriptive",
       "qualified_individuals_with_weather":len(result),"complete_weather_pairs":complete,"missing_weather_pairs":missing,
       "mean_delta_era5_air_temperature_C":mean(x[0] for x in result),
       "mean_delta_precip_minus_ET0_past30days_mm":mean(x[1] for x in result),
       "individual_averages_warmer":sum(x[0]>0 for x in result),
       "individual_averages_cooler":sum(x[0]<0 for x in result),
       "individual_averages_higher_water_proxy":sum(x[1]>0 for x in result),
       "individual_averages_lower_water_proxy":sum(x[1]<0 for x in result),
       "noncausal_warning":"One coarse Etosha grid, shared environment across individuals and possibly distinct sampling years."}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True,type=Path)
    arg=ap.parse_args();arg.out.mkdir(parents=True,exist_ok=True)
    frozen=json.loads(CONTRACT.read_text());assert frozen["version"]=="etosha-shared-solar-calendar-climate-v0"
    src={x["label"]:x for x in json.loads(SOUTH.read_text())["sources"]}
    results=[]
    for label in ("etosha_elephant","etosha_jackal"):
        x=src[label];r={"source":label,"taxon":x["taxon"],"doi":x["doi"],
                        "already_observed_gps_effect":frozen["expected_original_gps_results"][label]}
        native=arg.out/(label+".native");csvpath=arg.out/(label+".csv")
        try:
            matches=[p for p in original_files(x["package_uuid"]) if p["bitstream_uuid"]==x["provider_original_bitstream_uuid"]]
            if len(matches)!=1 or matches[0]["checksum"]["value"].lower()!=x["provider_original_md5"].lower():raise ValueError("Provider ORIGINAL source changed")
            r["original_md5_verified"]=checksum_and_download(matches[0],native)
            if x["provider_filename"].endswith(".zip"):safe_unzip_data_csv(native,csvpath)
            else:native.replace(csvpath)
            pairs,meta=pairs_from_source(csvpath);r.update(meta)
            if not pairs:raise ValueError("No source-supported matched solar years")
            all_dates=[d for years in pairs.values() for dates in years for pair in dates for d in pair]
            weather,receipts=read_weather({"latitude":-19.0,"longitude":16.0},min(all_dates),max(all_dates))
            r["provider_era5_source_receipts"]=receipts
            r.update(join_region_climate(pairs,weather))
        except Exception as ex:
            r.update(status="source_hold",error=f"{type(ex).__name__}: {ex}")
        finally:
            native.unlink(missing_ok=True);csvpath.unlink(missing_ok=True)
        print("ETOSHA_REGIONAL_CLIMATE "+json.dumps(r,sort_keys=True),flush=True)
        results.append(r)
    same=sorted(set(results[0].get("qualified_solar_years",[]))&set(results[1].get("qualified_solar_years",[])))
    report={"site":"Etosha Namibia, single coarse ERA5 grid -19,16","post_outcome_exploratory":True,
             "shared_supported_solar_years":same,"source_groups":results}
    (arg.out/"etosha_shared_era5.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("ETOSHA_SHARED_SOLAR_YEARS "+json.dumps({"years":same,"source_groups":len(results)}),flush=True)
if __name__=="__main__":main()
